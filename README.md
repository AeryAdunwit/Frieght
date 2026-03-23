# SiS Freight Chatbot

Monorepo for the SiS Freight Path 2 chatbot stack.

## Structure
- `backend/`: FastAPI API, tracking, vector search, Google Sheets sync
- `frontend/`: static chat UI for GitHub Pages
- `docs/`: SQL setup and deployment runbook

## Local development
1. Create a local `.env` from [`backend/.env.example`](backend/.env.example).
2. Install backend dependencies:
   - `python -m pip install -r backend/requirements.txt`
3. Start the API:
   - `uvicorn backend.main:app --reload`
4. Open [`frontend/index.html`](frontend/index.html) in a local static server.
5. If needed, set `GENERATION_MODEL=gemini-2.5-flash-lite` in the backend environment.

## Knowledge base setup
- Google Sheets template: [docs/KNOWLEDGE_SHEETS_TEMPLATE.md](docs/KNOWLEDGE_SHEETS_TEMPLATE.md)
- Paste-ready sheet data: [docs/GOOGLE_SHEETS_PASTE_READY.md](docs/GOOGLE_SHEETS_PASTE_READY.md)
- Setup runbook: [docs/SETUP_GOOGLE_SHEETS_SUPABASE_RENDER.md](docs/SETUP_GOOGLE_SHEETS_SUPABASE_RENDER.md)
- Supabase schema: [docs/supabase_schema.sql](docs/supabase_schema.sql)
- Sync command:
  - `python -m backend.sync_vectors`

## Visit Counter
- The footer analytics now use the backend endpoint `GET /analytics/visit`.
- The backend stores `page_views_total` and `unique_visitors_total` in Supabase.
- Run the latest [docs/supabase_schema.sql](docs/supabase_schema.sql) so Supabase has `site_metrics`, `site_visitors`, and `increment_site_metric`.
- After updating the schema, redeploy Render so the live backend can write page views and unique visitors.

## Chat Logs
- Chat interactions are stored in the Supabase table `chat_logs`.
- Each row keeps `session_id`, intent data, source lane, the user message, the bot reply, and timestamp.
- Run the latest [docs/supabase_schema.sql](docs/supabase_schema.sql) and redeploy Render before expecting live logs.

## Admin Analytics
- Admin analytics page: [`Frieght/admin-analytics.html`](Frieght/admin-analytics.html)
- Backend summary endpoint: `GET /analytics/chat-overview`
- CSV export endpoint: `GET /analytics/chat-export`
- Review queue update endpoint: `POST /analytics/chat-review`
- Feedback endpoint from widget: `POST /analytics/chat-feedback`
- Use this page to review top intents, top recurring questions, recent chat logs, and review candidates before updating Google Sheets keywords or answers.

## Tests
- Quick run:
  - `py -3 -m unittest discover -s backend/tests -v`
- Pytest + coverage gate:
  - `py -3 -m pip install -r requirements-dev.txt`
  - `py -3 -m pytest`
- Run one file:
  - `py -3 -m unittest backend.tests.test_tracking -v`
  - `py -3 -m unittest backend.tests.test_api_smoke -v`
  - `py -3 -m unittest backend.tests.test_chat_integration -v`
  - `py -3 -m unittest backend.tests.test_admin_auth_integration -v`
- Quality checks:
  - `py -3 -m ruff check backend/app backend/tests`
  - `py -3 -m mypy`
- Frontend syntax smoke check:
  - `node --check Frieght/js/chat.js`
- CI workflow:
  - GitHub Actions runs `.github/workflows/tests.yml` on every push and pull request
  - Pipeline now includes `pytest-cov`, `ruff`, and `mypy` for the refactored app core
- Full guide:
  - [docs/TESTING.md](docs/TESTING.md)

## DevOps
- Deployment runbook:
  - [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- DevOps guide:
  - [docs/DEVOPS.md](docs/DEVOPS.md)
- Deep health checks:
  - `GET /health/deep`
  - `GET /readyz`
- Container build:
  - `docker build -t frieght-backend .`
