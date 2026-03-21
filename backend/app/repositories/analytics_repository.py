from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from ..constants import (
    DEFAULT_ANALYTICS_DAYS,
    DEFAULT_APPROVAL_LOOKBACK_DAYS,
    DEFAULT_EXTENDED_LIMIT,
    DEFAULT_FETCH_LIMIT,
    DEFAULT_SYNC_RUN_LIMIT,
    MAX_ANALYTICS_DAYS,
    MAX_APPROVAL_LOOKBACK_DAYS,
    MAX_EXTENDED_LIMIT,
    MAX_FETCH_LIMIT,
    MAX_OWNER_NAME_LENGTH,
    MAX_QUERY_TEXT_LENGTH,
    MAX_SYNC_RUN_LIMIT,
)
from ..logging_utils import get_logger
from ...vector_search import get_supabase_client

logger = get_logger(__name__)


class AnalyticsRepository:
    def get_client(self):
        return get_supabase_client()

    def is_configured(self) -> bool:
        return self.get_client() is not None

    def _clamp(self, value: int, minimum: int, maximum: int) -> int:
        return max(minimum, min(value, maximum))

    def _utc_start_at(self, days: int, maximum_days: int) -> str:
        safe_days = self._clamp(days, 1, maximum_days)
        return (datetime.now(timezone.utc) - timedelta(days=safe_days)).isoformat()

    def _safe_query_text(self, query_text: str) -> str:
        return " ".join((query_text or "").strip().split())[:MAX_QUERY_TEXT_LENGTH]

    def _safe_owner_name(self, owner_name: str) -> str:
        return " ".join((owner_name or "").strip().split())[:MAX_OWNER_NAME_LENGTH]

    def _execute_or_empty(self, label: str, query) -> list[dict[str, Any]]:
        try:
            result = query.execute()
            return result.data or []
        except Exception as exc:
            logger.error("%s failed: %s", label, exc)
            return []

    def fetch_chat_logs(
        self,
        *,
        days: int = DEFAULT_ANALYTICS_DAYS,
        limit: int = DEFAULT_FETCH_LIMIT,
        intent_name: str = "",
        source: str = "",
        query_text: str = "",
    ) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            raise RuntimeError("Supabase not configured")

        safe_limit = self._clamp(limit, 1, MAX_FETCH_LIMIT)
        start_at = self._utc_start_at(days, MAX_ANALYTICS_DAYS)

        query = supabase.table("chat_logs").select(
            "id,session_id,intent_name,intent_lane,preferred_answer_intent,source,"
            "job_number,user_message,bot_reply,created_at"
        )
        query = query.gte("created_at", start_at)

        safe_intent_name = (intent_name or "").strip()
        safe_source = (source or "").strip()
        safe_query_text = self._safe_query_text(query_text)
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

        rows = self._execute_or_empty("fetch_chat_logs", query.order("created_at", desc=True).limit(safe_limit))
        return rows

    def fetch_review_statuses(self, chat_log_ids: list[int]) -> dict[int, dict[str, Any]]:
        supabase = self.get_client()
        if not supabase or not chat_log_ids:
            return {}

        rows = self._execute_or_empty(
            "fetch_review_statuses",
            supabase.table("chat_log_reviews")
            .select("chat_log_id,status,note,owner_name,updated_at")
            .in_("chat_log_id", chat_log_ids),
        )

        status_map: dict[int, dict[str, Any]] = {}
        for row in rows:
            try:
                chat_log_id = int(row.get("chat_log_id"))
            except (TypeError, ValueError):
                continue
            status_map[chat_log_id] = row
        return status_map

    def fetch_feedback_rows(self, *, days: int = DEFAULT_ANALYTICS_DAYS, limit: int = DEFAULT_EXTENDED_LIMIT) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        safe_limit = self._clamp(limit, 1, MAX_EXTENDED_LIMIT)
        start_at = self._utc_start_at(days, MAX_ANALYTICS_DAYS)

        return self._execute_or_empty(
            "fetch_feedback_rows",
            supabase.table("chat_feedback")
            .select(
                "id,chat_log_id,session_id,intent_name,source,preferred_answer_intent,"
                "feedback_value,user_message,bot_reply,created_at"
            )
            .gte("created_at", start_at)
            .order("created_at", desc=True)
            .limit(safe_limit),
        )

    def fetch_recent_review_updates(self, *, days: int = DEFAULT_ANALYTICS_DAYS, limit: int = DEFAULT_EXTENDED_LIMIT) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        safe_limit = self._clamp(limit, 1, MAX_EXTENDED_LIMIT)
        start_at = self._utc_start_at(days, MAX_ANALYTICS_DAYS)

        return self._execute_or_empty(
            "fetch_recent_review_updates",
            supabase.table("chat_log_reviews")
            .select("chat_log_id,status,note,owner_name,updated_at")
            .gte("updated_at", start_at)
            .order("updated_at", desc=True)
            .limit(safe_limit),
        )

    def fetch_sheet_approval_rows(self, *, days: int = DEFAULT_APPROVAL_LOOKBACK_DAYS, limit: int = DEFAULT_EXTENDED_LIMIT) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        safe_limit = self._clamp(limit, 1, MAX_EXTENDED_LIMIT)
        start_at = self._utc_start_at(days, MAX_APPROVAL_LOOKBACK_DAYS)

        return self._execute_or_empty(
            "fetch_sheet_approval_rows",
            supabase.table("sheet_approvals")
            .select("id,chat_log_id,topic,question,answer,keywords,intent,active,reason,created_at")
            .gte("created_at", start_at)
            .order("created_at", desc=True)
            .limit(safe_limit),
        )

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

        safe_limit = self._clamp(limit, 1, MAX_EXTENDED_LIMIT)
        start_at = self._utc_start_at(days, MAX_APPROVAL_LOOKBACK_DAYS)

        query = (
            supabase.table("handoff_requests")
            .select(
                "id,session_id,customer_name,contact_value,preferred_channel,request_note,"
                "intent_name,source,job_number,user_message,bot_reply,status,owner_name,"
                "staff_note,created_at,updated_at"
            )
            .gte("created_at", start_at)
        )

        safe_owner_name = self._safe_owner_name(owner_name)
        if safe_owner_name:
            query = query.eq("owner_name", safe_owner_name)

        safe_query_text = self._safe_query_text(query_text)
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

        return self._execute_or_empty("fetch_handoff_rows", query.order("created_at", desc=True).limit(safe_limit))

    def fetch_sync_run_rows(self, *, limit: int = DEFAULT_SYNC_RUN_LIMIT) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        safe_limit = self._clamp(limit, 1, MAX_SYNC_RUN_LIMIT)
        return self._execute_or_empty(
            "fetch_sync_run_rows",
            supabase.table("knowledge_sync_runs")
            .select("id,trigger_source,status,rows_synced,failed_rows,error_detail,initiated_by,created_at,started_at,finished_at")
            .order("created_at", desc=True)
            .limit(safe_limit),
        )

    def fetch_kb_rows(self) -> list[dict[str, Any]]:
        supabase = self.get_client()
        if not supabase:
            return []

        return self._execute_or_empty(
            "fetch_kb_rows",
            supabase.table("knowledge_base").select("topic,intent,question,keywords").limit(MAX_FETCH_LIMIT),
        )

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
            rows = self._execute_or_empty(
                "find_matching_chat_log_for_feedback",
                supabase.table("chat_logs")
                .select("id,intent_name,intent_lane,preferred_answer_intent,source")
                .eq("session_id", session_id)
                .eq("user_message", user_message)
                .eq("bot_reply", bot_reply)
                .order("created_at", desc=True)
                .limit(1),
            )
            return rows[0] if rows else None
        except Exception as exc:
            logger.error("find_matching_chat_log_for_feedback failed: %s", exc)
            return None

    def insert_chat_feedback(self, payload: dict[str, Any]) -> None:
        supabase = self.get_client()
        if not supabase:
            raise RuntimeError("Supabase not configured")
        supabase.table("chat_feedback").insert(payload).execute()
