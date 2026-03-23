from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from ..logging_utils import get_logger, log_with_context
from .knowledge_sync_core import sync
from .sheets_core import append_knowledge_row, get_sheet_tab_link, knowledge_row_exists
from .vector_search_core import get_supabase_client, invalidate_knowledge_caches

logger = get_logger(__name__)

BANGKOK_TZ = timezone(timedelta(hours=7))
sync_lock = asyncio.Lock()

INTENT_TOPIC_MAP = {
    "solar": {"solar"},
    "booking": {"booking"},
    "pricing": {"pricing"},
    "claim": {"claim"},
    "coverage": {"coverage"},
    "document": {"documents"},
    "timeline": {"timeline"},
    "general_chat": {"general"},
}


def sanitize_visitor_id(visitor_id: str) -> str:
    raw = (visitor_id or "").strip()
    if not raw:
        return ""
    sanitized = "".join(ch for ch in raw if ch.isalnum() or ch in {"-", "_"})
    return sanitized[:96]


def sanitize_log_text(text: str, max_length: int = 4000) -> str:
    return (text or "").strip()[:max_length]


def truncate_text(text: str, max_length: int = 180) -> str:
    raw = (text or "").strip()
    if len(raw) <= max_length:
        return raw
    return raw[: max_length - 1].rstrip() + "..."


def normalize_question_key(text: str) -> str:
    normalized = " ".join((text or "").strip().lower().split())
    return normalized[:240]


def bangkok_date_label(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BANGKOK_TZ).date().isoformat()


