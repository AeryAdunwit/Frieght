from __future__ import annotations

from fastapi import Request

from ..models.chat import PublicChatPayload


class ChatService:
    async def handle_chat(self, request: Request, body: PublicChatPayload):
        from ... import main as legacy_main

        return await legacy_main.chat(request, body)
