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

## Tests
- `python -m unittest discover backend/tests`
