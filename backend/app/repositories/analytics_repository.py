from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from ...vector_search import get_supabase_client


class AnalyticsRepository:
    def get_client(self):
        return get_supabase_client()

    def is_configured(self) -> bool:
        return self.get_client() is not None

    def fetch_chat_logs(
        self,
        *,
        days: int = 7,
        limit: int = 500,
        intent_name: str = "",
        source: str = "",
        query_text: str = "",
    ) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            raise RuntimeError("Supabase not configured")

        safe_days = max(1, min(days, 90))
        safe_limit = max(1, min(limit, 1000))
        start_at = (datetime.now(timezone.utc) - timedelta(days=safe_days)).isoformat()

        query = supabase.table("chat_logs").select(
            "id,session_id,intent_name,intent_lane,preferred_answer_intent,source,"
            "job_number,user_message,bot_reply,created_at"
        )
        query = query.gte("created_at", start_at)

        safe_intent_name = (intent_name or "").strip()
        safe_source = (source or "").strip()
        safe_query_text = " ".join((query_text or "").strip().split())[:120]
        if safe_intent_name:
            query = query.eq("intent_name", safe_intent_name)
        if safe_source:
            query = query.eq("source", safe_source)
        if safe_query_text:
            escaped_query = safe_query_text.replace(",", " ").replace("%", "")
            query = query.or_(
                ",".join(
                    [
                        f"user_message.ilike.%{escaped_query}%",
                        f"bot_reply.ilike.%{escaped_query}%",
                        f"job_number.ilike.%{escaped_query}%",
                        f"session_id.ilike.%{escaped_query}%",
                    ]
                )
            )

        result = query.order("created_at", desc=True).limit(safe_limit).execute()
        return result.data or []

    def fetch_review_statuses(self, chat_log_ids: list[int]) -> dict[int, dict[str, Any]]:
        supabase = self.get_client()
        if not supabase or not chat_log_ids:
            return {}

        try:
            result = (
                supabase.table("chat_log_reviews")
                .select("chat_log_id,status,note,owner_name,updated_at")
                .in_("chat_log_id", chat_log_ids)
                .execute()
            )
        except Exception as exc:
            print(f"Chat review status read error: {exc}")
            return {}

        status_map: dict[int, dict[str, Any]] = {}
        for row in result.data or []:
            try:
                chat_log_id = int(row.get("chat_log_id"))
            except (TypeError, ValueError):
                continue
            status_map[chat_log_id] = row
        return status_map

    def fetch_feedback_rows(self, *, days: int = 7, limit: int = 1000) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        safe_days = max(1, min(days, 90))
        safe_limit = max(1, min(limit, 2000))
        start_at = (datetime.now(timezone.utc) - timedelta(days=safe_days)).isoformat()

        try:
            result = (
                supabase.table("chat_feedback")
                .select(
                    "id,chat_log_id,session_id,intent_name,source,preferred_answer_intent,"
                    "feedback_value,user_message,bot_reply,created_at"
                )
                .gte("created_at", start_at)
                .order("created_at", desc=True)
                .limit(safe_limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            print(f"Chat feedback read error: {exc}")
            return []

    def fetch_recent_review_updates(self, *, days: int = 7, limit: int = 1000) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        safe_days = max(1, min(days, 90))
        safe_limit = max(1, min(limit, 2000))
        start_at = (datetime.now(timezone.utc) - timedelta(days=safe_days)).isoformat()

        try:
            result = (
                supabase.table("chat_log_reviews")
                .select("chat_log_id,status,note,owner_name,updated_at")
                .gte("updated_at", start_at)
                .order("updated_at", desc=True)
                .limit(safe_limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            print(f"Chat review updates read error: {exc}")
            return []

    def fetch_sheet_approval_rows(self, *, days: int = 30, limit: int = 1000) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        safe_days = max(1, min(days, 180))
        safe_limit = max(1, min(limit, 2000))
        start_at = (datetime.now(timezone.utc) - timedelta(days=safe_days)).isoformat()

        try:
            result = (
                supabase.table("sheet_approvals")
                .select("id,chat_log_id,topic,question,answer,keywords,intent,active,reason,created_at")
                .gte("created_at", start_at)
                .order("created_at", desc=True)
                .limit(safe_limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            print(f"Sheet approvals read error: {exc}")
            return []

    def fetch_handoff_rows(
        self,
        *,
        days: int = 30,
        limit: int = 1000,
        owner_name: str = "",
        query_text: str = "",
    ) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        safe_days = max(1, min(days, 180))
        safe_limit = max(1, min(limit, 2000))
        start_at = (datetime.now(timezone.utc) - timedelta(days=safe_days)).isoformat()

        query = (
            supabase.table("handoff_requests")
            .select(
                "id,session_id,customer_name,contact_value,preferred_channel,request_note,"
                "intent_name,source,job_number,user_message,bot_reply,status,owner_name,"
                "staff_note,created_at,updated_at"
            )
            .gte("created_at", start_at)
        )

        safe_owner_name = " ".join((owner_name or "").strip().split())[:120]
        if safe_owner_name:
            query = query.eq("owner_name", safe_owner_name)

        safe_query_text = " ".join((query_text or "").strip().split())[:120]
        if safe_query_text:
            escaped_query = safe_query_text.replace(",", " ").replace("%", "")
            query = query.or_(
                ",".join(
                    [
                        f"customer_name.ilike.%{escaped_query}%",
                        f"contact_value.ilike.%{escaped_query}%",
                        f"user_message.ilike.%{escaped_query}%",
                        f"job_number.ilike.%{escaped_query}%",
                        f"session_id.ilike.%{escaped_query}%",
                    ]
                )
            )

        try:
            result = query.order("created_at", desc=True).limit(safe_limit).execute()
            return result.data or []
        except Exception as exc:
            print(f"Handoff rows read error: {exc}")
            return []

    def fetch_sync_run_rows(self, *, limit: int = 50) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        safe_limit = max(1, min(limit, 200))
        try:
            result = (
                supabase.table("knowledge_sync_runs")
                .select("id,trigger_source,status,rows_synced,failed_rows,error_detail,initiated_by,created_at,started_at,finished_at")
                .order("created_at", desc=True)
                .limit(safe_limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            print(f"Knowledge sync runs read error: {exc}")
            return []

    def fetch_kb_rows(self) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        try:
            result = supabase.table("knowledge_base").select("topic,intent,question,keywords").limit(1000).execute()
            return result.data or []
        except Exception as exc:
            print(f"Knowledge base read error: {exc}")
            return []

    def find_matching_chat_log_for_feedback(
        self,
        *,
        session_id: str,
        user_message: str,
        bot_reply: str,
    ) -> dict[str, Any] | None:
        supabase = self.get_client()
        if not supabase:
            return None

        try:
            result = (
                supabase.table("chat_logs")
                .select("id,intent_name,intent_lane,preferred_answer_intent,source")
                .eq("session_id", session_id)
                .eq("user_message", user_message)
                .eq("bot_reply", bot_reply)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            return rows[0] if rows else None
        except Exception as exc:
            print(f"Chat feedback match error: {exc}")
            return None

    def insert_chat_feedback(self, payload: dict[str, Any]) -> None:
        supabase = self.get_client()
        if not supabase:
            raise RuntimeError("Supabase not configured")
        supabase.table("chat_feedback").insert(payload).execute()
