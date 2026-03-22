from fastapi import APIRouter, Body, Depends, Request

from ..dependencies import get_knowledge_admin_service
from ..middleware.rate_limiter import limiter
from ..models.analytics import SheetApprovalPayload
from ..models.responses import SheetTabLinkResponse, SyncRunResponse
from ..services.knowledge_admin_service import KnowledgeAdminService

router = APIRouter(tags=["knowledge"])


@router.post("/analytics/knowledge-sync", response_model=SyncRunResponse)
@limiter.limit("10/minute")
async def trigger_knowledge_sync(
    request: Request,
    knowledge_admin_service: KnowledgeAdminService = Depends(get_knowledge_admin_service),
):
    return await knowledge_admin_service.trigger_sync(request)


@router.post("/analytics/approve-to-sheet")
@limiter.limit("20/minute")
async def approve_to_sheet(
    request: Request,
    body: SheetApprovalPayload = Body(...),
    knowledge_admin_service: KnowledgeAdminService = Depends(get_knowledge_admin_service),
):
    return await knowledge_admin_service.approve_to_sheet(request, body)


@router.get("/analytics/sheet-tab-link", response_model=SheetTabLinkResponse)
@limiter.limit("30/minute")
async def sheet_tab_link(
    request: Request,
    topic: str = "",
    knowledge_admin_service: KnowledgeAdminService = Depends(get_knowledge_admin_service),
):
    return knowledge_admin_service.get_sheet_tab_link(request, topic)
