from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from ..config import AppSettings
from ..logging_utils import get_logger
from ..models.responses import BasicHealthResponse, DeepHealthResponse, HealthCheckItem
from ..repositories.supabase_repository import SupabaseRepository

logger = get_logger(__name__)


class HealthService:
    def __init__(
        self,
        settings: AppSettings | None = None,
        repository: SupabaseRepository | None = None,
    ) -> None:
        self.settings = settings or AppSettings()
        self.repository = repository or SupabaseRepository()

    def _check_supabase(self) -> HealthCheckItem:
        if not self.repository.is_configured():
            return HealthCheckItem(status="degraded", configured=False, detail="supabase env missing")

        client = self.repository.get_client()
        try:
            result = client.table("site_metrics").select("metric_key").limit(1).execute()
            return HealthCheckItem(status="ok", configured=True, rows_checked=len(result.data or []))
        except Exception as exc:
            logger.warning("Deep health Supabase check failed: %s", exc)
            return HealthCheckItem(status="degraded", configured=True, detail="supabase query failed")

    def _check_google_credentials(self) -> HealthCheckItem:
        try:
            from .sheets_core import _load_credentials

            _load_credentials()
            return HealthCheckItem(status="ok", configured=True)
        except Exception as exc:
            logger.warning("Deep health Google credentials check failed: %s", exc)
            return HealthCheckItem(
                status="degraded",
                configured=bool(self.settings.sheet_id or self.settings.tracking_sheet_id),
                detail="google credentials invalid",
            )

    def _check_gemini(self) -> HealthCheckItem:
        if self.settings.gemini_api_key:
            return HealthCheckItem(status="ok", configured=True)
        return HealthCheckItem(status="degraded", configured=False, detail="gemini api key missing")

    def get_basic_health(self) -> BasicHealthResponse:
        return BasicHealthResponse(status="ok")

    def get_deep_health(self) -> tuple[DeepHealthResponse, int]:
        checks = {
            "supabase": self._check_supabase(),
            "google_credentials": self._check_google_credentials(),
            "gemini": self._check_gemini(),
        }
        overall_status: Literal["ok", "degraded"] = "ok" if all(check.status == "ok" for check in checks.values()) else "degraded"
        payload = DeepHealthResponse(
            status=overall_status,
            service="frieght-backend",
            checked_at=datetime.now(timezone.utc).isoformat(),
            checks=checks,
        )
        status_code = 200 if overall_status == "ok" else 503
        return payload, status_code
