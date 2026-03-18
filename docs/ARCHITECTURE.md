# SiS Freight Recommended Architecture

## Goal
Use a hybrid chatbot architecture that keeps operational flows deterministic while allowing natural long-form conversations for service questions.

## Recommended Production Shape
- `tracking lane`
  - Purpose: DO / tracking-number lookups
  - Data source: Google Sheets tracking data
  - Behavior: direct response, no LLM required for the answer body
- `rule-based lane`
  - Purpose: greeting, thanks, human handoff, simple operational prompts
  - Data source: code-based intent rules
  - Behavior: fixed lightweight responses
- `hybrid retrieval lane`
  - Purpose: booking, pricing, claims, service explanations
  - Data source: Supabase pgvector + Gemini
  - Behavior: route by intent, retrieve knowledge, then answer naturally
- `long-form consult lane`
  - Purpose: longer customer scenarios or consultative questions
  - Data source: Supabase pgvector + Gemini
  - Behavior: retrieve more context and answer in a structured, conversational way

## Runtime Flow
1. Frontend sends `{ message, history[] }` to `POST /chat`
2. Backend validates and sanitizes input
3. Intent router classifies the message into a lane
4. Backend handles the request by lane:
   - `tracking`: direct Google Sheets lookup
   - `rule`: canned response
   - `hybrid` or `long-form`: retrieve from Supabase and answer with Gemini
5. Response streams back via SSE

## Why This Fits This Project
- Tracking remains reliable and auditable
- FAQ and operational questions can still be tightly controlled
- Solar/consult/general questions can become more natural over time
- Knowledge updates stay editable in Google Sheets and searchable via Supabase

## Data Responsibilities
- `Google Sheets tracking`
  - operational DO / carrier lookup
- `Google Sheets knowledge sheets`
  - FAQ, Solar Hub, booking, pricing, claims, policies
- `Supabase knowledge_base`
  - vectorized long-form knowledge store for retrieval

## Backend Modules
- [main.py](/C:/Users/Sorravit_L/Frieght/backend/main.py)
  - API entrypoint, SSE, lane orchestration
- [intent_router.py](/C:/Users/Sorravit_L/Frieght/backend/intent_router.py)
  - intent classification and lane metadata
- [tracking.py](/C:/Users/Sorravit_L/Frieght/backend/tracking.py)
  - deterministic tracking lookup and carrier-specific links
- [vector_search.py](/C:/Users/Sorravit_L/Frieght/backend/vector_search.py)
  - Supabase pgvector retrieval
- [sync_vectors.py](/C:/Users/Sorravit_L/Frieght/backend/sync_vectors.py)
  - Google Sheets to Supabase sync

## Knowledge Sheet Recommendation
- `solar`
  - service overview, use cases, pricing logic, restrictions
- `booking`
  - booking steps, required data, SLA, contact path
- `pricing`
  - quote rules, pricing factors, when manual pricing is needed
- `claims`
  - damaged goods, escalation, evidence requirements
- `general`
  - company services, coverage, operating constraints
- `coverage`
  - provinces, area constraints, destination eligibility
- `documents`
  - invoice, packing list, POD, required paperwork
- `timeline`
  - pickup windows, cut-off times, SLA expectations

## Intent Map Recommendation
- `solar`
  - phrases about solar panels, hub, inverter, solar jobs
- `booking`
  - booking, pickup, fleet size, truck type, same-day arrangements
- `pricing`
  - quote, rate, service charge, minimum charge, how pricing is calculated
- `claim`
  - damaged goods, lost goods, complaints, delays, wrong delivery
- `coverage`
  - service area, provinces, destination checks
- `documents`
  - invoice, packing list, POD, document requirements
- `timeline`
  - lead time, transit time, cut-off, pickup schedule
- `general_chat`
  - non-operational or broad questions

## Near-Term Implementation Plan
1. Keep tracking on the direct lane
2. Expand intent keywords gradually based on real chat logs
3. Organize knowledge sheets by topic
4. Improve long-form prompts per intent
5. Add topic-aware analytics later if needed

## Next Operational Step
- Fill the sheet tabs based on [KNOWLEDGE_SHEETS_TEMPLATE.md](/C:/Users/Sorravit_L/Frieght/docs/KNOWLEDGE_SHEETS_TEMPLATE.md)
- Re-run vector sync after each meaningful batch of content updates
