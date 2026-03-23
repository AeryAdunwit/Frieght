from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import AppSettings
from .middleware.rate_limiter import RateLimitExceeded, limiter, rate_limit_exceeded_handler
from .routers import analytics_router, chat_router, handoff_router, health_router, knowledge_router, tracking_router

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
    return base_origins + list(safe_settings.additional_cors_origins)


def create_app(settings: AppSettings | None = None) -> FastAPI:
    safe_settings = settings or AppSettings()
    app = FastAPI(title="SiS Freight Chatbot API")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=build_allowed_origins(safe_settings),
        allow_methods=["POST", "GET"],
        allow_headers=["Content-Type", "X-Session-Id", "X-Visitor-Id", "X-Admin-Key"],
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
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
