from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def _as_bool(value: str, default: bool = False) -> bool:
    normalized = (value or "").strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class AppSettings:
    generation_model: str = field(default_factory=lambda: os.environ.get("GENERATION_MODEL", "gemini-2.5-flash-lite"))
    frontend_url: str = field(default_factory=lambda: os.environ.get("FRONTEND_URL", "https://aeryadunwit.github.io").strip())
    public_site_base_url: str = field(
        default_factory=lambda: os.environ.get(
            "PUBLIC_SITE_BASE_URL", "https://aeryadunwit.github.io/Frieght"
        ).rstrip("/")
    )
    additional_cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(os.environ.get("ADDITIONAL_CORS_ORIGINS", ""))
    )
    admin_api_key: str = field(default_factory=lambda: os.environ.get("ADMIN_API_KEY", "").strip())
    admin_session_cookie_name: str = field(
        default_factory=lambda: os.environ.get("ADMIN_SESSION_COOKIE_NAME", "frieght_admin_session").strip()
        or "frieght_admin_session"
    )
    admin_session_max_age_seconds: int = field(default_factory=lambda: int(os.environ.get("ADMIN_SESSION_MAX_AGE_SECONDS", "28800")))
    sheet_id: str = field(default_factory=lambda: os.environ.get("SHEET_ID", "").strip())
    tracking_sheet_id: str = field(
        default_factory=lambda: os.environ.get(
            "TRACKING_SHEET_ID", "1-dGeRU60BzTBRxDVWB1DmGLZfPXEcPSHNjUsKqD-sUQ"
        ).strip()
    )
    enable_tracking_resolution_queue: bool = field(
        default_factory=lambda: _as_bool(os.environ.get("ENABLE_TRACKING_RESOLUTION_QUEUE", ""), False)
    )
    supabase_url: str = field(default_factory=lambda: os.environ.get("SUPABASE_URL", "").strip())
    gemini_api_key: str = field(default_factory=lambda: os.environ.get("GEMINI_API_KEY", "").strip())
    scg_recaptcha_site_key: str = field(default_factory=lambda: os.environ.get("SCG_RECAPTCHA_SITE_KEY", "").strip())
    enable_external_circuit_breakers: bool = field(
        default_factory=lambda: _as_bool(os.environ.get("ENABLE_EXTERNAL_CIRCUIT_BREAKERS", ""), False)
    )
    gemini_circuit_failure_threshold: int = field(
        default_factory=lambda: int(os.environ.get("GEMINI_CIRCUIT_FAILURE_THRESHOLD", "3"))
    )
    gemini_circuit_recovery_seconds: int = field(
        default_factory=lambda: int(os.environ.get("GEMINI_CIRCUIT_RECOVERY_SECONDS", "30"))
    )
    sheets_circuit_failure_threshold: int = field(
        default_factory=lambda: int(os.environ.get("SHEETS_CIRCUIT_FAILURE_THRESHOLD", "3"))
    )
    sheets_circuit_recovery_seconds: int = field(
        default_factory=lambda: int(os.environ.get("SHEETS_CIRCUIT_RECOVERY_SECONDS", "30"))
    )
    tracking_circuit_failure_threshold: int = field(
        default_factory=lambda: int(os.environ.get("TRACKING_CIRCUIT_FAILURE_THRESHOLD", "3"))
    )
    tracking_circuit_recovery_seconds: int = field(
        default_factory=lambda: int(os.environ.get("TRACKING_CIRCUIT_RECOVERY_SECONDS", "30"))
    )
    sentry_dsn: str = field(default_factory=lambda: os.environ.get("SENTRY_DSN", "").strip())
    sentry_environment: str = field(default_factory=lambda: os.environ.get("SENTRY_ENVIRONMENT", "production").strip() or "production")
    sentry_traces_sample_rate: float = field(default_factory=lambda: float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.0")))
