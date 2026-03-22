from typing import Literal

from pydantic import BaseModel


class HandoffPayload(BaseModel):
    session_id: str
    customer_name: str = ""
    contact_value: str = ""
    preferred_channel: Literal["phone", "line", "email", "other"] = "phone"
    request_note: str = ""
    intent_name: str = ""
    source: str = ""
    job_number: str = ""
    user_message: str = ""
    bot_reply: str = ""


class HandoffUpdatePayload(BaseModel):
    handoff_id: int
    status: Literal["open", "contacted", "closed", "snoozed"] = "open"
    note: str = ""
    owner_name: str = ""


HandoffPayload.model_rebuild()
HandoffUpdatePayload.model_rebuild()