def get_metric_value(metric_key: str) -> int:
    supabase = get_supabase_client()
    if not supabase:
        return 0

    try:
        result = (
            supabase.table("site_metrics")
            .select("metric_value")
            .eq("metric_key", metric_key)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return 0
        return int(rows[0].get("metric_value") or 0)
    except Exception as exc:
        log_with_context(logger, 40, "Visit metric read failed", metric_key=metric_key, error=exc)
        return 0


def get_total_visit_count() -> int:
    return get_metric_value("page_views_total")


def get_unique_visitor_count() -> int:
    return get_metric_value("unique_visitors_total")


def increment_metric_value(metric_key: str, delta: int = 1) -> int:
    supabase = get_supabase_client()
    if not supabase:
        raise RuntimeError("Supabase not configured")

    try:
        current_value = get_metric_value(metric_key)
        next_value = current_value + delta
        supabase.table("site_metrics").upsert(
            {
                "metric_key": metric_key,
                "metric_value": next_value,
            }
        ).execute()
        return next_value
    except Exception as exc:
        log_with_context(
            logger,
            40,
            "Visit metric increment fallback failed",
            metric_key=metric_key,
            delta=delta,
            error=exc,
        )
        raise


def register_site_visit(visitor_id: str) -> dict[str, int]:
    supabase = get_supabase_client()
    if not supabase:
        raise RuntimeError("Supabase not configured")

    sanitized_visitor_id = sanitize_visitor_id(visitor_id)
    page_views_total = increment_metric_value("page_views_total")
    unique_visitors_total = get_unique_visitor_count()

    if not sanitized_visitor_id:
        return {
            "page_views_total": page_views_total,
            "unique_visitors_total": unique_visitors_total,
        }

    try:
        existing = (
            supabase.table("site_visitors")
            .select("visitor_id,visit_count")
            .eq("visitor_id", sanitized_visitor_id)
            .limit(1)
            .execute()
        )
        rows = existing.data or []

        if rows:
            next_visit_count = int(rows[0].get("visit_count") or 0) + 1
            supabase.table("site_visitors").update(
                {
                    "visit_count": next_visit_count,
                    "last_seen_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("visitor_id", sanitized_visitor_id).execute()
        else:
            supabase.table("site_visitors").insert(
                {
                    "visitor_id": sanitized_visitor_id,
                    "visit_count": 1,
                    "first_seen_at": datetime.now(timezone.utc).isoformat(),
                    "last_seen_at": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()
            unique_visitors_total = increment_metric_value("unique_visitors_total")

        return {
            "page_views_total": page_views_total,
            "unique_visitors_total": unique_visitors_total,
        }
    except Exception as exc:
        log_with_context(logger, 40, "Visit registration failed", visitor_id=sanitized_visitor_id, error=exc)
        return {
            "page_views_total": page_views_total,
            "unique_visitors_total": unique_visitors_total,
        }


def log_chat_interaction(
    session_id: str,
    user_message: str,
    bot_reply: str,
    intent: Any,
    source: str,
    job_number: str | None = None,
) -> None:
    supabase = get_supabase_client()
    if not supabase:
        return

    safe_session_id = sanitize_visitor_id(session_id) or "anonymous"
    try:
        supabase.table("chat_logs").insert(
            {
                "session_id": safe_session_id,
                "intent_name": getattr(intent, "name", "") or "",
                "intent_lane": getattr(intent, "lane", "") or "",
                "preferred_answer_intent": (getattr(intent, "preferred_answer_intent", "") or "").strip() or None,
                "source": source,
                "job_number": (job_number or "").strip() or None,
                "user_message": sanitize_log_text(user_message, 2000),
                "bot_reply": sanitize_log_text(bot_reply, 4000),
            }
        ).execute()
    except Exception as exc:
        log_with_context(
            logger,
            40,
            "Chat log write failed",
            session_id=safe_session_id,
            intent_name=getattr(intent, "name", "") or "",
            source=source,
            error=exc,
        )


def find_matching_chat_log_for_feedback(
    session_id: str,
    user_message: str,
    bot_reply: str,
) -> dict[str, Any] | None:
    supabase = get_supabase_client()
    if not supabase:
        return None

    safe_session_id = sanitize_visitor_id(session_id) or "anonymous"
    safe_user_message = sanitize_log_text(user_message, 2000)
    safe_bot_reply = sanitize_log_text(bot_reply, 4000)

    try:
        result = (
            supabase.table("chat_logs")
            .select("id,intent_name,intent_lane,preferred_answer_intent,source")
            .eq("session_id", safe_session_id)
            .eq("user_message", safe_user_message)
            .eq("bot_reply", safe_bot_reply)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None
    except Exception as exc:
        log_with_context(logger, 40, "Chat feedback match failed", session_id=safe_session_id, error=exc)
        return None


def create_sync_run(trigger_source: str, initiated_by: str = "") -> int | None:
    supabase = get_supabase_client()
    if not supabase:
        return None

    try:
        result = (
            supabase.table("knowledge_sync_runs")
            .insert(
                {
                    "trigger_source": (trigger_source or "manual").strip() or "manual",
                    "status": "running",
                    "initiated_by": sanitize_log_text(initiated_by, 120) or None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .execute()
        )
        rows = result.data or []
        if not rows:
            return None
        return int(rows[0].get("id"))
    except Exception as exc:
        log_with_context(
            logger,
            40,
            "Knowledge sync run create failed",
            trigger_source=trigger_source,
            initiated_by=initiated_by,
            error=exc,
        )
        return None


def finish_sync_run(
    run_id: int | None,
    *,
    status: str,
    rows_synced: int = 0,
    failed_rows: int = 0,
    error_detail: str = "",
) -> None:
    supabase = get_supabase_client()
    if not supabase or not run_id:
        return

    try:
        supabase.table("knowledge_sync_runs").update(
            {
                "status": status,
                "rows_synced": max(0, int(rows_synced or 0)),
                "failed_rows": max(0, int(failed_rows or 0)),
                "error_detail": sanitize_log_text(error_detail, 1000) or None,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", run_id).execute()
    except Exception as exc:
        log_with_context(logger, 40, "Knowledge sync run finish failed", run_id=run_id, status=status, error=exc)


async def execute_logged_sync(trigger_source: str, initiated_by: str = "") -> dict[str, Any]:
    if sync_lock.locked():
        return {"status": "busy", "rows_synced": 0, "failed_rows": 0, "error_detail": ""}

    async with sync_lock:
        run_id = create_sync_run(trigger_source, initiated_by)
        try:
            sync_result = await asyncio.to_thread(sync)
            invalidate_knowledge_caches()
            rows_synced = int((sync_result or {}).get("rows_synced") or 0)
            failed_rows = int((sync_result or {}).get("failed_rows") or 0)
            status = "completed" if failed_rows == 0 else "completed_with_errors"
            finish_sync_run(
                run_id,
                status=status,
                rows_synced=rows_synced,
                failed_rows=failed_rows,
            )
            return {
                "status": status,
                "rows_synced": rows_synced,
                "failed_rows": failed_rows,
                "error_detail": "",
            }
        except Exception as exc:
            finish_sync_run(
                run_id,
                status="failed",
                error_detail=str(exc),
            )
            raise
