from __future__ import annotations

from fastapi import Request

from ..models.handoff import HandoffPayload, HandoffUpdatePayload
from .analytics_service import AnalyticsService
from .security_service import SecurityService


class HandoffService:
    def __init__(
        self,
        analytics_service: AnalyticsService | None = None,
        security_service: SecurityService | None = None,
    ) -> None:
        self.analytics_service = analytics_service or AnalyticsService()
        self.security_service = security_service or SecurityService()

    def create_request(self, body: HandoffPayload):
        return self.analytics_service.create_handoff_request(body)

    def update_request(self, request: Request, body: HandoffUpdatePayload):
        auth_error = self.security_service.require_admin_api_key(request)
        if auth_error:
            return auth_error
        return self.analytics_service.update_handoff_request(body)
