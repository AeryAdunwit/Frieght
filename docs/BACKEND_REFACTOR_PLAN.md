# Backend Refactor Plan

This project now includes a parallel scaffold under `backend/app/` so the team
can migrate away from the current single-file backend safely.

## What is intentionally unchanged
- The live entrypoint is still `backend/main.py`
- Existing routes, analytics, tracking, chat, and knowledge sync keep working
- No folder rename from `Frieght` to `Freight` has been attempted yet because
  it would break deployed paths, GitHub Pages URLs, and helper links

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
5. Switch Render start command to `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   only after parity testing is complete

## Legacy folders
- `backend/legacy/`
- `frontend/legacy/`

These should be archived or removed only after confirming there are no active
deployments or helper pages still depending on them.
