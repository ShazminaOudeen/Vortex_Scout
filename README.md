# SCOUT — Team Vortex (Intellicon '26 Buildathon)

Autonomous shelf-void detection & micro-audit intelligence for modern retail.
Zero-hardware: reads POS data, detects phantom inventory with ZIP + Isolation Forest,
and turns it into a 3-minute morning audit checklist via a Gemini agent.

```
POS stream → [1 Ingestion/Feature store] → [2 ML anomaly engine] → [3 Gemini floor agent] → [4 Next.js PWA + dashboard]
```

## Repo layout

```
backend/    FastAPI + ML engine + Gemini agent + synthetic data generator
frontend/   Next.js 14 (App Router) + Tailwind — /floor, /dashboard, /inventory, /simulate
supabase/   schema.sql  (run once in the Supabase SQL editor)
docs/       Scout_DevGuide, Gate 1 submission
```

## Quickstart

**Prereqs:** Python 3.11+, Node 20+, Git.

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
uvicorn main:app --reload --port 8000
pytest                            # should be green
```
API docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local        # Windows: copy .env.example .env.local
npm run dev
```
App: http://localhost:3000

The app runs **out of the box with no keys**: the backend uses an in-memory demo store and a
template briefing if `GEMINI_API_KEY` is empty; the frontend falls back to mock data if the API is down.

### Keys you'll need (put in `backend/.env`, never commit)
- **Supabase:** create a free project → SQL editor → run `supabase/schema.sql` → copy URL + service key.
- **Gemini:** free key from https://aistudio.google.com/apikey. The guide says Gemini 1.5 Flash, but Google
  has retired it — we default to `gemini-2.5-flash` (set `GEMINI_MODEL` to change).

## Who owns what

| Task | Owner | Start here |
|------|-------|-----------|
| 1 — Data & API | _name_ | `backend/app/api/v1/pos.py`, `audit.py`, `app/core/store.py` → Supabase, `app/generator/` |
| 2 — ML & Agent | _name_ | `backend/app/ml/*.py`, `backend/app/agent/gemini_client.py` |
| 3 — Frontend | _name_ | `frontend/src/app/*`, `frontend/src/components/*` |
| 4 — Integration & Demo | _name_ | `backend/tests/`, `/simulate`, slides/script |

Search the code for `TODO(Task N)` to find your work items.

## API contract (frontend ↔ backend)
Keep `backend/app/models/*.py` and `frontend/src/lib/types.ts` in sync. Change both in the same PR.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/pos/stream` | Batch-ingest POS rows |
| GET | `/api/v1/anomalies` | Flagged SKUs |
| GET | `/api/v1/anomalies/metrics` | Dashboard KPIs |
| POST | `/api/v1/anomalies/run` | Run detection |
| GET | `/api/v1/agent/checklist` | Gemini-built aisle-grouped checklist |
| POST | `/api/v1/audit/reconcile` | Staff action: restocked / damaged / false_alarm |
| POST | `/api/v1/simulate/{phantom\|normal\|reset}` | Judge demo hooks |

See [CONTRIBUTING.md](CONTRIBUTING.md) for the git workflow.
