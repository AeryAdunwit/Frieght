from __future__ import annotations

import asyncio
import os

import google.generativeai as genai

from ..config import AppSettings
from ..logging_utils import get_logger, log_with_context
from .chat_support_service import enforce_nong_godang_voice
from .circuit_breaker import CircuitBreakerOpenError, get_or_create_circuit_breaker
from .intent_router_core import ChatIntent
from .runtime_support import log_chat_interaction

GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "gemini-2.5-flash-lite")
MODEL_EMPTY_FALLBACK = "แป๊บนึงค้าบ ตอนนี้ระบบตอบไม่ทัน ลองใหม่อีกที หรือเรียกทีมงานช่วยต่อได้เลย"
MODEL_ERROR_FALLBACK = "ตอนนี้ระบบตอบกลับมีสะดุดนิดหน่อยค้าบ ลองใหม่อีกครั้งได้เลย"

logger = get_logger(__name__)


def _get_gemini_circuit_breaker():
    settings = AppSettings()
    if not settings.enable_external_circuit_breakers:
        return None
    return get_or_create_circuit_breaker(
        "gemini",
        failure_threshold=settings.gemini_circuit_failure_threshold,
        recovery_timeout_seconds=settings.gemini_circuit_recovery_seconds,
    )


async def stream_text_response(text: str):
    for line in text.splitlines() or [""]:
        yield f"data: {line}\n".encode("utf-8")
    yield b"\n"
    yield b"data: [DONE]\n\n"


async def stream_logged_text_response(
    text: str,
    *,
    session_id: str,
    user_message: str,
    intent: ChatIntent,
    source: str,
    job_number: str | None = None,
):
    log_chat_interaction(session_id, user_message, text, intent, source, job_number)
    async for payload in stream_text_response(text):
        yield payload


async def stream_model_response(
    message: str,
    history: list[dict],
    system_instruction: str,
    *,
    session_id: str,
    intent: ChatIntent,
    job_number: str | None = None,
):
    breaker = _get_gemini_circuit_breaker()
    try:
        if breaker and breaker.is_open():
            raise CircuitBreakerOpenError("gemini circuit is open")

        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel(model_name=GENERATION_MODEL, system_instruction=system_instruction)
        chat_session = model.start_chat(history=history)
        response = chat_session.send_message(message, stream=True)

        emitted_parts: list[str] = []
        for chunk in response:
            try:
                text = getattr(chunk, "text", None)
            except Exception as exc:
                log_with_context(logger, 30, "stream_model_response chunk parse failed", error=exc)
                text = None

            if text:
                emitted_parts.append(text)
                await asyncio.sleep(0)

        if not emitted_parts:
            if breaker:
                breaker.record_success()
            log_chat_interaction(session_id, message, MODEL_EMPTY_FALLBACK, intent, "model_fallback", job_number)
            yield f"data: {MODEL_EMPTY_FALLBACK}\n\n".encode("utf-8")
            yield b"data: [DONE]\n\n"
            return

        normalized_text = enforce_nong_godang_voice("".join(emitted_parts))
        if breaker:
            breaker.record_success()
        log_chat_interaction(session_id, message, normalized_text, intent, "model", job_number)
        async for payload in stream_text_response(normalized_text):
            yield payload
    except CircuitBreakerOpenError as exc:
        log_with_context(logger, 30, "stream_model_response short-circuited", error=exc)
        log_chat_interaction(
            session_id,
            message,
            MODEL_ERROR_FALLBACK,
            intent,
            "model_circuit_open",
            job_number,
        )
        yield f"data: {MODEL_ERROR_FALLBACK}\n\n".encode("utf-8")
        yield b"data: [DONE]\n\n"
    except Exception as exc:
        if breaker:
            breaker.record_failure(exc)
        log_with_context(logger, 40, "stream_model_response failed", error=exc)
        log_chat_interaction(
            session_id,
            message,
            MODEL_ERROR_FALLBACK,
            intent,
            "model_error",
            job_number,
        )
        yield f"data: {MODEL_ERROR_FALLBACK}\n\n".encode("utf-8")
        yield b"data: [DONE]\n\n"
