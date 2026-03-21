from __future__ import annotations

from pydantic import BaseModel


class TrackingLookupPayload(BaseModel):
    number: str


class ScgTrackingPayload(BaseModel):
    number: str
    token: str = ""
