# Task List — SiS Freight

See `tasks/plan.md` for full acceptance criteria and dependency graph.

---

## Phase 1 — Gas Booking: Commit & Deploy

- [ ] **1.1** Commit gas-booking changes (doget.js, functionlist.html, index.html, script.html, style.html, deploy.sh)
- [ ] **1.2** Deploy to Google Apps Script (`clasp push` or `./gas-booking/deploy.sh`) and smoke-test in browser

## ⛳ Checkpoint A — gas-booking committed and deployed

---

## Phase 2 — Backend: Parity Verification

- [ ] **2.1** Run parity tests: `pytest backend/tests/test_api_smoke.py test_app_main.py test_main_compat.py test_root_wrappers.py -v`
- [ ] **2.2** Run full test suite: `pytest backend/tests/ -v --tb=short` — confirm no new failures

## ⛳ Checkpoint B — all tests green

---

## Phase 3 — Backend: Entrypoint Switch

- [ ] **3.1** Update `render.yaml` startCommand → `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- [ ] **3.2** Update `Dockerfile` CMD → `backend.app.main:app`
- [ ] **3.3** Commit render.yaml + Dockerfile; trigger Render "Clear build cache & deploy"; verify all 8 endpoints
- [ ] **3.4** Update README.md — replace any `backend.main:app` references

## ⛳ Checkpoint C — Render live on backend.app.main

---

## Phase 4 — Roadmap (unscheduled)

- [ ] Analytics logging (question + score → Supabase table)
- [ ] Human escalation flow (collect email when score < 0.65)
- [ ] Markdown rendering in chat frontend
- [ ] Quick Reply chips after each answer
- [ ] Admin dashboard (sync status, top queries, unanswered)
