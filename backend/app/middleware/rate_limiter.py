from __future__ import annotations

import re

from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def build_rate_limit_key(request: Request) -> str:
    ip_address = get_remote_address(request) or "unknown"
    session_key = (
        request.headers.get("X-Session-Id", "").strip()
        or request.headers.get("X-Visitor-Id", "").strip()
        or request.query_params.get("visitor_id", "").strip()
    )
    compact_session = re.sub(r"[^A-Za-z0-9_.:-]", "", session_key)[:80]
    return f"{ip_address}:{compact_session}" if compact_session else ip_address


limiter = Limiter(key_func=build_rate_limit_key)
rate_limit_exceeded_handler = _rate_limit_exceeded_handler

__all__ = [
    "build_rate_limit_key",
    "limiter",
    "RateLimitExceeded",
    "rate_limit_exceeded_handler",
]
