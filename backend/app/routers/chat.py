from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Request

from ..dependencies import get_chat_service
from ..middleware.rate_limiter import limiter
from ..models.chat import PublicChatPayload
from ..services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@router.post("/chat")
@limiter.limit("20/minute")
async def chat(
    request: Request,
    body: PublicChatPayload = Body(...),
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.handle_chat(request, body)
