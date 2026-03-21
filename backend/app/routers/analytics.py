from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..dependencies import get_analytics_service, get_security_service
from ..models.analytics import ChatFeedbackPayload, ChatReviewPayload, SheetApprovalPayload
from ..models.handoff import HandoffPayload, HandoffUpdatePayload
from ..models.responses import (
    HandoffUpdateResponse,
    ReviewUpdateResponse,
    SheetTabLinkResponse,
    SyncRunResponse,
    VisitMetricsResponse,
)
from ..services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/visit-count", response_model=VisitMetricsResponse)
async def visit_count(
    request: Request,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    return analytics_service.get_visit_count()


@router.get("/visit", response_model=VisitMetricsResponse)
@router.post("/visit", response_model=VisitMetricsResponse)
async def register_visit(
    request: Request,
    visitor_id: str = "",
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    return analytics_service.register_visit(visitor_id)


@router.get("/chat-overview")
async def chat_overview(
    request: Request,
    days: int = 7,
    fetch_limit: int = 500,
    recent_limit: int = 40,
    intent_name: str = "",
    source: str = "",
    query_text: str = "",
    owner_name: str = "",
    review_status: str = "",
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    auth_error = get_security_service().require_admin_api_key(request)
    if auth_error:
        return auth_error
    return analytics_service.get_chat_overview(
        days=days,
        fetch_limit=fetch_limit,
        recent_limit=recent_limit,
        intent_name=intent_name,
        source=source,
        query_text=query_text,
        owner_name=owner_name,
        review_status=review_status,
    )


@router.get("/chat-export")
async def chat_export(
    request: Request,
    days: int = 7,
    fetch_limit: int = 1000,
    intent_name: str = "",
    source: str = "",
    query_text: str = "",
    owner_name: str = "",
    review_status: str = "",
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    auth_error = get_security_service().require_admin_api_key(request)
    if auth_error:
        return auth_error
    return analytics_service.export_chat_logs(
        days=days,
        fetch_limit=fetch_limit,
        intent_name=intent_name,
        source=source,
        query_text=query_text,
        owner_name=owner_name,
        review_status=review_status,
    )


@router.post("/chat-review", response_model=ReviewUpdateResponse)
async def update_chat_review(
    request: Request,
    body: ChatReviewPayload,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    auth_error = get_security_service().require_admin_api_key(request)
    if auth_error:
        return auth_error
    return analytics_service.update_chat_review(body)


@router.post("/handoff-request")
async def create_handoff_request(
    request: Request,
    body: HandoffPayload,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    return analytics_service.create_handoff_request(body)


@router.post("/handoff-update", response_model=HandoffUpdateResponse)
async def update_handoff_request(
    request: Request,
    body: HandoffUpdatePayload,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    auth_error = get_security_service().require_admin_api_key(request)
    if auth_error:
        return auth_error
    return analytics_service.update_handoff_request(body)


@router.post("/knowledge-sync", response_model=SyncRunResponse)
async def trigger_knowledge_sync(
    request: Request,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    auth_error = get_security_service().require_admin_api_key(request)
    if auth_error:
        return auth_error
    return await analytics_service.trigger_knowledge_sync()


@router.post("/approve-to-sheet")
async def approve_to_sheet(
    request: Request,
    body: SheetApprovalPayload,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    auth_error = get_security_service().require_admin_api_key(request)
    if auth_error:
        return auth_error
    return await analytics_service.approve_to_sheet(body)


@router.get("/sheet-tab-link", response_model=SheetTabLinkResponse)
async def sheet_tab_link(
    request: Request,
    topic: str = "",
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    auth_error = get_security_service().require_admin_api_key(request)
    if auth_error:
        return auth_error
    return analytics_service.get_sheet_tab_link(topic)


@router.post("/chat-feedback")
async def chat_feedback(
    request: Request,
    body: ChatFeedbackPayload,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    return analytics_service.save_chat_feedback(body)
