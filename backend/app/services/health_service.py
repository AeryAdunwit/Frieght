from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..config import AppSettings
from ..logging_utils import get_logger
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

    def _check_supabase(self) -> dict[str, Any]:
        if not self.repository.is_configured():
            return {
                "status": "degraded",
                "configured": False,
                "detail": "supabase env missing",
            }

        client = self.repository.get_client()
        try:
            result = client.table("site_metrics").select("metric_key").limit(1).execute()
            return {
                "status": "ok",
                "configured": True,
                "rows_checked": len(result.data or []),
            }
        except Exception as exc:
            logger.warning("Deep health Supabase check failed: %s", exc)
            return {
                "status": "degraded",
                "configured": True,
                "detail": "supabase query failed",
            }

    def _check_google_credentials(self) -> dict[str, Any]:
        try:
            from ...sheets_loader import _load_credentials

            _load_credentials()
            return {"status": "ok", "configured": True}
        except Exception as exc:
            logger.warning("Deep health Google credentials check failed: %s", exc)
            return {
                "status": "degraded",
                "configured": bool(self.settings.sheet_id or self.settings.tracking_sheet_id),
                "detail": "google credentials invalid",
            }

    def _check_gemini(self) -> dict[str, Any]:
        if self.settings.gemini_api_key:
            return {"status": "ok", "configured": True}
        return {"status": "degraded", "configured": False, "detail": "gemini api key missing"}

    def get_basic_health(self) -> dict[str, str]:
        return {"status": "ok"}

    def get_deep_health(self) -> tuple[dict[str, Any], int]:
        checks = {
            "supabase": self._check_supabase(),
            "google_credentials": self._check_google_credentials(),
            "gemini": self._check_gemini(),
        }
        overall_status = "ok" if all(check["status"] == "ok" for check in checks.values()) else "degraded"
        payload = {
            "status": overall_status,
            "service": "frieght-backend",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        }
        status_code = 200 if overall_status == "ok" else 503
        return payload, status_code
