from __future__ import annotations

import asyncio
import os

import google.generativeai as genai

from ..logging_utils import get_logger, log_with_context
from .chat_support_service import enforce_nong_godang_voice
from .intent_router_core import ChatIntent
from .runtime_support import log_chat_interaction

GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "gemini-2.5-flash-lite")

logger = get_logger(__name__)


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
    try:
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
            fallback = "แป๊บนึงค้าบ ตอนนี้ระบบตอบไม่ทัน ลองใหม่อีกที หรือเรียกทีมงานช่วยต่อได้เลย"
            log_chat_interaction(session_id, message, fallback, intent, "model_fallback", job_number)
            yield f"data: {fallback}\n\n".encode("utf-8")
            yield b"data: [DONE]\n\n"
            return

        normalized_text = enforce_nong_godang_voice("".join(emitted_parts))
        log_chat_interaction(session_id, message, normalized_text, intent, "model", job_number)
        async for payload in stream_text_response(normalized_text):
            yield payload
    except Exception as exc:
        log_with_context(logger, 40, "stream_model_response failed", error=exc)
        safe_message = "ตอนนี้ระบบตอบกลับมีสะดุดนิดหน่อยค้าบ ลองใหม่อีกครั้งได้เลย"
        log_chat_interaction(
            session_id,
            message,
            safe_message,
            intent,
            "model_error",
            job_number,
        )
        yield f"data: {safe_message}\n\n".encode("utf-8")
        yield b"data: [DONE]\n\n"
