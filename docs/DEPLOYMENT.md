# SiS Freight Chatbot Deployment Runbook

## Monorepo layout
- `backend/`: FastAPI app, vector search, sync pipeline, tests
- `frontend/`: static chat UI for GitHub Pages
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
   - `keywords` (optional)
   - `active` (optional, use `no` to exclude)

## 3. Backend deployment
1. Copy [`backend/.env.example`](../backend/.env.example) to local `.env` for development only.
2. Deploy Render with start command:
   - `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
3. Set environment variables in Render:
   - `SHEET_ID`
   - `GOOGLE_CREDENTIALS`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_KEY`
   - `GEMINI_API_KEY`
   - `FRONTEND_URL`
4. Verify `GET /health` returns `{"status":"ok"}`.

## 4. Frontend deployment
1. Update `<meta name="api-base-url">` in [`frontend/index.html`](../frontend/index.html) with the Render URL.
2. Publish the `frontend/` folder to GitHub Pages.
3. Set `FRONTEND_URL` in Render to the exact GitHub Pages origin.

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
