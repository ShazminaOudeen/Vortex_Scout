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

**Prereqs:** Python 3.12 (the pinned versions in `requirements.txt` target it), Node 20+, Git.

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

**Load demo data** (optional; the in-memory store already ships the 200-SKU catalog):
```bash
# with SUPABASE_URL / SUPABASE_KEY set: wipes the demo tables, loads 14 days of history (~20k rows)
python -m app.generator.seed --phantom s1 --scenario frozen
# or: write a CSV and push it into a running API
python -m app.generator.generate_mock_pos --days 14 --phantom s1 --out mock_pos.csv
python -m app.generator.load_csv mock_pos.csv --api http://localhost:8000
```
Phantom scenarios: `frozen`, `damaged`, `backroom_stuck` (see `app/generator/generate_mock_pos.py`).

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
| POST | `/api/v1/pos/stream` | Batch-ingest POS rows → `{ingested, rejected, errors[]}` (422 if every row is rejected) |
| POST | `/api/v1/pos/stream/csv` | Same, body is raw CSV (`Content-Type: text/csv`) |
| GET | `/api/v1/anomalies` | Flagged SKUs |
| GET | `/api/v1/anomalies/metrics` | Dashboard KPIs |
| POST | `/api/v1/anomalies/run` | Run detection |
| GET | `/api/v1/agent/checklist` | Gemini-built aisle-grouped checklist |
| POST | `/api/v1/audit/reconcile` | Staff action: restocked / damaged / false_alarm. Idempotent; `damaged` writes `units` off the ledger |
| GET | `/api/v1/audit/stats` | Action counts + `false_alarm_rate` (threshold calibration) |
| POST | `/api/v1/simulate/{phantom\|normal\|reset}` | Judge demo hooks (`?variant=frozen\|damaged\|backroom_stuck` for phantom) |

### Feature store (for the ML engine)
`app.ml.feature_pipeline.get_velocity(sku_id=None, since=None, until=None)` returns a dense frame with columns
`sku_id, hour, units, hour_of_day, day_of_week, is_peak` — one row per SKU per trading hour, explicit zeros
included (a silent SKU shows a trailing run of zeros). `hours_since_last_sale()` gives the per-SKU gap.
All timestamps are store-clock (Asia/Colombo, UTC+5:30) wall times; tz-aware input is converted on ingest.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the git workflow.
