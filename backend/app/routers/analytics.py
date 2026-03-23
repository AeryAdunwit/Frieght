from fastapi import APIRouter, Body, Depends, Request

from ..dependencies import get_analytics_service, get_security_service
from ..middleware.rate_limiter import limiter
from ..models.analytics import AdminSessionPayload, ChatFeedbackPayload, ChatReviewPayload
from ..models.responses import (
    AdminSessionResponse,
    ReviewUpdateResponse,
    VisitMetricsResponse,
)
from ..services.analytics_service import AnalyticsService
from ..services.security_service import SecurityService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/visit-count", response_model=VisitMetricsResponse)
@limiter.limit("60/minute")
async def visit_count(
    request: Request,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    return analytics_service.get_visit_count()


@router.get("/visit", response_model=VisitMetricsResponse)
@router.post("/visit", response_model=VisitMetricsResponse)
@limiter.limit("60/minute")
async def register_visit(
    request: Request,
    visitor_id: str = "",
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    return analytics_service.register_visit(visitor_id)


@router.get("/chat-overview")
@limiter.limit("30/minute")
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
    get_security_service().ensure_admin_api_key(request)
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


@router.post("/admin-session", response_model=AdminSessionResponse)
@limiter.limit("10/minute")
async def create_admin_session(
    request: Request,
    body: AdminSessionPayload = Body(...),
    security_service: SecurityService = Depends(get_security_service),
):
    return security_service.create_admin_session(request, body.admin_api_key)


@router.delete("/admin-session", response_model=AdminSessionResponse)
@limiter.limit("10/minute")
async def delete_admin_session(
    request: Request,
    security_service: SecurityService = Depends(get_security_service),
):
    return security_service.clear_admin_session(request)


@router.get("/chat-export")
@limiter.limit("20/minute")
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
    get_security_service().ensure_admin_api_key(request)
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
@limiter.limit("30/minute")
async def update_chat_review(
    request: Request,
    body: ChatReviewPayload = Body(...),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    get_security_service().ensure_admin_api_key(request)
    return analytics_service.update_chat_review(body)

@router.post("/chat-feedback")
@limiter.limit("60/minute")
async def chat_feedback(
    request: Request,
    body: ChatFeedbackPayload = Body(...),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    return analytics_service.save_chat_feedback(body)
