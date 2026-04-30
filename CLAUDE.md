# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Backend dev server:**
```bash
uvicorn backend.main:app --reload          # current live entrypoint (compat bridge)
uvicorn backend.app.main:app --reload      # new scaffold entrypoint (target after switchover)
```

**Tests:**
```bash
python -m pytest                                             # full suite with coverage (≥70% gate)
python -m pytest backend/tests/test_tracking.py -v          # single file
python -m pytest backend/tests/test_api_smoke.py backend/tests/test_app_main.py backend/tests/test_main_compat.py backend/tests/test_root_wrappers.py -v  # parity tests only
```

**Lint / type check:**
```bash
python -m ruff check backend/app backend/tests
python -m ruff format backend/app backend/tests            # auto-format
python -m mypy                                             # only checks files listed in pyproject.toml [tool.mypy]
```

**Knowledge sync (Sheets → Supabase):**
```bash
python -m backend.sync_vectors
```

**Frontend smoke check:**
```bash
node --check Frieght/js/chat.js
node Frieght/tests/chat-message-utils.smoke.mjs
```

**Container:**
```bash
docker build -t frieght-backend .
```

**Gas Booking (Google Apps Script):**
```bash
cd gas-booking && clasp push
```

## Architecture

### Two entrypoints — one is a compatibility bridge

`backend/main.py` is the **current Render start command** target (`render.yaml` → `uvicorn backend.main:app`). It is a thin bridge that re-exports everything from `backend/app/`. All real business logic lives in `backend/app/`. The next step is switching Render to `uvicorn backend.app.main:app` once the four parity tests pass. See `tasks/plan.md` (Phase 3) and `docs/BACKEND_SWITCHOVER_CHECKLIST.md`.

**Do not add business logic to `backend/main.py`**. New code goes into `backend/app/`.

The six root-level wrapper files (`backend/intent_router.py`, `backend/sanitizer.py`, `backend/vector_search.py`, `backend/tracking.py`, `backend/sheets_loader.py`, `backend/sync_vectors.py`) are one-line re-exports kept only for import compatibility during the transition.

### Chat request flow — 4 lanes

Every request hits `POST /chat` → `ChatService.handle_chat()` → intent classification → lane dispatch:

| Lane | Trigger | Handler |
|------|---------|---------|
| **math** | arithmetic expression | `build_basic_math_reply` — no LLM |
| **tracking** | job number detected | `tracking_core` → Google Sheets direct lookup |
| **rule** | greeting / thanks / handoff phrases | canned response, no LLM |
| **knowledge** | everything else | `vector_search_core` (Supabase pgvector) → Gemini SSE stream |

- Intent classification: `backend/app/services/intent_router_core.py` → `ChatIntent` dataclass
- Vector search: `backend/app/services/vector_search_core.py` — cosine similarity, default threshold 0.65, top-k 3
- Tracking lookup: `backend/app/services/tracking_core.py` → Google Sheets (`TRACKING_SHEET_ID`)
- LLM: `backend/app/services/gemini_service.py` — model set via `GENERATION_MODEL` env var, defaults to `gemini-2.5-flash-lite`

### Key service boundaries

- `backend/app/config.py` — `AppSettings` dataclass (slots); all env var reads happen here, nowhere else
- `backend/app/dependencies.py` — FastAPI dependency injection wiring
- `backend/app/repositories/supabase_repository.py` — all Supabase reads/writes
- `backend/app/repositories/analytics_repository.py` — chat logs, page views, unique visitors
- `backend/app/middleware/sanitizer.py` — input validation and prompt injection defense; always called before any LLM path
- `backend/app/middleware/rate_limiter.py` — 20 req/min/IP via slowapi
- `backend/app/services/circuit_breaker.py` — wraps Gemini, Sheets, and Tracking calls; opt-in via `ENABLE_EXTERNAL_CIRCUIT_BREAKERS=true`

### Security / CORS

CORS origin list is built from `FRONTEND_URL` env var (exact origin, not wildcard) plus `ADDITIONAL_CORS_ORIGINS` (comma-separated). All mutating requests enforce an origin allowlist check in the `add_security_headers` middleware. `X-Frame-Options: DENY` is set globally **except** for `/tracking/porlor/search`, which is intentionally embedded in an iframe.

Admin analytics routes (`/analytics/*`) require either an `X-Admin-Key` header or a `frieght_admin_session` cookie (session max-age controlled by `ADMIN_SESSION_MAX_AGE_SECONDS`, default 8 h).

### Frontend

`Frieght/` — static files served by GitHub Pages. Chat UI at `index.html`, admin analytics at `admin-analytics.html`. Chat uses SSE streaming from `POST /chat`. A keep-alive ping hits `GET /health` every 5 minutes from the browser to prevent Render free-tier cold start.

The chat client is split into focused modules under `Frieght/js/`: `chat.js` (entry point / orchestrator), `chat-runtime.js`, `chat-message-utils.js`, `chat-network-utils.js`, `chat-conversation-utils.js`, `chat-boot-utils.js`, `chat-renderers.js`, `chat-state-utils.js`, `chat-content.js`.

### Gas Booking

`gas-booking/` is a standalone Google Apps Script project (clasp-managed), entirely separate from the chatbot backend. Sheets tabs: `ดรอปดาวน์` (dropdown data), `บันทึกข้อมูล` (booking records). All server calls in the UI use `google.script.run` instead of AJAX to avoid GAS redirect/CORS issues. The UI has a main calendar (non-special provinces) and a special calendar (Bangkok, Nonthaburi, Samut Prakan, Pathum Thani — defined in `SPECIAL_PROVINCES`).

### Supabase schema

Tables: `knowledge_base` (pgvector, 768-dim Gemini embeddings), `chat_logs`, `site_metrics`, `site_visitors`. The RPC function `match_knowledge(query_embedding, match_count, match_threshold)` is used by vector search. Full schema in `docs/supabase_schema.sql`.

### Environment variables

All required vars are documented in `backend/.env.example`. Critical: `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY` (sync pipeline only), `SHEET_ID` (knowledge base), `TRACKING_SHEET_ID`, `GOOGLE_CREDENTIALS` (full service account JSON as a single string), `FRONTEND_URL` (exact GitHub Pages origin — used for CORS allowlist, not a wildcard), `ADMIN_API_KEY`.
