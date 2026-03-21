from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatTurnPayload(BaseModel):
    role: Literal["user", "model"]
    content: str


class PublicChatPayload(BaseModel):
    message: str
    history: list[ChatTurnPayload] = Field(default_factory=list)
    session_id: str = ""
    response_mode: Literal["quick", "detail"] = "quick"

