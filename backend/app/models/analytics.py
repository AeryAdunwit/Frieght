from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ChatReviewPayload(BaseModel):
    chat_log_id: int
    status: Literal["open", "resolved", "approved", "snoozed"] = "resolved"
    note: str = ""
    owner_name: str = ""


class SheetApprovalPayload(BaseModel):
    chat_log_id: int | None = None
    topic: str
    question: str
    answer: str
    keywords: str = ""
    intent: str = ""
    active: str = "yes"
    reason: str = ""

