from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from fastapi.responses import JSONResponse, Response

from ..config import AppSettings
from ..logging_utils import get_logger, log_with_context
from ..models.analytics import ChatFeedbackPayload, ChatReviewPayload, SheetApprovalPayload
from ..models.handoff import HandoffPayload, HandoffUpdatePayload
from ..models.responses import (
    HandoffUpdateResponse,
    ReviewUpdateResponse,
    SheetTabLinkResponse,
    SyncRunResponse,
    VisitMetricsResponse,
)
from .chat_analytics_helper_service import ChatAnalyticsHelperService
from .security_service import SecurityService

logger = get_logger(__name__)


def _legacy():
    from ... import main as legacy_main

    return legacy_main


class AnalyticsService:
    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or AppSettings()
        self.security_service = SecurityService(self.settings)
        self.helper_service = ChatAnalyticsHelperService(self.settings)

    def get_visit_count(self) -> VisitMetricsResponse:
        legacy_main = _legacy()
        page_views_total = legacy_main._get_total_visit_count()
        unique_visitors_total = legacy_main._get_unique_visitor_count()
        return VisitMetricsResponse(
            count=page_views_total,
            page_views_total=page_views_total,
            unique_visitors_total=unique_visitors_total,
        )

    def register_visit(self, visitor_id: str) -> JSONResponse | VisitMetricsResponse:
        legacy_main = _legacy()
        try:
            metrics = legacy_main._register_site_visit(visitor_id)
        except Exception:
            return JSONResponse(status_code=500, content={"error": "visit counter unavailable"})

        return VisitMetricsResponse(
            count=metrics["page_views_total"],
            page_views_total=metrics["page_views_total"],
            unique_visitors_total=metrics["unique_visitors_total"],
        )

    def get_chat_overview(
        self,
        *,
        days: int,
        fetch_limit: int,
        recent_limit: int,
        intent_name: str,
        source: str,
        query_text: str,
        owner_name: str,
        review_status: str,
    ) -> JSONResponse | dict[str, Any]:
        legacy_main = _legacy()
        try:
            return self.helper_service.build_chat_overview(
                days=days,
                fetch_limit=fetch_limit,
                recent_limit=recent_limit,
                intent_name=intent_name,
                source=source,
                query_text=query_text,
                owner_name=owner_name,
                review_status=review_status,
            )
        except Exception as exc:
            self.security_service.log_server_error("chat_overview", exc)
            try:
                return legacy_main._build_chat_overview(
                    days=days,
                    fetch_limit=fetch_limit,
                    recent_limit=recent_limit,
                    intent_name=intent_name,
                    source=source,
                    query_text=query_text,
                    owner_name=owner_name,
                    review_status=review_status,
                )
            except Exception as fallback_exc:
                self.security_service.log_server_error("chat_overview_fallback", fallback_exc)
                return self.security_service.safe_error_response("chat analytics unavailable")

    def export_chat_logs(
        self,
        *,
        days: int,
        fetch_limit: int,
        intent_name: str,
        source: str,
        query_text: str,
        owner_name: str,
        review_status: str,
    ) -> JSONResponse | Response:
        legacy_main = _legacy()
        try:
            rows = self.helper_service.build_export_rows(
                days=days,
                fetch_limit=fetch_limit,
                intent_name=intent_name,
                source=source,
                query_text=query_text,
                owner_name=owner_name,
                review_status=review_status,
            )
        except Exception as exc:
            self.security_service.log_server_error("chat_export", exc)
            try:
                rows = legacy_main._fetch_chat_logs(
                    days=days,
                    limit=fetch_limit,
                    intent_name=intent_name,
                    source=source,
                    query_text=query_text,
                )
                safe_owner_name = " ".join(owner_name.strip().split())[:120]
                safe_review_status = " ".join(review_status.strip().split())[:40]
                review_status_map = legacy_main._fetch_review_statuses(
                    [int(row.get("id")) for row in rows if isinstance(row.get("id"), int)]
                )
                for row in rows:
                    row_id = row.get("id")
                    review_info = review_status_map.get(row_id if isinstance(row_id, int) else -1, {})
                    row["owner_name"] = (review_info.get("owner_name") or "").strip()
                    row["review_status"] = (review_info.get("status") or "open").strip() or "open"
                if safe_owner_name:
                    rows = [row for row in rows if (row.get("owner_name") or "").strip() == safe_owner_name]
                if safe_review_status:
                    rows = [
                        row
                        for row in rows
                        if ((row.get("review_status") or "open").strip() or "open") == safe_review_status
                    ]
            except Exception as fallback_exc:
                self.security_service.log_server_error("chat_export_fallback", fallback_exc)
                return self.security_service.safe_error_response("chat export unavailable")

        tsv_lines = [
            "\t".join(
                [
                    "created_at",
                    "session_id",
                    "intent_name",
                    "intent_lane",
                    "preferred_answer_intent",
                    "source",
                    "job_number",
                    "review_status",
                    "owner_name",
                    "user_message",
                    "bot_reply",
                ]
            )
        ]

        def escape_tsv(value: Any) -> str:
            text = str(value or "")
            text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").replace("\t", " ")
            return text

        for row in rows:
            tsv_lines.append(
                "\t".join(
                    [
                        escape_tsv(row.get("created_at")),
                        escape_tsv(row.get("session_id")),
                        escape_tsv(row.get("intent_name")),
                        escape_tsv(row.get("intent_lane")),
                        escape_tsv(row.get("preferred_answer_intent")),
                        escape_tsv(row.get("source")),
                        escape_tsv(row.get("job_number")),
                        escape_tsv(row.get("review_status")),
                        escape_tsv(row.get("owner_name")),
                        escape_tsv(row.get("user_message")),
                        escape_tsv(row.get("bot_reply")),
                    ]
                )
            )

        filename_bits = ["chat-logs", f"{max(1, min(days, 90))}d"]
        if (intent_name or "").strip():
            filename_bits.append((intent_name or "").strip())
        if (source or "").strip():
            filename_bits.append((source or "").strip())
        if (query_text or "").strip():
            filename_bits.append("search")
        if (owner_name or "").strip():
            filename_bits.append("owner")
        if (review_status or "").strip():
            filename_bits.append("status")
        filename = "-".join(filename_bits) + ".tsv"
        tsv_content = "\ufeff" + "\r\n".join(tsv_lines)

        return Response(
            content=tsv_content.encode("utf-16le"),
            media_type="text/tab-separated-values; charset=utf-16le",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    def update_chat_review(self, body: ChatReviewPayload) -> JSONResponse | ReviewUpdateResponse:
        legacy_main = _legacy()
        supabase = legacy_main.get_supabase_client()
        if not supabase:
            return self.security_service.safe_error_response("admin storage unavailable")

        note = legacy_main._sanitize_log_text(body.note, 500)
        owner_name = legacy_main._sanitize_log_text(body.owner_name, 120)

        try:
            supabase.table("chat_log_reviews").upsert(
                {
                    "chat_log_id": body.chat_log_id,
                    "status": body.status,
                    "note": note or None,
                    "owner_name": owner_name or None,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()
        except Exception as exc:
            self.security_service.log_server_error("update_chat_review", exc)
            return self.security_service.safe_error_response("review update failed")

        return ReviewUpdateResponse(
            ok=True,
            chat_log_id=body.chat_log_id,
            status=body.status,
            owner_name=owner_name,
        )

    def create_handoff_request(self, body: HandoffPayload) -> JSONResponse | dict[str, Any]:
        legacy_main = _legacy()
        supabase = legacy_main.get_supabase_client()
        if not supabase:
            return JSONResponse(status_code=500, content={"error": "Supabase not configured"})

        safe_session_id = legacy_main._sanitize_visitor_id(body.session_id) or "anonymous"
        safe_name = legacy_main._sanitize_log_text(body.customer_name, 120)
        safe_contact = legacy_main._sanitize_log_text(body.contact_value, 160)
        safe_channel = (body.preferred_channel or "phone").strip() or "phone"
        safe_note = legacy_main._sanitize_log_text(body.request_note, 800)
        safe_user_message = legacy_main._sanitize_log_text(body.user_message, 2000)
        safe_bot_reply = legacy_main._sanitize_log_text(body.bot_reply, 4000)
        safe_intent = legacy_main._sanitize_log_text(body.intent_name, 80)
        safe_source = legacy_main._sanitize_log_text(body.source, 80) or "chat_widget"
        safe_job_number = legacy_main._sanitize_log_text(body.job_number, 40)

        if not safe_contact and not safe_note:
            return JSONResponse(
                status_code=400,
                content={"error": "contact or request note is required"},
            )

        try:
            result = (
                supabase.table("handoff_requests")
                .insert(
                    {
                        "session_id": safe_session_id,
                        "customer_name": safe_name or None,
                        "contact_value": safe_contact or None,
                        "preferred_channel": safe_channel,
                        "request_note": safe_note or None,
                        "intent_name": safe_intent or None,
                        "source": safe_source,
                        "job_number": safe_job_number or None,
                        "user_message": safe_user_message or None,
                        "bot_reply": safe_bot_reply or None,
                        "status": "open",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )
        except Exception as exc:
            self.security_service.log_server_error("create_handoff_request", exc)
            return self.security_service.safe_error_response("handoff create failed")

        rows = result.data or []
        handoff_id = rows[0].get("id") if rows else None
        return {
            "ok": True,
            "handoff_id": handoff_id,
            "status": "open",
        }

    def update_handoff_request(self, body: HandoffUpdatePayload) -> JSONResponse | HandoffUpdateResponse:
        legacy_main = _legacy()
        supabase = legacy_main.get_supabase_client()
        if not supabase:
            return self.security_service.safe_error_response("admin storage unavailable")

        safe_note = legacy_main._sanitize_log_text(body.note, 800)
        safe_owner = legacy_main._sanitize_log_text(body.owner_name, 120)

        try:
            supabase.table("handoff_requests").update(
                {
                    "status": body.status,
                    "staff_note": safe_note or None,
                    "owner_name": safe_owner or None,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("id", body.handoff_id).execute()
        except Exception as exc:
            self.security_service.log_server_error("update_handoff_request", exc)
            return self.security_service.safe_error_response("handoff update failed")

        return HandoffUpdateResponse(
            ok=True,
            handoff_id=body.handoff_id,
            status=body.status,
            owner_name=safe_owner,
        )

    async def trigger_knowledge_sync(self) -> JSONResponse | SyncRunResponse:
        legacy_main = _legacy()
        try:
            result = await legacy_main._execute_logged_sync("manual_admin", "admin_analytics")
        except Exception as exc:
            self.security_service.log_server_error("trigger_knowledge_sync", exc)
            return self.security_service.safe_error_response("knowledge sync failed")

        if result.get("status") == "busy":
            return JSONResponse(status_code=409, content={"error": "knowledge sync already running"})

        return SyncRunResponse(ok=True, **result)

    async def approve_to_sheet(self, body: SheetApprovalPayload) -> JSONResponse | dict[str, Any]:
        legacy_main = _legacy()
        sheet_id = os.environ.get("SHEET_ID", "").strip()
        if not sheet_id:
            return self.security_service.safe_error_response("sheet integration unavailable")

        safe_topic = (body.topic or "").strip() or "general"
        safe_question = legacy_main._sanitize_log_text(body.question, 500)
        safe_answer = legacy_main._sanitize_log_text(body.answer, 2000)
        safe_keywords = legacy_main._sanitize_log_text(body.keywords, 500)
        safe_intent = legacy_main._sanitize_log_text(body.intent, 120)
        safe_reason = legacy_main._sanitize_log_text(body.reason, 500)

        if not safe_question or not safe_answer:
            return JSONResponse(status_code=400, content={"error": "question and answer are required"})

        try:
            if legacy_main.knowledge_row_exists(sheet_id, safe_topic, safe_question):
                existing_link = legacy_main.get_sheet_tab_link(sheet_id, safe_topic)
                return JSONResponse(
                    status_code=409,
                    content={
                        "error": "row already exists in Google Sheet",
                        "topic": safe_topic,
                        "question": safe_question,
                        "sheet_url": existing_link,
                    },
                )
        except Exception as exc:
            log_with_context(logger, 40, "Sheet duplicate check failed", topic=safe_topic, question=safe_question, error=exc)

        try:
            append_result = legacy_main.append_knowledge_row(
                sheet_id,
                safe_topic,
                question=safe_question,
                answer=safe_answer,
                keywords=safe_keywords,
                intent=safe_intent,
                active=body.active,
            )
        except Exception as exc:
            self.security_service.log_server_error("approve_to_sheet_append", exc)
            return self.security_service.safe_error_response("append to Google Sheet failed")

        supabase = legacy_main.get_supabase_client()
        approved_sheet_url = ""
        try:
            approved_sheet_url = legacy_main.get_sheet_tab_link(sheet_id, safe_topic)
        except Exception as exc:
            log_with_context(logger, 40, "Sheet tab link lookup failed", topic=safe_topic, error=exc)

        if supabase:
            try:
                supabase.table("sheet_approvals").insert(
                    {
                        "chat_log_id": body.chat_log_id,
                        "topic": safe_topic,
                        "question": safe_question,
                        "answer": safe_answer,
                        "keywords": safe_keywords or None,
                        "intent": safe_intent or None,
                        "active": body.active,
                        "reason": safe_reason or None,
                    }
                ).execute()
            except Exception as exc:
                log_with_context(logger, 40, "Sheet approval write failed", chat_log_id=body.chat_log_id, topic=safe_topic, error=exc)

            if body.chat_log_id:
                try:
                    supabase.table("chat_log_reviews").upsert(
                        {
                            "chat_log_id": body.chat_log_id,
                            "status": "approved",
                            "note": "approved_to_sheet",
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }
                    ).execute()
                except Exception as exc:
                    log_with_context(logger, 40, "Chat review approve status update failed", chat_log_id=body.chat_log_id, error=exc)

        sync_status = "skipped"
        sync_error = ""
        rows_synced = 0
        failed_rows = 0
        try:
            sync_result = await legacy_main._execute_logged_sync(
                "approve_to_sheet",
                f"chat_log:{body.chat_log_id}" if body.chat_log_id else "chat_log:none",
            )
            sync_status = sync_result.get("status") or "completed"
            rows_synced = int(sync_result.get("rows_synced") or 0)
            failed_rows = int(sync_result.get("failed_rows") or 0)
            sync_error = sync_result.get("error_detail") or ""
        except Exception as exc:
            sync_status = "failed"
            sync_error = str(exc)
            log_with_context(logger, 40, "Knowledge sync after approval failed", chat_log_id=body.chat_log_id, topic=safe_topic, error=exc)

        return {
            "ok": True,
            "topic": safe_topic,
            "question": safe_question,
            "updated_range": append_result.get("updates", {}).get("updatedRange"),
            "sheet_url": approved_sheet_url,
            "sync_status": sync_status,
            "rows_synced": rows_synced,
            "failed_rows": failed_rows,
            "sync_error": sync_error,
        }

    def get_sheet_tab_link(self, topic: str = "") -> JSONResponse | SheetTabLinkResponse:
        legacy_main = _legacy()
        sheet_id = os.environ.get("SHEET_ID", "").strip()
        if not sheet_id:
            return self.security_service.safe_error_response("sheet integration unavailable")

        try:
            url = legacy_main.get_sheet_tab_link(sheet_id, topic)
        except Exception as exc:
            self.security_service.log_server_error("sheet_tab_link", exc)
            return self.security_service.safe_error_response("sheet link unavailable")

        return SheetTabLinkResponse(
            ok=True,
            topic=(topic or "").strip() or "general",
            url=url,
        )

    def save_chat_feedback(self, body: ChatFeedbackPayload) -> JSONResponse | dict[str, Any]:
        legacy_main = _legacy()
        supabase = legacy_main.get_supabase_client()
        if not supabase:
            return JSONResponse(status_code=500, content={"error": "Supabase not configured"})

        safe_session_id = legacy_main._sanitize_visitor_id(body.session_id) or "anonymous"
        safe_user_message = legacy_main._sanitize_log_text(body.user_message, 2000)
        safe_bot_reply = legacy_main._sanitize_log_text(body.bot_reply, 4000)
        try:
            matched_log = self.helper_service.find_matching_chat_log_for_feedback(
                session_id=safe_session_id,
                user_message=safe_user_message,
                bot_reply=safe_bot_reply,
            )
        except Exception as exc:
            self.security_service.log_server_error("chat_feedback_match", exc)
            matched_log = legacy_main._find_matching_chat_log_for_feedback(
                safe_session_id,
                safe_user_message,
                safe_bot_reply,
            )

        payload = {
            "chat_log_id": matched_log.get("id") if matched_log else None,
            "session_id": safe_session_id,
            "intent_name": matched_log.get("intent_name") if matched_log else None,
            "source": matched_log.get("source") if matched_log else None,
            "preferred_answer_intent": matched_log.get("preferred_answer_intent") if matched_log else None,
            "feedback_value": body.feedback_value,
            "user_message": safe_user_message,
            "bot_reply": safe_bot_reply,
        }

        try:
            self.helper_service.insert_chat_feedback(payload)
        except Exception as exc:
            self.security_service.log_server_error("chat_feedback", exc)
            try:
                supabase.table("chat_feedback").insert(payload).execute()
            except Exception as fallback_exc:
                self.security_service.log_server_error("chat_feedback_fallback", fallback_exc)
                return self.security_service.safe_error_response("feedback write failed")

        return {"ok": True, "feedback_value": body.feedback_value}
