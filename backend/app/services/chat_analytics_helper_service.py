from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from ..config import AppSettings
from ..logging_utils import get_logger
from ..repositories.analytics_repository import AnalyticsRepository
from .security_service import SecurityService

logger = get_logger(__name__)


def _legacy():
    from ... import main as legacy_main

    return legacy_main


class ChatAnalyticsHelperService:
    def __init__(
        self,
        settings: AppSettings | None = None,
        repository: AnalyticsRepository | None = None,
    ) -> None:
        self.settings = settings or AppSettings()
        self.repository = repository or AnalyticsRepository()
        self.security_service = SecurityService(self.settings)

    def _truncate_text(self, text: str, max_length: int = 180) -> str:
        raw = (text or "").strip()
        if len(raw) <= max_length:
            return raw
        return raw[: max_length - 1].rstrip() + "..."

    def _normalize_question_key(self, text: str) -> str:
        normalized = " ".join((text or "").strip().lower().split())
        return normalized[:240]

    def _bangkok_date_label(self, value: str | None) -> str:
        if not value:
            return ""
        legacy_main = _legacy()
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(legacy_main.BANGKOK_TZ).date().isoformat()

    def _counter_to_rows(self, counter: Counter[str], *, key_name: str, limit: int = 10) -> list[dict[str, Any]]:
        return [{key_name: value, "count": count} for value, count in counter.most_common(limit)]

    def _suggest_sheet_topic(self, intent_name: str) -> str:
        legacy_main = _legacy()
        mapped_topics = legacy_main.INTENT_TOPIC_MAP.get((intent_name or "").strip(), set())
        if mapped_topics:
            return sorted(mapped_topics)[0]
        return "general"

    def _build_keyword_suggestions(self, question: str, intent_name: str) -> str:
        base_question = " ".join((question or "").strip().split())
        lowered = base_question.lower()
        suggestions = [base_question]

        intent_hint_map = {
            "solar": ["ธุรกิจ em คืออะไร", "ส่ง solar ผ่าน hub", "solar hub"],
            "pricing": ["ค่าส่งเท่าไหร่", "ประเมินราคา", "quotation"],
            "booking": ["จองงานยังไง", "ต้องใช้ข้อมูลอะไร", "เหมาคัน"],
            "claim": ["เคลมยังไง", "ของเสียหาย", "ส่งผิด"],
            "coverage": ["ส่งได้ทั่วประเทศไหม", "มีส่งต่างจังหวัดไหม", "เช็กพื้นที่ส่ง"],
            "document": ["ต้องใช้เอกสารอะไร", "เอกสารที่ต้องเตรียม", "เอกสารไม่ครบ"],
            "timeline": ["ใช้เวลากี่วัน", "ตัดรอบกี่โมง", "ส่งช้าเพราะอะไร"],
            "general_chat": ["มีบริการอะไรบ้าง", "ทักเจ้าหน้าที่", "สอบถามเพิ่มเติม"],
        }

        for hint in intent_hint_map.get(intent_name, []):
            if hint.lower() != lowered:
                suggestions.append(hint)

        deduped: list[str] = []
        seen: set[str] = set()
        for suggestion in suggestions:
            cleaned = suggestion.strip()
            normalized = cleaned.lower()
            if not cleaned or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(cleaned)
        return ", ".join(deduped[:4])

    def _build_draft_answer(self, question: str, intent_name: str) -> str:
        normalized = (question or "").strip().lower()
        safe_intent = (intent_name or "general").strip() or "general"

        if safe_intent == "solar":
            if any(keyword in normalized for keyword in ("ราคา", "ค่าส่ง", "ประเมิน")):
                return "ราคาจะประเมินตามต้นทาง ปลายทาง จำนวนแผง รุ่นสินค้า และเงื่อนไขหน้างานค้าบ ถ้าจะให้ช่วยต่อ ส่งรายละเอียดงานมาได้เลย"
            if any(keyword in normalized for keyword in ("เตรียม", "ข้อมูล", "เอกสาร", "แจ้งอะไร")):
                return "รบกวนส่งต้นทาง ปลายทาง จำนวนแผง รุ่นสินค้า วันที่ต้องการส่ง และเงื่อนไขหน้างานมาได้เลยค้าบ เดี๋ยวน้องช่วยไล่ต่อให้"
            if any(keyword in normalized for keyword in ("ข้อจำกัด", "เงื่อนไข", "ระวัง")):
                return "ข้อจำกัดจะขึ้นกับพื้นที่หน้างาน วิธีแพ็กสินค้า และรถที่เข้าพื้นที่ได้ค้าบ ถ้ามีรายละเอียดงาน เดี๋ยวน้องช่วยเช็กให้ตรงขึ้น"
            if any(keyword in normalized for keyword in ("เหมาะ", "งานแบบไหน", "กรณีไหน")):
                return "บริการนี้เหมาะกับงานส่งแผง Solar ที่ต้องดูหน้างานและการจัดการขนส่งเป็นพิเศษค้าบ ถ้ามีเคสจริงส่งรายละเอียดมาได้เลย"
            return "เป็นบริการสำหรับงานส่ง Solar ที่ต้องดูรายละเอียดหน้างานและการขนส่งเป็นพิเศษค้าบ ถ้าจะให้ช่วยต่อ ส่งข้อมูลงานมาได้เลย"

        if safe_intent == "pricing":
            return "ราคาจะดูจากต้นทาง ปลายทาง ประเภทสินค้า น้ำหนัก ขนาด จำนวน และเงื่อนไขหน้างานค้าบ ถ้าจะประเมินต่อ ส่งรายละเอียดงานมาได้เลย"
        if safe_intent == "booking":
            return "ถ้าจะจองงาน รบกวนส่งต้นทาง ปลายทาง ประเภทสินค้า จำนวน และวันที่ต้องการเข้ารับมาได้เลยค้าบ เดี๋ยวน้องช่วยไล่ขั้นตอนต่อให้"
        if safe_intent == "claim":
            return "ถ้ามีเคสเสียหายหรือส่งผิด รบกวนส่งเลขงาน รายละเอียดปัญหา และรูปหรือหลักฐานที่เกี่ยวข้องมาได้เลยค้าบ เดี๋ยวน้องช่วยสรุปให้ทีมต่อ"
        if safe_intent == "coverage":
            return "เรื่องพื้นที่บริการต้องดูปลายทางจริงก่อนค้าบ ถ้าส่งจังหวัดหรือจุดส่งมา เดี๋ยวน้องช่วยเช็กต่อให้"
        if safe_intent == "document":
            return "เอกสารที่ใช้จะขึ้นกับประเภทงานค้าบ ถ้าส่งรายละเอียดงานมานิดนึง เดี๋ยวน้องช่วยไล่ว่าต้องเตรียมอะไรบ้าง"
        if safe_intent == "timeline":
            return "ระยะเวลาจะขึ้นกับต้นทาง ปลายทาง รอบเข้ารับ และเงื่อนไขหน้างานค้าบ ถ้าส่งรายละเอียดมา เดี๋ยวน้องช่วยกะเวลาให้ตรงขึ้น"
        if safe_intent == "general_chat":
            return "ถามมาได้เลยค้าบ ถ้าเป็นเรื่องงาน น้องจะช่วยจับประเด็นแล้วสรุปให้สั้น ๆ ก่อน"
        return "น้องสรุปให้เบื้องต้นก่อนค้าบ ถ้าจะให้ตอบตรงเคสกว่านี้ ส่งรายละเอียดงานเพิ่มมาได้เลย"

    def build_handoff_readiness(self, row: dict[str, Any]) -> dict[str, Any]:
        contact_value = (row.get("contact_value") or "").strip()
        request_note = (row.get("request_note") or "").strip()
        owner_name = (row.get("owner_name") or "").strip()
        preferred_channel = (row.get("preferred_channel") or "phone").strip() or "phone"
        job_number = (row.get("job_number") or "").strip()
        user_message = (row.get("user_message") or "").strip()

        score = 0
        missing: list[str] = []

        if contact_value:
            score += 40
        else:
            missing.append("ช่องทางติดต่อ")
        if request_note:
            score += 25
        else:
            missing.append("สรุปสั้น ๆ")
        if job_number:
            score += 15
        if len(user_message) >= 20:
            score += 10
        if owner_name:
            score += 10
        if preferred_channel in {"phone", "line", "email"}:
            score += 5

        score = min(score, 100)
        if score >= 75:
            stage = "พร้อมตามต่อ"
        elif score >= 45:
            stage = "พอคุยต่อได้"
        else:
            stage = "ข้อมูลยังไม่พอ"

        return {"lead_score": score, "lead_stage": stage, "missing_fields": missing[:3]}

    def fetch_logs_with_review_status(
        self,
        *,
        days: int,
        limit: int,
        intent_name: str = "",
        source: str = "",
        query_text: str = "",
    ) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
        logs = self.repository.fetch_chat_logs(
            days=days,
            limit=limit,
            intent_name=intent_name,
            source=source,
            query_text=query_text,
        )
        review_status_map = self.repository.fetch_review_statuses(
            [int(row.get("id")) for row in logs if isinstance(row.get("id"), int)]
        )
        for row in logs:
            row_id = row.get("id")
            review_info = review_status_map.get(row_id if isinstance(row_id, int) else -1, {})
            row["review_status"] = (review_info.get("status") or "open").strip() or "open"
            row["review_note"] = (review_info.get("note") or "").strip()
            row["owner_name"] = (review_info.get("owner_name") or "").strip()
            row["review_updated_at"] = review_info.get("updated_at")
        return logs, review_status_map

    def build_export_rows(
        self,
        *,
        days: int,
        fetch_limit: int,
        intent_name: str,
        source: str,
        query_text: str,
        owner_name: str,
        review_status: str,
    ) -> list[dict[str, Any]]:
        rows, _ = self.fetch_logs_with_review_status(
            days=days,
            limit=fetch_limit,
            intent_name=intent_name,
            source=source,
            query_text=query_text,
        )
        safe_owner_name = " ".join(owner_name.strip().split())[:120]
        safe_review_status = " ".join(review_status.strip().split())[:40]
        if safe_owner_name:
            rows = [row for row in rows if (row.get("owner_name") or "").strip() == safe_owner_name]
        if safe_review_status:
            rows = [
                row
                for row in rows
                if ((row.get("review_status") or "open").strip() or "open") == safe_review_status
            ]
        return rows

    def build_sheet_candidates(
        self,
        *,
        top_questions: list[dict[str, Any]],
        review_logs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        seen_questions: set[str] = set()
        approval_rows = self.repository.fetch_sheet_approval_rows(days=180, limit=2000)

        def add_candidate(
            question: str,
            intent_name: str,
            reason: str,
            *,
            chat_log_id: int | None = None,
            source: str = "",
        ) -> None:
            cleaned_question = self._truncate_text(question, 140)
            if not cleaned_question:
                return
            normalized_question = self._normalize_question_key(cleaned_question)
            if normalized_question in seen_questions:
                return
            seen_questions.add(normalized_question)
            safe_intent = (intent_name or "general").strip() or "general"
            suggested_topic = self._suggest_sheet_topic(safe_intent)
            suggested_answer = self._build_draft_answer(cleaned_question, safe_intent)
            suggested_keywords = self._build_keyword_suggestions(cleaned_question, safe_intent)
            already_approved = any(
                self._normalize_question_key(row.get("question") or "") == normalized_question
                and (row.get("topic") or "").strip() == suggested_topic
                for row in approval_rows
            )
            candidates.append(
                {
                    "question": cleaned_question,
                    "suggested_topic": suggested_topic,
                    "suggested_intent": safe_intent,
                    "suggested_keywords": suggested_keywords,
                    "suggested_answer": suggested_answer,
                    "reason": reason,
                    "chat_log_id": chat_log_id,
                    "source": (source or "").strip(),
                    "active": "yes",
                    "already_approved": already_approved,
                    "sheet_row_tsv": f"{cleaned_question}\t{suggested_answer}\t{suggested_keywords}\t{safe_intent}\tyes",
                }
            )

        for row in top_questions[:8]:
            add_candidate(
                row.get("question") or "",
                row.get("intent_name") or "general",
                "คำถามนี้ถูกถามซ้ำบ่อย ควรมี answer/keywords ที่เฉพาะขึ้นในชีต",
            )

        for row in review_logs[:8]:
            add_candidate(
                row.get("user_message") or "",
                row.get("intent_name") or "general",
                "เคสนี้เคย fallback หรือ not found ควรเติมชีตเพื่อลดการตอบหลุด",
                chat_log_id=row.get("id") if isinstance(row.get("id"), int) else None,
                source=row.get("source") or "",
            )

        return candidates[:12]

    def build_chat_overview(
        self,
        *,
        days: int,
        fetch_limit: int,
        recent_limit: int,
        intent_name: str = "",
        source: str = "",
        query_text: str = "",
        owner_name: str = "",
        review_status: str = "",
    ) -> dict[str, Any]:
        legacy_main = _legacy()
        logs, review_status_map = self.fetch_logs_with_review_status(
            days=days,
            limit=fetch_limit,
            intent_name=intent_name,
            source=source,
            query_text=query_text,
        )
        feedback_rows = self.repository.fetch_feedback_rows(days=days, limit=fetch_limit)
        review_updates = self.repository.fetch_recent_review_updates(days=days, limit=fetch_limit)
        sheet_approval_rows = self.repository.fetch_sheet_approval_rows(days=max(days, 30), limit=fetch_limit)
        handoff_rows = self.repository.fetch_handoff_rows(
            days=max(days, 30),
            limit=fetch_limit,
            owner_name=owner_name,
            query_text=query_text,
        )
        sync_run_rows = self.repository.fetch_sync_run_rows(limit=20)
        kb_rows = self.repository.fetch_kb_rows()
        safe_recent_limit = max(1, min(recent_limit, 100))

        available_owners = sorted(
            {
                (row.get("owner_name") or "").strip()
                for row in [*logs, *handoff_rows]
                if (row.get("owner_name") or "").strip()
            }
        )
        available_statuses = sorted(
            {
                "open",
                "resolved",
                "approved",
                "snoozed",
                *{(row.get("review_status") or "open").strip() or "open" for row in logs},
            }
        )

        safe_owner_name = " ".join((owner_name or "").strip().split())[:120]
        if safe_owner_name:
            logs = [row for row in logs if (row.get("owner_name") or "").strip() == safe_owner_name]

        safe_review_status = " ".join((review_status or "").strip().split())[:40]
        if safe_review_status:
            logs = [row for row in logs if ((row.get("review_status") or "open").strip() or "open") == safe_review_status]

        owner_dashboard_counter: dict[str, dict[str, int | str]] = {}
        for row in logs:
            owner_value = (row.get("owner_name") or "").strip()
            if not owner_value:
                continue
            owner_entry = owner_dashboard_counter.setdefault(
                owner_value,
                {"owner_name": owner_value, "open_count": 0, "resolved_count": 0, "approved_count": 0, "total_count": 0},
            )
            row_status = (row.get("review_status") or "open").strip() or "open"
            owner_entry["total_count"] = int(owner_entry["total_count"]) + 1
            if row_status == "resolved":
                owner_entry["resolved_count"] = int(owner_entry["resolved_count"]) + 1
            elif row_status == "approved":
                owner_entry["approved_count"] = int(owner_entry["approved_count"]) + 1
            else:
                owner_entry["open_count"] = int(owner_entry["open_count"]) + 1

        agent_productivity_counter: dict[str, dict[str, int | str]] = {}

        def ensure_agent_productivity(owner_value: str) -> dict[str, int | str]:
            return agent_productivity_counter.setdefault(
                owner_value,
                {
                    "owner_name": owner_value,
                    "review_open_count": 0,
                    "review_snoozed_count": 0,
                    "review_resolved_count": 0,
                    "review_approved_count": 0,
                    "handoff_open_count": 0,
                    "handoff_contacted_count": 0,
                    "handoff_snoozed_count": 0,
                    "handoff_closed_count": 0,
                    "actions_today": 0,
                    "active_queue_count": 0,
                },
            )

        for row in logs:
            owner_value = (row.get("owner_name") or "").strip()
            if not owner_value:
                continue
            owner_entry = ensure_agent_productivity(owner_value)
            row_status = (row.get("review_status") or "open").strip() or "open"
            if row_status == "resolved":
                owner_entry["review_resolved_count"] = int(owner_entry["review_resolved_count"]) + 1
            elif row_status == "approved":
                owner_entry["review_approved_count"] = int(owner_entry["review_approved_count"]) + 1
            elif row_status == "snoozed":
                owner_entry["review_snoozed_count"] = int(owner_entry["review_snoozed_count"]) + 1
                owner_entry["active_queue_count"] = int(owner_entry["active_queue_count"]) + 1
            else:
                owner_entry["review_open_count"] = int(owner_entry["review_open_count"]) + 1
                owner_entry["active_queue_count"] = int(owner_entry["active_queue_count"]) + 1

        for row in handoff_rows:
            owner_value = (row.get("owner_name") or "").strip()
            if not owner_value:
                continue
            owner_entry = ensure_agent_productivity(owner_value)
            handoff_status_value = (row.get("status") or "open").strip() or "open"
            if handoff_status_value == "closed":
                owner_entry["handoff_closed_count"] = int(owner_entry["handoff_closed_count"]) + 1
            elif handoff_status_value == "contacted":
                owner_entry["handoff_contacted_count"] = int(owner_entry["handoff_contacted_count"]) + 1
                owner_entry["active_queue_count"] = int(owner_entry["active_queue_count"]) + 1
            elif handoff_status_value == "snoozed":
                owner_entry["handoff_snoozed_count"] = int(owner_entry["handoff_snoozed_count"]) + 1
                owner_entry["active_queue_count"] = int(owner_entry["active_queue_count"]) + 1
            else:
                owner_entry["handoff_open_count"] = int(owner_entry["handoff_open_count"]) + 1
                owner_entry["active_queue_count"] = int(owner_entry["active_queue_count"]) + 1

        unique_sessions = {row.get("session_id") or "anonymous" for row in logs}
        negative_feedback_log_ids = {
            int(row.get("chat_log_id"))
            for row in feedback_rows
            if (row.get("feedback_value") or "").strip() == "not_helpful" and isinstance(row.get("chat_log_id"), int)
        }
        review_sources = {"model_error", "model_fallback", "tracking_not_found"}
        review_logs = []
        for row in logs:
            row_id = row.get("id")
            row_source = (row.get("source") or "").strip()
            row_status = (row.get("review_status") or "open").strip() or "open"
            has_explicit_review = isinstance(row_id, int) and row_id in review_status_map
            has_negative_feedback = isinstance(row_id, int) and row_id in negative_feedback_log_ids
            should_review = row_source in review_sources or has_negative_feedback or has_explicit_review
            if should_review and row_status not in {"resolved", "approved"}:
                review_logs.append(row)

        now_bangkok = datetime.now(legacy_main.BANGKOK_TZ)
        sla_counts = {"under_1d": 0, "between_1d_3d": 0, "over_3d": 0}
        stale_review_examples: list[dict[str, Any]] = []
        for row in review_logs:
            created_at_raw = row.get("created_at")
            try:
                created_at = datetime.fromisoformat(str(created_at_raw).replace("Z", "+00:00"))
            except ValueError:
                created_at = None

            age_hours = 0.0
            if created_at is not None:
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                age_hours = max(0.0, (now_bangkok - created_at.astimezone(legacy_main.BANGKOK_TZ)).total_seconds() / 3600)

            if age_hours >= 72:
                sla_counts["over_3d"] += 1
            elif age_hours >= 24:
                sla_counts["between_1d_3d"] += 1
            else:
                sla_counts["under_1d"] += 1

            stale_review_examples.append(
                {
                    "id": row.get("id"),
                    "user_message": self._truncate_text(row.get("user_message") or "", 140),
                    "owner_name": row.get("owner_name") or "",
                    "review_status": row.get("review_status") or "open",
                    "age_hours": round(age_hours, 1),
                    "source": row.get("source") or "unknown",
                }
            )

        stale_review_examples.sort(key=lambda row: (-float(row.get("age_hours") or 0), str(row.get("user_message") or "").lower()))

        intent_counts = Counter((row.get("intent_name") or "unknown").strip() or "unknown" for row in logs)
        lane_counts = Counter((row.get("intent_lane") or "unknown").strip() or "unknown" for row in logs)
        source_counts = Counter((row.get("source") or "unknown").strip() or "unknown" for row in logs)
        preferred_intent_counts = Counter((row.get("preferred_answer_intent") or "none").strip() or "none" for row in logs)
        feedback_counts = Counter((row.get("feedback_value") or "unknown").strip() or "unknown" for row in feedback_rows)
        negative_feedback_counts = Counter(
            (row.get("intent_name") or "unknown").strip() or "unknown"
            for row in feedback_rows
            if (row.get("feedback_value") or "") == "not_helpful"
        )
        kb_topic_counts = Counter((row.get("topic") or "unknown").strip() or "unknown" for row in kb_rows)
        today_label = datetime.now(legacy_main.BANGKOK_TZ).date().isoformat()
        approvals_today = sum(1 for row in sheet_approval_rows if self._bangkok_date_label(row.get("created_at")) == today_label)
        handoffs_today = sum(1 for row in handoff_rows if self._bangkok_date_label(row.get("created_at")) == today_label)
        resolved_today = sum(
            1
            for row in review_updates
            if (row.get("status") or "").strip() == "resolved" and self._bangkok_date_label(row.get("updated_at")) == today_label
        )
        approved_today = sum(
            1
            for row in review_updates
            if (row.get("status") or "").strip() == "approved" and self._bangkok_date_label(row.get("updated_at")) == today_label
        )
        negative_feedback_today = sum(
            1
            for row in feedback_rows
            if (row.get("feedback_value") or "").strip() == "not_helpful"
            and self._bangkok_date_label(row.get("created_at")) == today_label
        )

        for row in review_updates:
            owner_value = (row.get("owner_name") or "").strip()
            if owner_value and self._bangkok_date_label(row.get("updated_at")) == today_label:
                owner_entry = ensure_agent_productivity(owner_value)
                owner_entry["actions_today"] = int(owner_entry["actions_today"]) + 1

        for row in handoff_rows:
            owner_value = (row.get("owner_name") or "").strip()
            updated_label = self._bangkok_date_label(row.get("updated_at") or row.get("created_at"))
            if owner_value and updated_label == today_label:
                owner_entry = ensure_agent_productivity(owner_value)
                owner_entry["actions_today"] = int(owner_entry["actions_today"]) + 1

        handoff_status_counts = Counter((row.get("status") or "open").strip() or "open" for row in handoff_rows)
        handoff_readiness_rows = [self.build_handoff_readiness(row) for row in handoff_rows]
        handoff_ready_count = sum(1 for item in handoff_readiness_rows if int(item.get("lead_score") or 0) >= 75)
        handoff_needs_info_count = sum(1 for item in handoff_readiness_rows if int(item.get("lead_score") or 0) < 45)
        handoff_queue = [
            {
                "id": row.get("id"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "customer_name": row.get("customer_name") or "",
                "contact_value": row.get("contact_value") or "",
                "preferred_channel": row.get("preferred_channel") or "phone",
                "request_note": self._truncate_text(row.get("request_note") or "", 220),
                "intent_name": row.get("intent_name") or "general_chat",
                "source": row.get("source") or "chat_widget",
                "job_number": row.get("job_number") or "",
                "user_message": self._truncate_text(row.get("user_message") or "", 180),
                "bot_reply": self._truncate_text(row.get("bot_reply") or "", 180),
                "status": row.get("status") or "open",
                "owner_name": row.get("owner_name") or "",
                "staff_note": row.get("staff_note") or "",
                "session_id": row.get("session_id") or "anonymous",
                **self.build_handoff_readiness(row),
            }
            for row in handoff_rows
            if (row.get("status") or "open").strip().lower() != "closed"
        ][:20]

        latest_sync = sync_run_rows[0] if sync_run_rows else None
        latest_successful_sync = next(
            (row for row in sync_run_rows if (row.get("status") or "").strip() in {"completed", "completed_with_errors"}),
            None,
        )

        unresolved_reason_counter: Counter[str] = Counter()
        unresolved_reason_labels: dict[str, str] = {}
        for row in review_logs:
            source_value = (row.get("source") or "").strip() or "unknown"
            intent_value = (row.get("intent_name") or "").strip() or "unknown"
            if source_value == "tracking_not_found":
                key = "tracking_not_found"
                label = "tracking not found"
            elif source_value == "model_fallback":
                key = "model_fallback"
                label = "model fallback"
            elif source_value == "model_error":
                key = "model_error"
                label = "model error"
            elif source_value.startswith("knowledge"):
                key = f"knowledge::{intent_value}"
                label = f"knowledge / {intent_value}"
            else:
                key = f"{source_value}::{intent_value}"
                label = f"{source_value} / {intent_value}"
            unresolved_reason_counter[key] += 1
            unresolved_reason_labels.setdefault(key, label)

        top_unresolved_reasons = [
            {"reason_key": key, "label": unresolved_reason_labels.get(key, key), "count": count}
            for key, count in unresolved_reason_counter.most_common(8)
        ]

        activity_timeline: list[dict[str, Any]] = []
        for row in feedback_rows[:80]:
            feedback_value = (row.get("feedback_value") or "").strip() or "unknown"
            feedback_label = "feedback ว่าตอบตรง" if feedback_value == "helpful" else "feedback ว่ายังไม่ตรง"
            activity_timeline.append(
                {
                    "kind": "feedback",
                    "created_at": row.get("created_at"),
                    "label": feedback_label,
                    "detail": self._truncate_text(row.get("user_message") or "", 120),
                    "owner_name": "",
                    "status": feedback_value,
                }
            )

        for row in review_updates[:80]:
            review_status_value = (row.get("status") or "").strip() or "open"
            activity_timeline.append(
                {
                    "kind": "review",
                    "created_at": row.get("updated_at"),
                    "label": f"review {review_status_value}",
                    "detail": self._truncate_text(row.get("note") or "อัปเดตสถานะรีวิว", 120),
                    "owner_name": (row.get("owner_name") or "").strip(),
                    "status": review_status_value,
                }
            )

        for row in sheet_approval_rows[:80]:
            activity_timeline.append(
                {
                    "kind": "approval",
                    "created_at": row.get("created_at"),
                    "label": "approve to sheet",
                    "detail": self._truncate_text(row.get("question") or "", 120),
                    "owner_name": "",
                    "status": "approved",
                }
            )

        for row in handoff_rows[:80]:
            activity_timeline.append(
                {
                    "kind": "handoff",
                    "created_at": row.get("updated_at") or row.get("created_at"),
                    "label": f"handoff {(row.get('status') or 'open').strip() or 'open'}",
                    "detail": self._truncate_text(row.get("request_note") or row.get("user_message") or "", 120),
                    "owner_name": (row.get("owner_name") or "").strip(),
                    "status": (row.get("status") or "open").strip() or "open",
                }
            )

        for row in sync_run_rows[:40]:
            activity_timeline.append(
                {
                    "kind": "knowledge_sync",
                    "created_at": row.get("finished_at") or row.get("started_at") or row.get("created_at"),
                    "label": f"sync {(row.get('status') or 'unknown').strip() or 'unknown'}",
                    "detail": f"rows {int(row.get('rows_synced') or 0)} | fail {int(row.get('failed_rows') or 0)}",
                    "owner_name": "",
                    "status": (row.get("status") or "unknown").strip() or "unknown",
                }
            )

        activity_timeline.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
        activity_timeline = activity_timeline[:20]

        top_question_counter: Counter[str] = Counter()
        top_question_labels: dict[str, str] = {}
        top_question_intents: dict[str, str] = {}
        top_job_counter: Counter[str] = Counter()
        for row in logs:
            normalized_question = self._normalize_question_key(row.get("user_message") or "")
            if len(normalized_question) >= 3:
                top_question_counter[normalized_question] += 1
                top_question_labels.setdefault(normalized_question, self._truncate_text(row.get("user_message") or "", 120))
                top_question_intents.setdefault(normalized_question, (row.get("intent_name") or "unknown").strip() or "unknown")
            job_number = (row.get("job_number") or "").strip()
            if job_number:
                top_job_counter[job_number] += 1

        top_questions = [
            {"question": top_question_labels[key], "count": count, "intent_name": top_question_intents.get(key, "unknown")}
            for key, count in top_question_counter.most_common(10)
        ]

        failed_question_counter: Counter[str] = Counter()
        failed_question_labels: dict[str, str] = {}
        failed_question_intents: dict[str, str] = {}
        for row in review_logs:
            normalized_question = self._normalize_question_key(row.get("user_message") or "")
            if len(normalized_question) < 3:
                continue
            failed_question_counter[normalized_question] += 1
            failed_question_labels.setdefault(normalized_question, self._truncate_text(row.get("user_message") or "", 120))
            failed_question_intents.setdefault(normalized_question, (row.get("intent_name") or "unknown").strip() or "unknown")

        top_failed_questions = [
            {"question": failed_question_labels[key], "count": count, "intent_name": failed_question_intents.get(key, "unknown")}
            for key, count in failed_question_counter.most_common(10)
        ]

        knowledge_health = []
        for intent_key in sorted(intent_counts.keys()):
            mapped_topics = legacy_main.INTENT_TOPIC_MAP.get(intent_key, set())
            kb_count = sum(kb_topic_counts.get(topic, 0) for topic in mapped_topics)
            chat_count = intent_counts.get(intent_key, 0)
            failed_count = sum(1 for row in review_logs if (row.get("intent_name") or "unknown") == intent_key)
            negative_count = negative_feedback_counts.get(intent_key, 0)
            priority_score = (chat_count * 2) + (failed_count * 8) + (negative_count * 10)

            if chat_count == 0:
                health_status = "quiet"
                priority_reason = "ยังเงียบอยู่"
            elif kb_count == 0:
                health_status = "need_knowledge"
                priority_score += 40
                priority_reason = "ยังไม่มี knowledge รองรับ"
            elif failed_count >= 3 or negative_count >= 3:
                health_status = "needs_tuning"
                priority_score += 20
                priority_reason = "มี fallback หรือ feedback ยังไม่ตรง"
            else:
                health_status = "healthy"
                priority_reason = "ความรู้พอใช้ได้แล้ว"

            knowledge_health.append(
                {
                    "intent_name": intent_key,
                    "chat_count": chat_count,
                    "kb_rows": kb_count,
                    "failed_count": failed_count,
                    "negative_feedback_count": negative_count,
                    "health_status": health_status,
                    "priority_score": priority_score,
                    "priority_reason": priority_reason,
                }
            )

        priority_intents = [
            row
            for row in sorted(
                knowledge_health,
                key=lambda item: (
                    0 if item["health_status"] == "need_knowledge" else 1 if item["health_status"] == "needs_tuning" else 2,
                    -item["priority_score"],
                    -(item["negative_feedback_count"] + item["failed_count"]),
                ),
            )
            if row["health_status"] in {"need_knowledge", "needs_tuning"}
        ][:5]

        recent_logs = [
            {
                "id": row.get("id"),
                "created_at": row.get("created_at"),
                "session_id": row.get("session_id") or "anonymous",
                "intent_name": row.get("intent_name") or "unknown",
                "intent_lane": row.get("intent_lane") or "unknown",
                "preferred_answer_intent": row.get("preferred_answer_intent") or "",
                "source": row.get("source") or "unknown",
                "job_number": row.get("job_number") or "",
                "review_status": row.get("review_status") or "open",
                "review_note": row.get("review_note") or "",
                "owner_name": row.get("owner_name") or "",
                "user_message": self._truncate_text(row.get("user_message") or "", 240),
                "bot_reply": self._truncate_text(row.get("bot_reply") or "", 320),
            }
            for row in logs[:safe_recent_limit]
        ]

        sheet_candidates = self.build_sheet_candidates(top_questions=top_questions, review_logs=review_logs)
        checklist_items = [
            {"label": "เปิด review queue แล้วเคลียร์เคส fallback/not found ก่อน", "value": len(review_logs), "status": "pending" if review_logs else "clear"},
            {"label": "เช็ก feedback ว่ายังไม่ตรงของวันนี้", "value": negative_feedback_today, "status": "pending" if negative_feedback_today else "clear"},
            {"label": "หยิบ draft ที่พร้อมแล้วส่งลง Google Sheet", "value": len(sheet_candidates), "status": "pending" if sheet_candidates else "clear"},
            {
                "label": "เช็กคิวส่งต่อเจ้าหน้าที่ที่ยังเปิดอยู่",
                "value": handoff_status_counts.get("open", 0) + handoff_status_counts.get("contacted", 0),
                "status": "pending" if handoff_status_counts.get("open", 0) + handoff_status_counts.get("contacted", 0) else "clear",
            },
        ]

        weekly_summary = {
            "period_days": max(1, min(days, 90)),
            "chat_messages": len(logs),
            "open_reviews": len(review_logs),
            "resolved_reviews": sum(1 for row in logs if ((row.get("review_status") or "open").strip() or "open") == "resolved"),
            "approved_reviews": sum(1 for row in logs if ((row.get("review_status") or "open").strip() or "open") == "approved"),
            "negative_feedback": feedback_counts.get("not_helpful", 0),
            "handoff_requests": len(handoff_rows),
            "top_owner": (
                sorted(owner_dashboard_counter.values(), key=lambda row: (-int(row["total_count"]), str(row["owner_name"]).lower()))[0]
                if owner_dashboard_counter
                else None
            ),
        }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "days": max(1, min(days, 90)),
            "filters": {
                "intent_name": (intent_name or "").strip(),
                "source": (source or "").strip(),
                "query_text": " ".join((query_text or "").strip().split())[:120],
                "owner_name": safe_owner_name,
                "review_status": safe_review_status,
            },
            "totals": {
                "chat_messages": len(logs),
                "unique_sessions": len(unique_sessions),
                "review_candidates": len(review_logs),
                "tracked_orders": sum(1 for row in logs if (row.get("job_number") or "").strip()),
                "helpful_feedback": feedback_counts.get("helpful", 0),
                "not_helpful_feedback": feedback_counts.get("not_helpful", 0),
            },
            "daily_workflow": {
                "review_date": today_label,
                "open_review_count": len(review_logs),
                "ready_to_approve_count": len(sheet_candidates),
                "negative_feedback_today": negative_feedback_today,
                "resolved_today": resolved_today,
                "approved_today": approved_today,
                "approvals_today": approvals_today,
                "handoffs_today": handoffs_today,
                "priority_intents": priority_intents,
                "checklist": checklist_items,
            },
            "weekly_summary": weekly_summary,
            "sla_dashboard": {
                "under_1d": sla_counts["under_1d"],
                "between_1d_3d": sla_counts["between_1d_3d"],
                "over_3d": sla_counts["over_3d"],
                "stale_examples": stale_review_examples[:8],
            },
            "top_unresolved_reasons": top_unresolved_reasons,
            "activity_timeline": activity_timeline,
            "intent_breakdown": self._counter_to_rows(intent_counts, key_name="intent_name", limit=12),
            "lane_breakdown": self._counter_to_rows(lane_counts, key_name="intent_lane", limit=12),
            "source_breakdown": self._counter_to_rows(source_counts, key_name="source", limit=12),
            "preferred_answer_breakdown": self._counter_to_rows(preferred_intent_counts, key_name="preferred_answer_intent", limit=12),
            "top_questions": top_questions,
            "top_failed_questions": top_failed_questions,
            "top_job_numbers": self._counter_to_rows(top_job_counter, key_name="job_number", limit=10),
            "feedback_breakdown": self._counter_to_rows(feedback_counts, key_name="feedback_value", limit=4),
            "handoff_summary": {
                "open_count": handoff_status_counts.get("open", 0),
                "contacted_count": handoff_status_counts.get("contacted", 0),
                "closed_count": handoff_status_counts.get("closed", 0),
                "total_count": len(handoff_rows),
                "today_count": handoffs_today,
                "ready_count": handoff_ready_count,
                "needs_info_count": handoff_needs_info_count,
            },
            "handoff_queue": handoff_queue,
            "knowledge_automation": {
                "sync_in_progress": legacy_main.sync_lock.locked(),
                "latest_run": latest_sync,
                "latest_successful_run": latest_successful_sync,
                "recent_runs": sync_run_rows[:8],
            },
            "available_intents": sorted(value for value in intent_counts.keys() if (value or "").strip()),
            "available_sources": sorted(value for value in source_counts.keys() if (value or "").strip()),
            "available_owners": available_owners,
            "available_statuses": available_statuses,
            "owner_dashboard": sorted(owner_dashboard_counter.values(), key=lambda row: (-int(row["open_count"]), -int(row["total_count"]), str(row["owner_name"]).lower())),
            "agent_productivity": sorted(agent_productivity_counter.values(), key=lambda row: (-int(row["active_queue_count"]), -int(row["actions_today"]), str(row["owner_name"]).lower())),
            "review_examples": [
                {
                    "id": row.get("id"),
                    "created_at": row.get("created_at"),
                    "source": row.get("source") or "unknown",
                    "intent_name": row.get("intent_name") or "unknown",
                    "review_status": row.get("review_status") or "open",
                    "review_note": row.get("review_note") or "",
                    "owner_name": row.get("owner_name") or "",
                    "user_message": self._truncate_text(row.get("user_message") or "", 180),
                    "bot_reply": self._truncate_text(row.get("bot_reply") or "", 220),
                }
                for row in review_logs[:12]
            ],
            "sheet_candidates": sheet_candidates,
            "knowledge_health": knowledge_health,
            "review_queue": [
                {
                    "id": row.get("id"),
                    "created_at": row.get("created_at"),
                    "intent_name": row.get("intent_name") or "unknown",
                    "source": row.get("source") or "unknown",
                    "user_message": self._truncate_text(row.get("user_message") or "", 220),
                    "bot_reply": self._truncate_text(row.get("bot_reply") or "", 240),
                    "review_status": row.get("review_status") or "open",
                    "review_note": row.get("review_note") or "",
                    "owner_name": row.get("owner_name") or "",
                }
                for row in review_logs[:20]
            ],
            "recent_approvals": [
                {
                    "id": row.get("id"),
                    "chat_log_id": row.get("chat_log_id"),
                    "topic": row.get("topic") or "general",
                    "intent": row.get("intent") or "general",
                    "question": self._truncate_text(row.get("question") or "", 140),
                    "created_at": row.get("created_at"),
                }
                for row in sheet_approval_rows[:10]
            ],
            "recent_logs": recent_logs,
        }

    def find_matching_chat_log_for_feedback(
        self,
        *,
        session_id: str,
        user_message: str,
        bot_reply: str,
    ) -> dict[str, Any] | None:
        legacy_main = _legacy()
        safe_session_id = legacy_main._sanitize_visitor_id(session_id) or "anonymous"
        safe_user_message = legacy_main._sanitize_log_text(user_message, 2000)
        safe_bot_reply = legacy_main._sanitize_log_text(bot_reply, 4000)
        return self.repository.find_matching_chat_log_for_feedback(
            session_id=safe_session_id,
            user_message=safe_user_message,
            bot_reply=safe_bot_reply,
        )

    def insert_chat_feedback(self, payload: dict[str, Any]) -> None:
        self.repository.insert_chat_feedback(payload)
