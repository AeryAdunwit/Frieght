from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BasicHealthResponse(BaseModel):
    status: Literal["ok"]


class HealthCheckItem(BaseModel):
    status: Literal["ok", "degraded"]
    configured: bool
    detail: str = ""
    rows_checked: int = 0


class DeepHealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    checked_at: str
    checks: dict[str, HealthCheckItem]


class PublicConfigResponse(BaseModel):
    admin_auth_enabled: bool
    scg_recaptcha_site_key: str = ""


class VisitMetricsResponse(BaseModel):
    count: int = 0
    page_views_total: int = 0
    unique_visitors_total: int = 0


class SyncRunResponse(BaseModel):
    status: str
    rows_synced: int = 0
    failed_rows: int = 0
    error_detail: str = ""
    ok: bool = True


class SheetTabLinkResponse(BaseModel):
    ok: bool = True
    topic: str = ""
    url: str = ""


class ReviewUpdateResponse(BaseModel):
    ok: bool = True
    chat_log_id: int
    status: str
    owner_name: str = ""


class HandoffUpdateResponse(BaseModel):
    ok: bool = True
    handoff_id: int
    status: str
    owner_name: str = ""


class ScgTrackingResponse(BaseModel):
    ok: bool = True
    number: str
    payload: dict[str, Any] = Field(default_factory=dict)
