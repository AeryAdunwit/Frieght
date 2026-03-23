import os
import re
import ast
from typing import Any

from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from slowapi.util import get_remote_address

from .app.main import app
from .app.dependencies import get_security_service
from .app.models.chat import PublicChatPayload as ChatRequest
from .app.models.chat import ChatTurnPayload as ChatTurn
from .app.services.chat_support_service import (
    build_basic_math_reply as app_build_basic_math_reply,
    build_history as app_build_history,
    build_intent_prompt as app_build_intent_prompt,
    direct_topic_intent_rows as app_direct_topic_intent_rows,
    build_missing_info_prompt as app_build_missing_info_prompt,
    build_response_mode_prompt as app_build_response_mode_prompt,
    enforce_nong_godang_voice as app_enforce_nong_godang_voice,
    enhance_intent as app_enhance_intent,
    format_direct_kb_reply as app_format_direct_kb_reply,
    format_specialized_reply as app_format_specialized_reply,
    knowledge_rows_to_context as app_knowledge_rows_to_context,
    normalize_response_mode as app_normalize_response_mode,
    recent_text_from_history as app_recent_text_from_history,
    resolve_knowledge_rows as app_resolve_knowledge_rows,
    rows_for_intent as app_rows_for_intent,
    rows_for_preferred_answer_intent as app_rows_for_preferred_answer_intent,
    search_knowledge_rows as app_search_knowledge_rows,
    tokenize_thaiish as app_tokenize_thaiish,
    topic_fallback_rows as app_topic_fallback_rows,
)
from .app.services.chat_runtime_service import (
    stream_logged_text_response as app_stream_logged_text_response,
    stream_model_response as app_stream_model_response,
    stream_text_response as app_stream_text_response,
)
from .app.services.chat_prompt_service import SYSTEM_PROMPT
from .app.services.runtime_support import (
    BANGKOK_TZ as app_BANGKOK_TZ,
    bangkok_date_label as app_bangkok_date_label,
    execute_logged_sync as app_execute_logged_sync,
    find_matching_chat_log_for_feedback as app_find_matching_chat_log_for_feedback,
    get_metric_value as app_get_metric_value,
    get_total_visit_count as app_get_total_visit_count,
    get_unique_visitor_count as app_get_unique_visitor_count,
    increment_metric_value as app_increment_metric_value,
    log_chat_interaction as app_log_chat_interaction,
    normalize_question_key as app_normalize_question_key,
    register_site_visit as app_register_site_visit,
    sanitize_log_text as app_sanitize_log_text,
    sanitize_visitor_id as app_sanitize_visitor_id,
    sync_lock as app_sync_lock,
    truncate_text as app_truncate_text,
)
from .intent_router import ChatIntent, classify_intent
from .sanitizer import validate_message
from .tracking import (
    build_tracking_context,
    extract_job_number,
    format_tracking_response,
    get_tracking_prompt,
    is_tracking_request,
    lookup_tracking,
)


load_dotenv()

BANGKOK_TZ = app_BANGKOK_TZ

GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "gemini-2.5-flash-lite")

NOT_FOUND_MESSAGE = "ขออภัย ไม่พบข้อมูลนี้ในระบบ กรุณาติดต่อทีมงานโดยตรงครับ"
sync_lock = app_sync_lock


def _get_metric_value(metric_key: str) -> int:
    return app_get_metric_value(metric_key)


def _get_total_visit_count() -> int:
    return app_get_total_visit_count()


def _get_unique_visitor_count() -> int:
    return app_get_unique_visitor_count()


def _increment_metric_value(metric_key: str, delta: int = 1) -> int:
    return app_increment_metric_value(metric_key, delta=delta)


def _sanitize_visitor_id(visitor_id: str) -> str:
    return app_sanitize_visitor_id(visitor_id)


def _sanitize_log_text(text: str, max_length: int = 4000) -> str:
    return app_sanitize_log_text(text, max_length=max_length)


def _truncate_text(text: str, max_length: int = 180) -> str:
    return app_truncate_text(text, max_length=max_length)


