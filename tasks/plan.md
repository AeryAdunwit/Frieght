# Implementation Plan — SiS Freight

**Date:** 2026-04-26  
**Branch:** main  
**Status:** Ready for review

---

## Project Context

Two independent work streams exist in this repo:

| Stream | Path | State |
|--------|------|-------|
| Gas Booking (GAS) | `gas-booking/` | 5 modified files + 1 new file, uncommitted |
| Chatbot Backend | `backend/` | Refactor ~90% done; Render still points to old entrypoint |

---

## Dependency Graph

### Stream A — Gas Booking (Google Apps Script)

```
Sheets data
  └─ doget.js (getAllData, saveBookingClient, filterdata)
       └─ script.html (carlists, savecar, initCalendar, initSpecialCalendar, showDatePopup)
            └─ functionlist.html (autocomplete, getdatatable, checkvalue, getFormData)
                 └─ index.html (UI layout: dual calendar + table + form)
                      └─ style.html (CSS)
```

All 5 files ship together as a single GAS deploy. There is no partial deploy — `clasp push` replaces everything atomically.

New: `deploy.sh` — a helper script for `clasp push`. Independent of the other files.

### Stream B — Backend Switchover

```
backend/app/main.py  (new entrypoint — create_app factory)
  ├── routers/  chat, analytics, health, tracking, handoff, knowledge
  ├── services/ chat_service → gemini_service, chat_support_service,
  │             tracking_service, knowledge_service, analytics_service …
  ├── repositories/ supabase_repository, analytics_repository
  ├── models/   chat, analytics, handoff, tracking, responses
  ├── middleware/ rate_limiter, sanitizer
  └── config.py, dependencies.py

backend/main.py  (current Render entrypoint — compatibility bridge)
  └── re-exports from backend/app/ with thin wrappers

Render start command (must change last):
  uvicorn backend.main:app  →  uvicorn backend.app.main:app
```

Blocking dependency: Render start command change must happen AFTER parity tests pass.

---

## Phase 1 — Gas Booking: Commit & Deploy

**Goal:** Get the working gas-booking changes into git and deployed to GAS.

No code changes needed — features are complete. This phase is purely ship work.

### Task 1.1 — Commit gas-booking changes

**What:** Stage and commit all 5 modified files + `deploy.sh`.  
**Acceptance criteria:**
- `git status` shows clean working tree for `gas-booking/`
- Commit message documents what changed (dual calendar, popup, month filter, cache clear, google.script.run migration)

**Verification:** `git log --oneline -1` shows the commit.

### Task 1.2 — Deploy to Google Apps Script

**What:** Run `clasp push` (or `./gas-booking/deploy.sh`) to push to the live GAS project.  
**Acceptance criteria:**
- `clasp push` exits 0
- Web app URL loads without JS errors in console
- Calendar shows existing bookings
- Special calendar shows only Bangkok/Nonthaburi/Samut Prakan/Pathum Thani bookings
- Saving a new booking clears cache and calendar refreshes immediately
- Day-click popup shows correct bookings for that date
- Month filter correctly narrows the table

**Verification:** Manual smoke test in browser against the live GAS URL.

---

## ⛳ Checkpoint A

Gas booking is committed and deployed. Backend work begins only after this checkpoint so the git history stays clean.

---

## Phase 2 — Backend: Parity Verification

**Goal:** Confirm `backend/app/main.py` is a full functional replacement before touching Render.

### Task 2.1 — Run the parity test suite

**What:** Run all four tests named in `docs/BACKEND_SWITCHOVER_CHECKLIST.md`.

```bash
python -m pytest backend/tests/test_api_smoke.py \
                 backend/tests/test_app_main.py \
                 backend/tests/test_main_compat.py \
                 backend/tests/test_root_wrappers.py -v
```

**Acceptance criteria:** All four test files pass with 0 failures.  
**Verification:** pytest exit code 0; no FAILED lines in output.

### Task 2.2 — Run full test suite

**What:** Run all backend tests to catch any regressions.

```bash
python -m pytest backend/tests/ -v --tb=short
```

**Acceptance criteria:** No new failures vs. baseline (pre-existing skips are acceptable).  
**Verification:** Exit code 0 or only pre-existing failures.

---

## ⛳ Checkpoint B

Full test suite green. Entrypoint switch is safe to proceed.

---

## Phase 3 — Backend: Entrypoint Switch

**Goal:** Move Render's start command from `backend.main` to `backend.app.main`.

### Task 3.1 — Update render.yaml

**What:** Change `startCommand` in `render.yaml` from:
```
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```
to:
```
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

**Acceptance criteria:** `render.yaml` contains the new start command.  
**Verification:** `grep "startCommand" render.yaml` shows `backend.app.main:app`.

### Task 3.2 — Update Dockerfile

**What:** Update CMD/ENTRYPOINT in `Dockerfile` to use `backend.app.main:app`.  
**Acceptance criteria:** Dockerfile CMD uses `backend.app.main:app`.  
**Verification:** `grep "app.main" Dockerfile` returns a match.

### Task 3.3 — Commit and deploy to Render

**What:** Commit `render.yaml` + `Dockerfile`. Trigger Render "Clear build cache & deploy".

**Acceptance criteria:**
- Deploy completes without build errors
- `GET /health` → `200 {"status":"ok"}`
- `GET /health/deep` → `200`
- `GET /readyz` → `200`
- `POST /chat` with a general question returns a streamed SSE response
- `POST /chat` with a tracking number returns tracking data
- `GET /analytics/chat-overview` → `200`
- `GET /tracking/porlor/search` → `200`
- `GET /public-config` → `200`

**Rollback plan:** If any endpoint returns 5xx, revert `startCommand` back to `backend.main:app` and redeploy. Total rollback time < 3 minutes.  
**Verification:** Curl each endpoint against the live Render URL.

### Task 3.4 — Update README.md

**What:** Update any `backend.main:app` references in README to `backend.app.main:app`.  
**Acceptance criteria:** No stale entrypoint references remain in docs.

---

## ⛳ Checkpoint C

Render is live on `backend.app.main`. Old compatibility bridge (`backend/main.py`) is now passive.

---

## Phase 4 — Phase 2 Roadmap (Future, Not Blocking)

From PRD §11.2. Not scheduled — listed for prioritization only.

| Item | Effort | Value |
|------|--------|-------|
| Analytics logging (question + score → Supabase) | Medium | Enables deflection rate KPI |
| Human escalation (email collect when score < 0.65) | Medium | Reduces lost queries |
| Markdown rendering in chat frontend | Small | Better UX for formatted answers |
| Quick Reply chips (3 suggested questions after answer) | Medium | Engagement |
| Admin dashboard (sync status, top queries, unanswered) | Large | Ops visibility |

---

## Risk Register

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| GAS deploy breaks live booking | Low | `clasp push` is atomic; prior version restorable via GAS version history |
| Render entrypoint switch causes 500 on live | Medium | Checkpoint B (tests) required before switching; rollback plan in Task 3.3 |
| CORS mismatch after entrypoint switch | Low | `FRONTEND_URL` env var unchanged; covered by test_app_main |
| Supabase RLS blocking queries after switch | Low | Repository layer unchanged; RLS already live before this change |
