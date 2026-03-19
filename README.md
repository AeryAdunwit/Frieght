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
- Sync command:
  - `python -m backend.sync_vectors`

## Tests
- `python -m unittest discover backend/tests`
