from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..dependencies import get_health_service
from ..models.responses import BasicHealthResponse, DeepHealthResponse
from ..services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=BasicHealthResponse)
async def health_check(
    health_service: HealthService = Depends(get_health_service),
):
    return health_service.get_basic_health()


@router.get("/health/deep", response_model=DeepHealthResponse)
async def deep_health_check(
    health_service: HealthService = Depends(get_health_service),
):
    payload, status_code = health_service.get_deep_health()
    return JSONResponse(status_code=status_code, content=payload.model_dump())


@router.get("/readyz", response_model=DeepHealthResponse)
async def readiness_check(
    health_service: HealthService = Depends(get_health_service),
):
    payload, status_code = health_service.get_deep_health()
    return JSONResponse(status_code=status_code, content=payload.model_dump())
