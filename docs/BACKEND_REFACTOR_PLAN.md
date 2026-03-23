# Backend Refactor Plan

This project now includes a parallel scaffold under `backend/app/` so the team
can migrate away from the current single-file backend safely.

## What is intentionally unchanged
- The live entrypoint is still `backend/main.py`
- Existing routes, analytics, tracking, chat, and knowledge sync keep working
- No folder rename from `Frieght` to `Freight` has been attempted yet because
  it would break deployed paths, GitHub Pages URLs, and helper links

## Current status snapshot
- `backend/app/main.py` now owns app bootstrap (CORS, security headers, router wiring)
- `backend/main.py` is increasingly a compatibility layer instead of the primary implementation
- `backend/main.py` has been trimmed down to a thin bridge layer and no longer owns the large analytics/chat helper blocks that used to live there
- `backend.main.chat()` now acts as a compatibility wrapper that delegates to `backend.app.services.chat_service.ChatService`
- `backend/intent_router.py` and `backend/sanitizer.py` now act as compatibility wrappers; the active logic lives under `backend/app/`
- `backend/vector_search.py`, `backend/tracking.py`, `backend/sheets_loader.py`, and `backend/sync_vectors.py` now also act as compatibility wrappers; active logic has been moved into `backend/app/services/`
- Tests now start moving toward `backend.app.main` instead of `backend.main`
- A dedicated switchover checklist now exists at `docs/BACKEND_SWITCHOVER_CHECKLIST.md` for the eventual entrypoint change
- `backend/legacy/` has been removed from the active repo after parity work moved into `backend/app/`

## New scaffold that is ready to grow
- `backend/app/config.py`
- `backend/app/dependencies.py`
- `backend/app/models/`
- `backend/app/routers/`
- `backend/app/services/`
- `backend/app/repositories/`
- `backend/app/middleware/`
- `backend/app/main.py`

## Recommended migration order
1. Move request/response models from `backend/main.py` into `backend/app/models/`
   Status:
   - analytics and handoff payloads now live in `backend/app/models/`
2. Move Supabase read/write logic into `backend/app/repositories/`
3. Move Gemini, tracking, sheets, and knowledge orchestration into
   `backend/app/services/`
4. Add thin routers in `backend/app/routers/` and route one domain at a time
   Status:
   - analytics domain now has a dedicated service and router scaffold
   - live `backend/main.py` can delegate to the extracted analytics layer safely
   - tracking helper endpoints now have a dedicated router/service scaffold
   - admin/public-config helpers now have a shared security service scaffold
   - app bootstrap now lives in `backend/app/main.py`
5. Switch Render start command to `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   only after parity testing is complete

## Legacy folders
- Frontend/backend legacy snapshots have been removed from the active repo.
- Remaining cleanup should focus on reducing compatibility wrappers only after the runtime switch is complete.
