from typing import Literal

from pydantic import BaseModel


class ChatReviewPayload(BaseModel):
    chat_log_id: int
    status: Literal["open", "resolved", "approved", "snoozed"] = "resolved"
    note: str = ""
    owner_name: str = ""


class ChatFeedbackPayload(BaseModel):
    session_id: str
    user_message: str
    bot_reply: str
    feedback_value: Literal["helpful", "not_helpful"]


class AdminSessionPayload(BaseModel):
    admin_api_key: str


class TrackingResolutionUpdatePayload(BaseModel):
    queue_id: int
    status: Literal["pending", "verified", "rejected"] = "verified"
    resolved_carrier: str = ""
    resolution_note: str = ""


class SheetApprovalPayload(BaseModel):
    chat_log_id: int | None = None
    topic: str
    question: str
    answer: str
    keywords: str = ""
    intent: str = ""
    active: str = "yes"
    reason: str = ""


ChatReviewPayload.model_rebuild()
ChatFeedbackPayload.model_rebuild()
AdminSessionPayload.model_rebuild()
TrackingResolutionUpdatePayload.model_rebuild()
SheetApprovalPayload.model_rebuild()
