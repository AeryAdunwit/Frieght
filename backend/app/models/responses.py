from __future__ import annotations

from typing import Literal

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
    payload: dict[str, object] = Field(default_factory=dict)


class ChatOverviewResponse(BaseModel):
    generated_at: str
    days: int
    filters: dict[str, object] = Field(default_factory=dict)
    totals: dict[str, object] = Field(default_factory=dict)
    daily_workflow: dict[str, object] = Field(default_factory=dict)
    weekly_summary: dict[str, object] = Field(default_factory=dict)
    sla_dashboard: dict[str, object] = Field(default_factory=dict)
    top_unresolved_reasons: list[dict[str, object]] = Field(default_factory=list)
    activity_timeline: list[dict[str, object]] = Field(default_factory=list)
    intent_breakdown: list[dict[str, object]] = Field(default_factory=list)
    lane_breakdown: list[dict[str, object]] = Field(default_factory=list)
    source_breakdown: list[dict[str, object]] = Field(default_factory=list)
    preferred_answer_breakdown: list[dict[str, object]] = Field(default_factory=list)
    top_questions: list[dict[str, object]] = Field(default_factory=list)
    top_failed_questions: list[dict[str, object]] = Field(default_factory=list)
    top_job_numbers: list[dict[str, object]] = Field(default_factory=list)
    feedback_breakdown: list[dict[str, object]] = Field(default_factory=list)
    handoff_summary: dict[str, object] = Field(default_factory=dict)
    handoff_queue: list[dict[str, object]] = Field(default_factory=list)
    knowledge_automation: dict[str, object] = Field(default_factory=dict)
    available_intents: list[str] = Field(default_factory=list)
    available_sources: list[str] = Field(default_factory=list)
    available_owners: list[str] = Field(default_factory=list)
    available_statuses: list[str] = Field(default_factory=list)
    owner_dashboard: list[dict[str, object]] = Field(default_factory=list)
    agent_productivity: list[dict[str, object]] = Field(default_factory=list)
    review_examples: list[dict[str, object]] = Field(default_factory=list)
    sheet_candidates: list[dict[str, object]] = Field(default_factory=list)
    knowledge_health: list[dict[str, object]] = Field(default_factory=list)
    review_queue: list[dict[str, object]] = Field(default_factory=list)
    recent_approvals: list[dict[str, object]] = Field(default_factory=list)
    recent_logs: list[dict[str, object]] = Field(default_factory=list)
    repository_errors: list[str] = Field(default_factory=list)
