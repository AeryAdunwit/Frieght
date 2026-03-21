from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HandoffPayload(BaseModel):
    session_id: str
    customer_name: str = ""
    contact_value: str = ""
    preferred_channel: Literal["phone", "line", "email"] = "phone"
    request_note: str = ""
    intent_name: str = ""
    source: str = ""
    job_number: str = ""
    user_message: str = ""
    bot_reply: str = ""


class HandoffUpdatePayload(BaseModel):
    handoff_id: int
    status: Literal["open", "contacted", "closed", "snoozed"] = "contacted"
    note: str = ""
    owner_name: str = ""

