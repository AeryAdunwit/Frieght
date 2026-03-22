from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Request

from ..dependencies import get_handoff_service
from ..middleware.rate_limiter import limiter
from ..models.handoff import HandoffPayload, HandoffUpdatePayload
from ..models.responses import HandoffUpdateResponse
from ..services.handoff_service import HandoffService

router = APIRouter(tags=["handoff"])


@router.post("/analytics/handoff-request")
@limiter.limit("20/minute")
async def create_handoff_request(
    request: Request,
    body: HandoffPayload = Body(...),
    handoff_service: HandoffService = Depends(get_handoff_service),
):
    return handoff_service.create_request(body)


@router.post("/analytics/handoff-update", response_model=HandoffUpdateResponse)
@limiter.limit("30/minute")
async def update_handoff_request(
    request: Request,
    body: HandoffUpdatePayload = Body(...),
    handoff_service: HandoffService = Depends(get_handoff_service),
):
    return handoff_service.update_request(request, body)
