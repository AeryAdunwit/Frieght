from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


@dataclass(slots=True)
class AppSettings:
    generation_model: str = os.environ.get("GENERATION_MODEL", "gemini-2.5-flash-lite")
    frontend_url: str = os.environ.get("FRONTEND_URL", "https://aeryadunwit.github.io").strip()
    public_site_base_url: str = os.environ.get(
        "PUBLIC_SITE_BASE_URL", "https://aeryadunwit.github.io/Frieght"
    ).rstrip("/")
    additional_cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(os.environ.get("ADDITIONAL_CORS_ORIGINS", ""))
    )
    admin_api_key: str = os.environ.get("ADMIN_API_KEY", "").strip()
    sheet_id: str = os.environ.get("SHEET_ID", "").strip()
    tracking_sheet_id: str = os.environ.get(
        "TRACKING_SHEET_ID", "1-dGeRU60BzTBRxDVWB1DmGLZfPXEcPSHNjUsKqD-sUQ"
    ).strip()
    supabase_url: str = os.environ.get("SUPABASE_URL", "").strip()
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "").strip()
    scg_recaptcha_site_key: str = os.environ.get("SCG_RECAPTCHA_SITE_KEY", "").strip()

