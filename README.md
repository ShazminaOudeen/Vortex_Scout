# Scout: Phantom Inventory Detection

![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688)
![Next.js](https://img.shields.io/badge/Next.js-14-000000)
![TypeScript](https://img.shields.io/badge/TypeScript-frontend-3178C6)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4)
![Track](https://img.shields.io/badge/Track-Undergraduate-informational)
![Domain](https://img.shields.io/badge/Domain-Retail%20%26%20Supply%20Chain%20AI-informational)

**Team Vortex | IntelliCon '26 Buildathon**

Autonomous shelf-void detection and micro-audit intelligence for modern retail.

**Topics:** `retail` `supply-chain` `phantom-inventory` `inventory-accuracy` `anomaly-detection` `time-series` `pos-data` `fastapi` `nextjs` `supabase` `gemini` `pwa` `intellicon-2026`

---

## Description

Supermarket systems track what should be on the shelf, not what is there. When damaged goods are discarded without a POS update, customers leave items in the wrong aisle, or backroom stock never reaches the shelf, the ledger keeps showing stock for a product whose shelf is empty. This is phantom inventory. Automatic replenishment never triggers because the system believes the stock exists, and staff lose minutes searching for items that are not there.

Scout is a zero-hardware intelligence layer that finds these cases using only the point-of-sale data a store already has. It learns how each product normally sells, flags products whose sales have stopped while the ledger still shows stock, and turns the result into a short morning audit checklist for floor supervisors. Staff verify each flagged shelf and reconcile it with a single tap: restocked, damaged, or false alarm.

**Target users:** store floor supervisors and category replenishment leads at multi-outlet supermarket chains in Sri Lanka. Secondary beneficiaries are operations managers who need store-level visibility into stock discrepancies.

## Table of Contents

1. [How It Works](#how-it-works)
2. [Current Status: What Is Real and What Is Mocked](#current-status-what-is-real-and-what-is-mocked)
3. [AI Components](#ai-components)
4. [Tech Stack](#tech-stack)
5. [Repository Structure](#repository-structure)
6. [Installation and Setup](#installation-and-setup)
7. [Running the Demo](#running-the-demo)
8. [API Reference](#api-reference)
9. [Testing](#testing)
10. [Preliminary Evaluation](#preliminary-evaluation)
11. [Known Limitations](#known-limitations)
12. [Roadmap](#roadmap)
13. [Team](#team)
14. [Third-Party Components and Credits](#third-party-components-and-credits)

---

## How It Works

```
POS transactions
      |
      v
Ingestion (POST /pos/stream) --> Supabase PostgreSQL (skus, pos_transactions, hourly_velocity,
      |                                                 stockout_anomalies, audit_log)
      v
Feature store: dense hourly sales per SKU, hours since last sale
      |
      v
Detection engine: expected vs actual sales during the current silence
      |
      v
POST /anomalies/run: flag if p_void >= 0.75 AND ledger stock > 0
      |
      v
Floor-action agent: group alerts by aisle, Gemini writes the briefing
      |
      v
/floor mobile checklist --> staff tap --> POST /audit/reconcile --> audit_log
```

### Detection method

For each SKU, Scout looks at the trailing run of consecutive zero-sale trading hours and asks how many sales it would normally have expected during that silence. Expected sales come from a store-wide trading rhythm (lunch and evening peaks, busier weekends) combined with the SKU's own sales speed, both learned only from the hours before the silence began.

The silence is scored with a likelihood-ratio test, which is converted to a probability of a shelf void (`p_void`) using a small prior. A fast-selling product that goes quiet for a few hours scores close to 1. A slow-selling product can be quiet for a whole day without being flagged, because that is normal for it. This is the reason a fixed rule such as "no sales for three hours" is not used: in the simulated catalogue the median product sells about 0.2 lines per open hour, and such a rule would generate constant false alarms.

A product is raised as an alert only if `p_void` is at least `VOID_THRESHOLD` (default 0.75) and the ledger stock is greater than zero. If the ledger already shows zero, the system already knows the product is out and it is not a phantom.

Each run of detection keeps the open alerts in step with the current evidence: still-flagged SKUs keep their alert with refreshed numbers, newly flagged SKUs get a new alert, and open alerts that are no longer supported are removed. Alerts that staff have already resolved are never modified.

---

## Current Status: What Is Real and What Is Mocked

| Component | Status | Notes |
|---|---|---|
| POS ingestion (JSON and CSV) | Functional | Row-by-row validation, unknown SKU or store rejected, chunked inserts, hourly velocity refreshed. |
| Synthetic data generator | Functional | 200 SKUs, peak hours, weekend and payday effects, three phantom scenarios. All sales data in this project is synthetic. |
| Feature store | Functional | Dense hourly sales per SKU with explicit zeros; hours since last sale. |
| Baseline shelf-void detector | Functional | Statistical likelihood-ratio model described above. |
| Detection endpoint | Functional | `POST /api/v1/anomalies/run`. |
| Gemini briefing | Functional with fallback | Depends on Gemini availability. Retries on temporary errors, caches for five minutes, falls back to a fixed template sentence. |
| Floor checklist page (`/floor`) | Functional | Shows real alerts grouped by aisle with one-tap actions. No login and no staff name capture. Does not auto-refresh. |
| Audit reconcile | Functional | Restocked, damaged, false alarm. Idempotent. A damaged action writes units off the ledger (simulated ERP adjustment). |
| Simulation hub (`/simulate`) | Functional | Injects phantom stockouts and normal trading, runs detection. |
| Zero-Inflated Poisson model | Not implemented | Placeholder module only. |
| Isolation Forest model | Not implemented | Placeholder module only. |
| Manager dashboard KPIs (`/dashboard`) | Mocked | Revenue recovered, audit completion rate, inventory record inaccuracy and the category breakdown are hardcoded values. The alert table on the page is real. |
| Dashboard velocity chart | Mocked | A decorative curve, not real sales data. |
| SKU explorer (`/inventory`) | Partial | Searches the flagged alerts only, not the full 200-SKU catalogue. |
| Progressive Web App | Partial | Manifest and icons only. No service worker and no offline support. |
| Authentication and roles | Not implemented | The backend holds the database key; the frontend never sees it. |
| Real POS integration | Not implemented | No real store data has been used. |
| Deployment | Not deployed | Runs locally. |

The frontend falls back to built-in sample data if the backend is unreachable. The sample alerts that ship in a freshly seeded database are placeholders and are replaced the first time detection runs.

---

## AI Components

- **Detection model.** A statistical model implemented with NumPy and pandas. It is not a pre-trained model and has no external API cost. scikit-learn and statsmodels are installed for the planned Zero-Inflated Poisson and Isolation Forest models but are not used by the detector today.
- **Gemini (Google Gen AI SDK).** Used for one narrow task: writing a one or two sentence morning briefing from the list of flagged items. Grouping, ordering and the alert rule are deterministic code, and Gemini output never affects which items are flagged. The model name is configurable through `GEMINI_MODEL` (default `gemini-3.8-flash`). During development the free tier is used; cost per briefing has not been measured. One call is made per distinct set of alerts and cached for five minutes.
- **AI-assisted development.** Parts of the codebase, tests and documentation were written with AI coding assistance (Claude by Anthropic). Details of tools, verification and examples are in the AI Usage Report submitted with the final submission.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn, Pydantic |
| Data processing | pandas, NumPy |
| Modelling | Statistical baseline (current); scikit-learn and statsmodels (planned models) |
| Database | PostgreSQL on Supabase (in-memory store when no keys are set) |
| LLM | Google Gemini via the `google-genai` SDK |
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, SWR, Recharts |
| Testing | pytest, a fake Supabase client for offline tests |
| Tools | Git and GitHub, VS Code |

---

## Repository Structure

```
backend/
  main.py                    FastAPI application entry point
  app/
    api/v1/                  pos, anomalies, agent, audit, simulate routers
    core/                    config, database client, data-access layer (store.py), time helpers
    ml/                      feature_pipeline.py, baseline.py (detector), zip_model.py and isolation_forest.py (planned)
    services/                ingest.py, detection.py
    agent/                   gemini_client.py, prompts.py
    generator/               synthetic POS generator, 200-SKU catalogue, seed and CSV loader
    models/                  Pydantic schemas
  tests/                     pytest suite (runs without network access or API keys)
frontend/
  src/app/                   pages: /, /floor, /dashboard, /inventory, /simulate
  src/components/            floor, dashboard and shared UI components
  src/hooks/, src/lib/       data hooks, API client, shared types
supabase/schema.sql          database schema
```

---

## Installation and Setup

### Prerequisites

- Python 3.12 (the pinned versions in `requirements.txt` target it)
- Node.js 20 or later
- Git

### 1. Clone the repository

```
git clone https://github.com/ShazminaOudeen/Vortex_Scout.git
cd Vortex_Scout
```

### 2. Backend

```
cd backend
python -m venv venv
source venv/bin/activate          # Windows Git Bash: source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env              # Windows Command Prompt: copy .env.example .env
uvicorn main:app --reload --port 8000
```

The API runs on http://localhost:8000 and interactive documentation is at http://localhost:8000/docs.

### 3. Frontend

```
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The app runs on http://localhost:3000.

### 4. Optional: connect Supabase and Gemini

The application runs with no keys. In that mode the backend uses an in-memory store and the briefing falls back to a fixed template sentence. To use a real database and Gemini, edit `backend/.env`:

| Variable | Purpose | Default |
|---|---|---|
| `SUPABASE_URL` | Supabase project URL | empty (in-memory store) |
| `SUPABASE_KEY` | Supabase **service_role** (secret) key. Keep it server-side and never commit it. | empty |
| `GEMINI_API_KEY` | Key from Google AI Studio | empty (template briefing) |
| `GEMINI_MODEL` | Gemini model name. Google retires models frequently; update this if you see a 404. | `gemini-3.8-flash` |
| `VOID_THRESHOLD` | Minimum `p_void` to raise an alert | `0.75` |
| `DEFAULT_STORE_ID` | Store used for generated alerts | `store_01` |
| `INGEST_CHUNK_SIZE` | Rows per database insert | `500` |

Supabase setup:

1. Create a free project at https://supabase.com.
2. Open the SQL Editor, paste the contents of `supabase/schema.sql`, and run it. This creates six tables: `stores`, `skus`, `pos_transactions`, `hourly_velocity`, `stockout_anomalies` and `audit_log`.
3. Copy the project URL and the secret key into `backend/.env`.
4. Load the demo data (14 days, about 20,000 sales rows):

```
cd backend
python -m app.generator.seed --yes
```

Warning: the seed command and `POST /api/v1/simulate/reset` delete rows in the demo tables of the connected database. Do not point them at data you want to keep.

Other data options:

```
# generate a CSV and push it into a running API
python -m app.generator.generate_mock_pos --days 14 --phantom s1 --out mock_pos.csv
python -m app.generator.load_csv mock_pos.csv --api http://localhost:8000
```

Phantom scenarios: `frozen` (sales stop abruptly), `damaged` (stock spoiled or pulled, ledger needs a write-off) and `backroom_stuck` (sales taper off as the shelf drains).

---

## Running the Demo

1. Start the backend and the frontend.
2. Open `/simulate` and click **Simulate Normal Peak** so every product, including the demo product, is selling.
3. Click **Inject Phantom Stockout**. Munchee Super Cream Cracker 490g stops selling for eight trading hours while the ledger still shows 40 units.
4. Click **Run Scout Detection & Trigger Agent**. The log lists the flagged product, its `p_void` and the evidence.
5. Open `/floor` and reload. The product appears in its aisle with the briefing at the top.
6. Tap **Restocked**. The alert closes and an audit record is written.

Do not use **Reset Store State** against a database that holds data you want to keep.

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

| Method | Path | Purpose |
|---|---|---|
| POST | `/pos/stream` | Batch-ingest POS rows. Returns `{ingested, rejected, errors[]}`; 422 if every row is rejected. |
| POST | `/pos/stream/csv` | Same, with a raw CSV body (`Content-Type: text/csv`). |
| GET | `/anomalies` | All alerts. |
| GET | `/anomalies/metrics` | Dashboard KPIs (currently mocked values). |
| POST | `/anomalies/run` | Run detection. Returns `flagged`, `created`, `updated`, `cleared`, `threshold`, `data_as_of` and the list of `alerts`. |
| GET | `/agent/checklist` | Aisle-grouped checklist with the Gemini briefing. |
| POST | `/audit/reconcile` | Staff action: `restocked`, `damaged` or `false_alarm`. Idempotent; `damaged` writes units off the ledger. |
| GET | `/audit/stats` | Action counts and the false-alarm rate. |
| POST | `/simulate/{phantom\|normal\|reset}` | Demo hooks. `?variant=frozen\|damaged\|backroom_stuck` selects the phantom type. |

The backend schemas in `backend/app/models/` and the frontend types in `frontend/src/lib/types.ts` must be kept in sync.

### Feature store

`app.ml.feature_pipeline.get_velocity()` returns one row per SKU per trading hour (08:00 to 22:00) with explicit zeros, so a silent SKU shows a trailing run of zeros. `hours_since_last_sale()` returns the per-SKU gap in wall-clock hours, including closed hours. All timestamps are store-clock times (Asia/Colombo, UTC+5:30).

---

## Testing

```
cd backend
pytest
```

The suite contains 158 tests and runs without network access or API keys. Tests never reach a real Supabase project or the real Gemini API, even if `backend/.env` contains keys. Data-layer and endpoint tests run twice, once against the in-memory store and once through the Supabase code paths using a fake client. A green run on the fake client is not a substitute for a smoke test against a real project.

Frontend checks:

```
cd frontend
npm run lint
npm run build
```

---

## Preliminary Evaluation

The figures below come from the bundled generator (14 days of simulated trading, one random seed per run) and are indicative only. They do not describe performance on a real store. The evaluation script is not yet part of the repository.

- **False alarms:** about 2 flagged SKU-checks in 19,600 on clean simulated data (7 days of hourly checks across 200 SKUs).
- **Detection of fast sellers:** the 25 fastest SKUs (12 percent of the catalogue, 45 percent of simulated sale lines) were flagged after roughly 3 to 9 silent trading hours.
- **Blind spot:** products selling below about 0.3 lines per open hour cannot be distinguished from normal quiet periods using sales data alone.

A formal precision, recall and false-positive-rate evaluation across quiet days, peak weekends and all three phantom scenarios is planned.

---

## Known Limitations

- Detection reads sales data only. It works for fast-moving products and cannot catch slow movers.
- After a supervisor taps Restocked, running detection again on unchanged sales data flags the product again, because nothing in the data shows the shelf was refilled. In the demo, use Simulate Normal Peak before re-running.
- `hours_since_last_sale` is measured in wall-clock hours and includes overnight time.
- The system assumes a single store and has no authentication.
- The dashboard KPIs and chart, and the SKU explorer, are incomplete as described in the status table.
- Free-tier Gemini is occasionally overloaded. The checklist page can wait several seconds for the retry logic before falling back to the template sentence.

---

## Roadmap

- Zero-Inflated Poisson model and Isolation Forest, compared against the baseline.
- Real dashboard KPIs and an expected-versus-actual sales chart per product.
- Full SKU explorer and per-product detail view.
- Formal evaluation (precision, recall, false-positive rate) and committed evaluation script.
- Suppress repeat alerts after a staff fix until sales resume.
- Staff name capture, service worker and offline support, deployment.

---

## Team

| Member | Role |
|---|---|
| G. Shazmina Oudeen | Team Lead |
| Aathika Asmeer | Member |
| Nethmi Weerathunga | Member |
| Noorul Shabeeha | Member |

**Event:** IntelliCon '26 Buildathon (AIESEC in SLIIT)
**Bracket:** Undergraduate
**Domain:** Retail and Supply Chain AI

Git workflow and contribution rules are in [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Third-Party Components and Credits

Backend: FastAPI, Uvicorn, Pydantic, pydantic-settings, python-dotenv, pandas, NumPy, scikit-learn, statsmodels, supabase-py, google-genai, httpx, pytest.

Frontend: Next.js, React, TypeScript, Tailwind CSS, SWR, Recharts, lucide-react, clsx, tailwind-merge.

Services: Supabase (PostgreSQL), Google Gemini API.

Data: all sales data is synthetic and produced by the generator in `backend/app/generator/`. No personal data is processed by this repository. The Gate 1 survey responses are anonymised and are held outside the repository.
