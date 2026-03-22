from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ..dependencies import get_tracking_service
from ..middleware.rate_limiter import limiter
from ..models.responses import PublicConfigResponse, ScgTrackingResponse
from ..models.tracking import ScgTrackingPayload
from ..services.tracking_service import TrackingService

router = APIRouter(tags=["tracking"])


@router.get("/public-config", response_model=PublicConfigResponse)
async def public_config(
    request: Request,
    tracking_service: TrackingService = Depends(get_tracking_service),
):
    return tracking_service.get_public_config()


@router.get("/tracking/porlor/search")
@limiter.limit("20/minute")
async def porlor_tracking_search(
    request: Request,
    track: str = "",
    tracking_service: TrackingService = Depends(get_tracking_service),
):
    return await tracking_service.porlor_tracking_search(track)


@router.post("/tracking/scg", response_model=ScgTrackingResponse)
@limiter.limit("20/minute")
async def scg_tracking(
    request: Request,
    body: ScgTrackingPayload,
    tracking_service: TrackingService = Depends(get_tracking_service),
):
    return await tracking_service.scg_tracking(body.number, body.token)