def _normalize_question_key(text: str) -> str:
    return app_normalize_question_key(text)


def _bangkok_date_label(value: str | None) -> str:
    return app_bangkok_date_label(value)


def _log_chat_interaction(
    session_id: str,
    user_message: str,
    bot_reply: str,
    intent: ChatIntent,
    source: str,
    job_number: str | None = None,
) -> None:
    app_log_chat_interaction(session_id, user_message, bot_reply, intent, source, job_number)


def _register_site_visit(visitor_id: str) -> dict[str, int]:
    return app_register_site_visit(visitor_id)


def _search_knowledge_rows(message: str, top_k: int = 3, threshold: float = 0.65) -> list[dict]:
    return app_search_knowledge_rows(message, top_k=top_k, threshold=threshold)


def _build_knowledge_context(message: str, top_k: int = 3, threshold: float = 0.65) -> str:
    results = _search_knowledge_rows(message, top_k=top_k, threshold=threshold)
    return _knowledge_rows_to_context(results)


def _knowledge_rows_to_context(results: list[dict]) -> str:
    return app_knowledge_rows_to_context(results)


def _tokenize_thaiish(text: str) -> list[str]:
    return app_tokenize_thaiish(text)


def _topic_fallback_rows(intent: ChatIntent, user_message: str, max_items: int = 2) -> list[dict]:
    return app_topic_fallback_rows(intent, user_message, max_items=max_items)


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


def _rows_for_intent(intent: ChatIntent, rows: list[dict]) -> list[dict]:
    return app_rows_for_intent(intent, rows)


def _rows_for_preferred_answer_intent(intent: ChatIntent, rows: list[dict]) -> list[dict]:
    return app_rows_for_preferred_answer_intent(intent, rows)


def _direct_topic_intent_rows(intent: ChatIntent, user_message: str) -> list[dict]:
    return app_direct_topic_intent_rows(intent, user_message)


def _resolve_knowledge_rows(intent: ChatIntent, user_message: str) -> list[dict]:
    return app_resolve_knowledge_rows(intent, user_message)


def _build_history(history: list[ChatTurn]) -> list[dict]:
    return app_build_history(history)


def _build_intent_prompt(intent: ChatIntent) -> str:
    return app_build_intent_prompt(intent)


def _normalize_response_mode(response_mode: str | None) -> str:
    return app_normalize_response_mode(response_mode)


def _build_response_mode_prompt(response_mode: str | None) -> str:
    return app_build_response_mode_prompt(response_mode)


def _enhance_intent(intent: ChatIntent) -> ChatIntent:
    return app_enhance_intent(intent)


def _enforce_nong_godang_voice(text: str) -> str:
    return app_enforce_nong_godang_voice(text)


def _format_direct_kb_reply(intent: ChatIntent, rows: list[dict], response_mode: str = "quick") -> str:
    return app_format_direct_kb_reply(intent, rows, response_mode)


def _select_distinct_answers(rows: list[dict], max_items: int = 3) -> list[str]:
    answers: list[str] = []
    seen: set[str] = set()
    for row in rows:
        answer = (row.get("answer") or "").strip()
        if not answer or answer in seen:
            continue
        seen.add(answer)
        answers.append(answer)
        if len(answers) >= max_items:
            break
    return answers


def _has_route_hint(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("ต้นทาง", "ปลายทาง", "จาก", "ไป", "รับจาก", "ส่งไป", "ถึง"))


def _has_quantity_hint(text: str) -> bool:
    lowered = text.lower()
    return bool(re.search(r"\d", lowered)) and any(
        token in lowered for token in ("แผง", "ชิ้น", "พาเลท", "พาเลต", "ลัง", "กล่อง", "กก", "kg", "ตัน", "คัน")
    )


def _has_schedule_hint(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("วันนี้", "พรุ่งนี้", "สัปดาห์", "อาทิตย์", "วันที่", "เช้า", "บ่าย", "เย็น", "ด่วน"))


