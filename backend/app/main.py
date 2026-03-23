from __future__ import annotations

from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import AppSettings
from .middleware.rate_limiter import RateLimitExceeded, limiter, rate_limit_exceeded_handler
from .routers import analytics_router, chat_router, handoff_router, health_router, knowledge_router, tracking_router
from .services.monitoring_service import init_monitoring

DEFAULT_LOCAL_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]


def build_allowed_origins(settings: AppSettings | None = None) -> list[str]:
    safe_settings = settings or AppSettings()
    base_origins = [safe_settings.frontend_url] if safe_settings.frontend_url else list(DEFAULT_LOCAL_ORIGINS)
    deduped: list[str] = []
    seen: set[str] = set()
    for origin in base_origins + list(safe_settings.additional_cors_origins):
        normalized = (origin or "").strip().rstrip("/")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _extract_origin_from_header(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        return raw.rstrip("/")
    parsed = urlsplit(raw)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def create_app(settings: AppSettings | None = None) -> FastAPI:
    safe_settings = settings or AppSettings()
    app = FastAPI(
        title="SiS Freight Chatbot API",
        summary="Backend API for chat, analytics, handoff, knowledge sync, and tracking flows.",
        description=(
            "Refactored FastAPI backend for the SiS Freight chatbot stack. "
            "Use `/docs` for Swagger UI and `/redoc` for a read-only reference."
        ),
        version="2.0.0",
        contact={"name": "SiS Freight Team", "url": safe_settings.public_site_base_url},
        docs_url="/docs",
        redoc_url="/redoc",
        swagger_ui_parameters={"displayRequestDuration": True, "defaultModelsExpandDepth": 0},
        openapi_tags=[
            {"name": "chat", "description": "Chatbot request and response flows."},
            {"name": "analytics", "description": "Admin analytics, export, and review tools."},
            {"name": "health", "description": "Liveness and readiness probes."},
            {"name": "tracking", "description": "Carrier tracking and helper endpoints."},
            {"name": "handoff", "description": "Human handoff and follow-up workflows."},
            {"name": "knowledge", "description": "Knowledge sync and approval endpoints."},
        ],
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=build_allowed_origins(safe_settings),
        allow_credentials=True,
        allow_methods=["POST", "GET"],
        allow_headers=["Content-Type", "X-Session-Id", "X-Visitor-Id", "X-Admin-Key"],
    )
    init_monitoring(safe_settings)

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            allowed_origins = set(build_allowed_origins(safe_settings))
            request_origin = _extract_origin_from_header(request.headers.get("origin", ""))
            referer_origin = _extract_origin_from_header(request.headers.get("referer", ""))
            caller_origin = request_origin or referer_origin
            if caller_origin and caller_origin not in allowed_origins:
                return JSONResponse(status_code=403, content={"error": "origin not allowed"})

        response = await call_next(request)
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if request.url.path.startswith(("/analytics", "/tracking", "/chat")):
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
            )
        return response

    app.include_router(chat_router)
    app.include_router(health_router)
    app.include_router(tracking_router)
    app.include_router(analytics_router)
    app.include_router(handoff_router)
    app.include_router(knowledge_router)
    return app


app = create_app()
