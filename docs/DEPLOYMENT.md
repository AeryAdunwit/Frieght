# SiS Freight Chatbot Deployment Runbook

## Monorepo layout
- `backend/`: FastAPI app, vector search, sync pipeline, tests
- `Frieght/`: live static chat UI for GitHub Pages
- `.github/workflows/`: scheduled sync job
- `docs/supabase_schema.sql`: initial Supabase setup

## 1. Supabase setup
1. Create a Supabase project.
2. Run [`docs/supabase_schema.sql`](./supabase_schema.sql) in SQL Editor.
3. Confirm `knowledge_base` and `match_knowledge` exist.

## 2. Google Sheets setup
1. Create or reuse a service account with Sheets read access.
2. Share the knowledge-base sheet with the service account email.
3. Ensure every knowledge tab uses these headers:
   - `question`
   - `answer`
   - `keywords`
   - `intent`
   - `active` (use `no` to exclude)

## 3. Backend deployment
1. Copy [`backend/.env.example`](../backend/.env.example) to local `.env` for development only.
2. Deploy Render with start command:
   - `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - future target after parity sign-off: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - or build with the root `Dockerfile` for container-based deployment
3. Set environment variables in Render:
   - `SHEET_ID`
   - `GOOGLE_CREDENTIALS`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_KEY`
   - `GEMINI_API_KEY`
   - `FRONTEND_URL`
   - optional admin cookie settings:
     - `ADMIN_SESSION_COOKIE_NAME`
     - `ADMIN_SESSION_MAX_AGE_SECONDS`
   - optional circuit breaker toggles:
     - `ENABLE_EXTERNAL_CIRCUIT_BREAKERS=false` (default)
     - `GEMINI_CIRCUIT_FAILURE_THRESHOLD`
     - `GEMINI_CIRCUIT_RECOVERY_SECONDS`
     - `SHEETS_CIRCUIT_FAILURE_THRESHOLD`
     - `SHEETS_CIRCUIT_RECOVERY_SECONDS`
     - `TRACKING_CIRCUIT_FAILURE_THRESHOLD`
     - `TRACKING_CIRCUIT_RECOVERY_SECONDS`
   - optional monitoring toggles:
     - `SENTRY_DSN`
     - `SENTRY_ENVIRONMENT`
     - `SENTRY_TRACES_SAMPLE_RATE`
4. Verify `GET /health` returns `{"status":"ok"}`.
5. Verify `GET /readyz` returns HTTP 200 before cutting traffic.
6. Verify `GET /docs` opens Swagger UI.
7. If planning the eventual entrypoint switch, follow [BACKEND_SWITCHOVER_CHECKLIST.md](./BACKEND_SWITCHOVER_CHECKLIST.md) first.

## 4. Frontend deployment
1. Publish the `Frieght/` folder to GitHub Pages.
2. Use the live Pages URLs:
   - `https://aeryadunwit.github.io/Frieght/Frieght/index.html`
   - `https://aeryadunwit.github.io/Frieght/Frieght/admin-analytics.html`
3. Set `FRONTEND_URL` in Render to:
   - `https://aeryadunwit.github.io`
4. Set `PUBLIC_SITE_BASE_URL` in Render to:
   - `https://aeryadunwit.github.io/Frieght`

## 5. Scheduled sync
1. Add GitHub secrets:
   - `SHEET_ID`
   - `GOOGLE_CREDENTIALS`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `GEMINI_API_KEY`
2. Run the `Sync Sheets to Vector Store` workflow manually once.
3. Confirm rows appear in `knowledge_base`.

## 6. Production checks
- Rate limit returns 429 after 20 requests/minute/IP.
- Prompt injection returns 400.
- CORS is locked to the exact frontend origin.
- No secrets are committed to tracked files.
- Keys used in local development are rotated before public launch.
- `GET /health/deep` should show `supabase`, `google_credentials`, and `gemini` as `ok` before launch.
- Docker build should pass via `.github/workflows/docker-validate.yml`.