def _has_product_hint(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("สินค้า", "solar", "โซลาร์", "แผง", "inverter", "อินเวอร์เตอร์", "พาเลท", "อะไหล่", "เครื่อง"))


def _normalize_basic_math_expression(message: str) -> str:
    normalized = (message or "").strip().lower()
    if not normalized or len(normalized) > 48:
        return ""

    for phrase in (
        "เท่าไหร่",
        "เท่าไร",
        "ได้อะไร",
        "ได้เท่าไหร่",
        "ได้เท่าไร",
        "คืออะไร",
        "ได้ไหม",
        "ช่วยคิด",
        "คิดให้หน่อย",
        "คำนวณให้หน่อย",
        "?",
        "=",
    ):
        normalized = normalized.replace(phrase, "")

    normalized = normalized.replace("x", "*").replace("×", "*").replace("÷", "/")
    normalized = re.sub(r"\s+", "", normalized)

    if not re.fullmatch(r"[\d.+\-*/()]+", normalized):
        return ""
    if not re.search(r"[+\-*/]", normalized):
        return ""
    if len(re.findall(r"\d+", normalized)) < 2:
        return ""
    return normalized


def _safe_eval_basic_math(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval_basic_math(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Num):
        return float(node.n)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _safe_eval_basic_math(node.operand)
        return operand if isinstance(node.op, ast.UAdd) else -operand
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        left = _safe_eval_basic_math(node.left)
        right = _safe_eval_basic_math(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if right == 0:
            raise ZeroDivisionError("division by zero")
        return left / right
    raise ValueError("unsupported math expression")


def _format_basic_math_result(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _build_basic_math_reply(message: str) -> str | None:
    return app_build_basic_math_reply(message)


def _build_missing_info_prompt(intent: ChatIntent, user_message: str, context_text: str = "") -> str:
    return app_build_missing_info_prompt(intent, user_message, context_text)


def _recent_text_from_history(history: list[ChatTurn], user_message: str, max_turns: int = 6) -> str:
    return app_recent_text_from_history(history, user_message, max_turns=max_turns)


def _build_handoff_readiness(row: dict[str, Any]) -> dict[str, Any]:
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

    return {
        "lead_score": score,
        "lead_stage": stage,
        "missing_fields": missing[:3],
    }


def _format_specialized_reply(
    intent: ChatIntent,
    user_message: str,
    rows: list[dict],
    response_mode: str = "quick",
    context_text: str = "",
) -> str:
    return app_format_specialized_reply(intent, user_message, rows, response_mode, context_text)


async def _stream_text_response(text: str):
    async for payload in app_stream_text_response(text):
        yield payload


async def _stream_logged_text_response(
    text: str,
    *,
    session_id: str,
    user_message: str,
    intent: ChatIntent,
    source: str,
    job_number: str | None = None,
):
    async for payload in app_stream_logged_text_response(
        text,
        session_id=session_id,
        user_message=user_message,
        intent=intent,
        source=source,
        job_number=job_number,
    ):
        yield payload


async def _stream_model_response(
    message: str,
    history: list[dict],
    system_instruction: str,
    *,
    session_id: str,
    intent: ChatIntent,
    job_number: str | None = None,
):
    async for payload in app_stream_model_response(
        message,
        history,
        system_instruction,
        session_id=session_id,
        intent=intent,
        job_number=job_number,
    ):
        yield payload


def _admin_auth_error() -> JSONResponse:
    return get_security_service().admin_auth_error()


def _require_admin_api_key(request: Request) -> JSONResponse | None:
    return get_security_service().require_admin_api_key(request)


def _log_server_error(label: str, exc: Exception) -> None:
    get_security_service().log_server_error(label, exc)


def _safe_error_response(message: str, status_code: int = 500) -> JSONResponse:
    return get_security_service().safe_error_response(message, status_code=status_code)


async def chat(request: Request, body: ChatRequest):
    from .app.dependencies import get_chat_service

    return await get_chat_service().handle_chat(request, body)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)

