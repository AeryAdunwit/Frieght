from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi.util import get_remote_address

from ..middleware.sanitizer import validate_message
from .tracking_core import (
    build_tracking_context,
    extract_job_number,
    format_tracking_response,
    get_tracking_prompt,
    is_tracking_request,
    lookup_tracking,
)
from ..models.chat import PublicChatPayload
from .chat_support_service import (
    build_basic_math_reply,
    build_history,
    build_intent_prompt,
    build_missing_info_prompt,
    build_response_mode_prompt,
    enhance_intent,
    format_direct_kb_reply,
    format_specialized_reply,
    knowledge_rows_to_context,
    normalize_response_mode,
    recent_text_from_history,
    resolve_knowledge_rows,
)
from .chat_runtime_service import stream_logged_text_response, stream_model_response
from .chat_prompt_service import SYSTEM_PROMPT
from .intent_router_core import classify_intent


class ChatService:
    async def handle_chat(self, request: Request, body: PublicChatPayload):
        if not os.environ.get("GEMINI_API_KEY"):
            return JSONResponse(status_code=500, content={"error": "chat service unavailable"})

        is_valid, error_message = validate_message(body.message)
        if not is_valid:
            return JSONResponse(status_code=400, content={"error": error_message})

        user_message = body.message.strip()
        conversation_memory_text = recent_text_from_history(body.history, user_message)
        intent = enhance_intent(classify_intent(user_message))
        session_id = body.session_id or request.headers.get("X-Session-Id", "") or get_remote_address(request)
        response_mode = normalize_response_mode(body.response_mode)

        basic_math_reply = build_basic_math_reply(user_message)
        if basic_math_reply and not is_tracking_request(user_message):
            return StreamingResponse(
                stream_logged_text_response(
                    basic_math_reply,
                    session_id=session_id,
                    user_message=user_message,
                    intent=intent,
                    source="math_quick",
                    job_number=None,
                ),
                media_type="text/event-stream",
            )

        job_number = extract_job_number(user_message)
        tracking_request = is_tracking_request(user_message)
        exact_job_lookup = job_number is not None and user_message == job_number

        if intent.canned_response:
            return StreamingResponse(
                stream_logged_text_response(
                    intent.canned_response,
                    session_id=session_id,
                    user_message=user_message,
                    intent=intent,
                    source="canned",
                    job_number=job_number,
                ),
                media_type="text/event-stream",
            )

        if not job_number and tracking_request:
            prompt_text = get_tracking_prompt()
            return StreamingResponse(
                stream_logged_text_response(
                    prompt_text,
                    session_id=session_id,
                    user_message=user_message,
                    intent=intent,
                    source="tracking_prompt",
                    job_number=job_number,
                ),
                media_type="text/event-stream",
            )

        if job_number:
            tracking_data = await lookup_tracking(job_number)
            if tracking_data:
                tracking_reply = format_tracking_response(tracking_data)
                return StreamingResponse(
                    stream_logged_text_response(
                        tracking_reply,
                        session_id=session_id,
                        user_message=user_message,
                        intent=intent,
                        source="tracking",
                        job_number=job_number,
                    ),
                    media_type="text/event-stream",
                )
            if tracking_request or exact_job_lookup:
                not_found_message = (
                    f"ไม่พบข้อมูลเลขที่ {job_number} ในระบบติดตาม ค้าบ\n"
                    f"ลองเช็ค Skyfrog ดูก่อนค้าบ https://track.skyfrog.net/h1IZM?TrackNo={job_number}"
                )
                return StreamingResponse(
                    stream_logged_text_response(
                        not_found_message,
                        session_id=session_id,
                        user_message=user_message,
                        intent=intent,
                        source="tracking_not_found",
                        job_number=job_number,
                    ),
                    media_type="text/event-stream",
                )

        knowledge_rows = resolve_knowledge_rows(intent, user_message)
        if intent.name in {"coverage", "document", "timeline"} and knowledge_rows:
            direct_reply = format_direct_kb_reply(intent, knowledge_rows, response_mode)
            return StreamingResponse(
                stream_logged_text_response(
                    direct_reply,
                    session_id=session_id,
                    user_message=user_message,
                    intent=intent,
                    source="knowledge_direct",
                    job_number=job_number,
                ),
                media_type="text/event-stream",
            )

        if intent.name in {"solar", "booking", "pricing", "claim"} and knowledge_rows and len(user_message) <= 220:
            specialized_reply = format_specialized_reply(
                intent,
                user_message,
                knowledge_rows,
                response_mode,
                conversation_memory_text,
            )
            if specialized_reply:
                return StreamingResponse(
                    stream_logged_text_response(
                        specialized_reply,
                        session_id=session_id,
                        user_message=user_message,
                        intent=intent,
                        source="knowledge_specialized",
                        job_number=job_number,
                    ),
                    media_type="text/event-stream",
                )

        if intent.missing_fields:
            missing_info_prompt = build_missing_info_prompt(intent, user_message, conversation_memory_text)
            if missing_info_prompt:
                return StreamingResponse(
                    stream_logged_text_response(
                        missing_info_prompt,
                        session_id=session_id,
                        user_message=user_message,
                        intent=intent,
                        source="missing_info_prompt",
                        job_number=job_number,
                    ),
                    media_type="text/event-stream",
                )

        tracking_context = await build_tracking_context(job_number) if job_number else ""
        knowledge_context = knowledge_rows_to_context(knowledge_rows)
        full_system_prompt = SYSTEM_PROMPT
        if tracking_context:
            full_system_prompt += f"\n\n[SYSTEM DATA]\n{tracking_context}"
        full_system_prompt += build_intent_prompt(intent)
        full_system_prompt += build_response_mode_prompt(response_mode)
        full_system_prompt += f"\n\n{knowledge_context}"

        history = build_history(body.history)
        return StreamingResponse(
            stream_model_response(
                user_message,
                history,
                full_system_prompt,
                session_id=session_id,
                intent=intent,
                job_number=job_number,
            ),
            media_type="text/event-stream",
        )
