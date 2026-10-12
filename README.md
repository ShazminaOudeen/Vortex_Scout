# Scout: Autonomous Phantom Inventory Detection

[![Live Web App](https://img.shields.io/badge/Vercel-Live%20Frontend-000000?style=for-the-badge&logo=vercel)](https://vortex-scout.vercel.app/)
[![Live API](https://img.shields.io/badge/Railway-Live%20Backend-0B0D0E?style=for-the-badge&logo=railway)](https://vortexscout-production.up.railway.app)
[![Swagger Docs](https://img.shields.io/badge/FastAPI-Swagger%20UI-009688?style=for-the-badge&logo=fastapi)](https://vortexscout-production.up.railway.app/docs)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![Next.js](https://img.shields.io/badge/Next.js-14-000000)
![TypeScript](https://img.shields.io/badge/TypeScript-frontend-3178C6)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E)
![Gemini](https://img.shields.io/badge/Google-Gemini%203.8%20Flash-4285F4)

**Team Vortex | IntelliCon '26 Buildathon**  
*Track:* Undergraduate · *Domain:* Retail & Supply Chain AI

Autonomous shelf-void detection, zero-hardware retail intelligence, and GenAI micro-audit routing for modern retail chains.

---

## 🌐 Live Deployments

The complete Scout platform is deployed and publicly accessible:

| Service | Platform | URL | Purpose |
|---|---|---|---|
| **Frontend Web App & Mobile PWA** | Vercel | [https://vortex-scout.vercel.app/](https://vortex-scout.vercel.app/) | Store Manager Dashboard, Floor Associate Mobile Walk, SKU Explorer, Simulation Hub & Evaluation Portal |
| **Backend REST API** | Railway | [https://vortexscout-production.up.railway.app](https://vortexscout-production.up.railway.app) | FastAPI streaming endpoints, feature store, ML detection engine & audit flow |
| **Interactive API Documentation** | Swagger / OpenAPI | [https://vortexscout-production.up.railway.app/docs](https://vortexscout-production.up.railway.app/docs) | Live endpoint testing, schema definitions, and interactive calls |

---

## Table of Contents

1. [Description](#description)
2. [How It Works](#how-it-works)
3. [Current Status: Fully Functional vs. Mocked (Transparency Statement)](#current-status-fully-functional-vs-mocked)
4. [AI Components Used](#ai-components-used)
5. [Tech Stack](#tech-stack)
6. [Key Features by Application Route](#key-features-by-application-route)
7. [Repository Structure](#repository-structure)
8. [Installation & Local Setup (Optional)](#installation--local-setup-optional)
9. [Interactive Judge Demo Walkthrough](#interactive-judge-demo-walkthrough)
10. [API Reference](#api-reference)
11. [Testing & Quality Assurance](#testing--quality-assurance)
12. [Empirical Evaluation](#empirical-evaluation)
13. [Team & Credits](#team--credits)

---

## Description

Supermarket systems track what should be on the shelf, not what is there. When damaged goods are discarded without a POS update, customers leave items in the wrong aisle, or backroom stock never reaches the shelf, the ledger keeps showing stock for a product whose shelf is empty. This is phantom inventory. Automatic replenishment never triggers because the system believes the stock exists, and staff lose minutes searching for items that are not there.

Scout is a zero-hardware intelligence layer that finds these cases using only the point-of-sale data a store already has. It learns how each product normally sells, flags products whose sales have stopped while the ledger still shows stock, and turns the result into a short morning audit checklist for floor supervisors. Staff verify each flagged shelf and reconcile it with a single tap: restocked, damaged, or false alarm.

**Target users:** store floor supervisors and category replenishment leads at multi-outlet supermarket chains in Sri Lanka. Secondary beneficiaries are operations managers who need store-level visibility into stock discrepancies.

---

## How It Works

```
        [ POS Transaction Stream / CSV Feed ]
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ Ingestion Layer (POST /api/v1/pos/stream)              │
│ • Validates rows, handles chunked bulk inserts         │
│ • Database: Supabase PostgreSQL (or in-memory store)   │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ Feature Store Pipeline (dense hourly velocity)         │
│ • Explicit zero-filling across open trading hours      │
│ • Computes hours_since_last_sale & rolling rates       │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ ML Anomaly Detection Engine (POST /anomalies/run)      │
│ • Likelihood-Ratio Baseline + ZIP count model          │
│ • Isolation Forest multi-dimensional outlier scoring   │
│ • Flags void if P_void >= 0.75 AND ledger_stock > 0    │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ GenAI Floor Action Agent (GET /agent/checklist)        │
│ • Aisle & Bay clustering (shortest walking route)      │
│ • Gemini 3.8 Flash natural-language morning briefing   │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│ Floor Associate Mobile PWA (/floor)                    │
│ • One-tap actions: [Restocked] [Damaged] [False Alarm] │
│ • POST /audit/reconcile -> atomic ledger deduction     │
└────────────────────────────────────────────────────────┘
```

---

## Current Status: Fully Functional vs. Mocked

The following tables delineate the functional scope of Scout:

### What Is Fully Functional & Built

| Component / Feature | Implementation Status | Implementation Details |
|---|:---:|---|
| **POS Stream Ingestion** | ✅ Fully Functional | `POST /api/v1/pos/stream` and `/stream/csv`. Row-by-row validation, invalid SKU/store rejection with error log, chunked inserts, automatic velocity refreshes. |
| **Statistical Baseline Detector** | ✅ Fully Functional | `backend/app/ml/baseline.py`. Likelihood-ratio statistical test on trailing zero-sale trading hours conditioned on store rhythms and SKU velocity. |
| **Zero-Inflated Poisson (ZIP) Model** | ✅ Fully Functional | `backend/app/ml/zip_model.py`. Decouples natural structural zeros (off-peak hours / slow movers) from sampling shelf voids (empty shelf during active demand). |
| **Isolation Forest Ensemble Scorer** | ✅ Fully Functional | `backend/app/ml/isolation_forest.py`. Scikit-learn multi-dimensional outlier detector (zero streak length, expected vs. actual ratio, replenishment age) blended into an ensemble void score. |
| **Threshold Calibration Engine** | ✅ Fully Functional | `backend/app/api/v1/audit.py` & `test_threshold_calibration.py`. Calibrates `VOID_THRESHOLD` based on historical staff false alarm feedback to minimize alert fatigue. |
| **Multi-Scenario Void Classification** | ✅ Fully Functional | `backend/app/ml/void_classifier.py`. Distinguishes between abrupt freeze (`frozen`), taper (`backroom_stuck`), and damage (`damaged`). |
| **GenAI Floor Action Agent** | ✅ Fully Functional | `backend/app/agent/gemini_client.py`. Live integration with Google Gemini 3.8 Flash (`gemini-3.8-flash`), physical aisle/bay sequence clustering, revenue-at-risk ranking, 5-min caching, and fallback template. |
| **"Why Flagged?" Root Cause Explainer** | ✅ Fully Functional | `backend/app/agent/explainer.py`. Produces plain-English explanations per SKU for staff and judges. |
| **Floor Associate Mobile PWA (`/floor`)** | ✅ Fully Functional | Real alert checklist, aisle grouping, single-tap resolutions (`Restocked`, `Damaged`, `False Alarm`), audio chime, haptic vibration, celebratory confetti, staff name capture, undo support, and PWA manifest. |
| **Audit Reconciliation & Ledger Sync** | ✅ Fully Functional | `POST /api/v1/audit/reconcile`. Idempotent operations. When `damaged` is reported, units are atomically deducted from `skus.ledger_stock` (clamped at 0), writing a permanent audit trail. |
| **Store Manager Analytics (`/dashboard`)** | ✅ Fully Functional | `backend/app/services/analytics.py`. Computes live KPIs from real database rows: active voids, audit completion %, LKR revenue recovered from restocked items, IRI rate, and department breakdown. |
| **Sales Velocity Time-Series Chart** | ✅ Fully Functional | `GET /api/v1/skus/{id}/velocity`. Recharts dual-line time-series graph contrasting expected hourly velocity against actual sales drop to zero. |
| **200-SKU Inventory Explorer (`/inventory`)** | ✅ Fully Functional | `GET /api/v1/skus`. Full 200-item grocery catalog with search, filter tabs (`All Items`, `Critical Voids P_void >= 0.75`, `Reconciled Today`), risk badges, and detail modal. |
| **Simulation Playground (`/simulate`)** | ✅ Fully Functional | 1-click preset anomaly injections, real-time scrolling POS terminal, and instant end-to-end pipeline trigger button. |
| **Evaluation Portal (`/evaluation`)** | ✅ Fully Functional | Interactive UI presenting benchmark metrics (Precision, Recall, F1, FPR) across 19,600 simulated checks, proving Scout's statistical advantage over heuristic rules. |
| **Cloud Deployment** | ✅ Fully Functional | Production deployment live on Railway (Backend) and Vercel (Frontend). |

### What Is Mocked / Simulated

| Component / Feature | Current Approach | Real-World Production Next Step |
|---|---|---|
| **POS Sales Stream** | **Synthetic Generation:** Sales transactions are generated by a realistic simulation script (`generate_mock_pos.py`) across 200 Sri Lankan grocery SKUs (peak hours 11–13 and 18–21 at 2x, weekends 1.2x, paydays 1.12x, 3 phantom scenarios). | Direct TCP/Kafka or webhook integration with physical supermarket POS cash register till systems (e.g., Toshiba, NCR, LS Retail). |
| **ERP Inventory Synchronization** | **Database-Level Adjustment:** Restocks and write-offs update Scout's database ledger directly to simulate inventory adjustments. | Direct bi-directional REST/SOAP connector to enterprise ERP systems (SAP S/4HANA Retail, Oracle Retail, Microsoft Dynamics 365). |
| **Store Tenancy & Authentication** | **Single Store Context:** Operates in a single demo store context (`store_01`). Floor associates enter their name locally without password prompts. | Multi-store tenancy with enterprise SSO (SAML/OAuth2) and role-based access control (RBAC). |
| **Offline PWA Sync** | **Online Manifest:** Manifest and icons support mobile home-screen installability, but background offline service worker caching is not implemented. | Service Worker background sync caching for audits conducted in dead-zone supermarket basements. |

---

## AI Components Used

1. **Applied Machine Learning & Statistical Anomaly Detection:**
   - **Likelihood-Ratio Statistical Baseline (`baseline.py`):** Models hourly expected sales $\lambda_{i,t}$ conditioned on day-of-week and time-of-day store traffic. Evaluates consecutive zero-sale trading hours via a likelihood-ratio test with a small prior, calculating void probability $P_{\text{void}} \in [0, 1]$.
   - **Zero-Inflated Poisson (ZIP) Engine (`zip_model.py`):** Separates natural structural zero non-purchase periods during slow trading hours from sampling zeros caused by shelf voids.
   - **Isolation Forest Ensemble Scorer (`isolation_forest.py`):** Unsupervised outlier scoring across multi-dimensional feature vectors (zero streak length, expected vs. actual ratio, replenishment age) blended into an ensemble void score.
2. **Generative AI Floor Action Agent (Gemini 3.8 Flash):**
   - Live reasoning via Google Gen AI SDK (`google-genai`) with model `gemini-3.8-flash`.
   - Synthesizes raw anomaly JSON arrays into a prioritized, human-friendly 2-sentence morning briefing for floor staff.
   - Organizes tasks by physical store geography (Aisle 01 $\rightarrow$ 02 $\rightarrow$ 05, then Bay sequence) to minimize staff walk time.
   - Generates plain-English root-cause explanations per item (via `explainer.py`).
   - Includes 5-minute memory caching and a deterministic fallback template for high availability.
3. **AI-Assisted Engineering:**
   - Code architecture, test suites (158 passing Pytest tests), and documentation were iteratively developed and reviewed with AI coding assistance (Anthropic Claude & Google DeepMind Antigravity).

---

## Tech Stack

| Layer | Technologies | Purpose |
|---|---|---|
| **Backend Framework** | Python 3.12, FastAPI, Uvicorn, Pydantic | Asynchronous REST API, high-throughput POS ingestion, and data modeling |
| **Data Processing** | Pandas, NumPy | Time-series resample, dense hourly sales aggregation, and rolling metrics |
| **Machine Learning** | Scikit-learn, Statsmodels, Scipy | Isolation Forest, Zero-Inflated Poisson modeling, and statistical inference |
| **Generative AI** | Google Gen AI SDK (`google-genai`), Gemini 3.8 Flash | Floor action agent reasoning, physical routing, and natural-language briefings |
| **Database** | PostgreSQL on Supabase / Thread-safe in-memory store | Relational schemas (`stores`, `skus`, `pos_transactions`, `hourly_velocity`, `stockout_anomalies`, `audit_log`) with zero-config in-memory fallback |
| **Frontend Framework** | Next.js 14 (App Router), React 18, TypeScript | Server and client rendered UI, desktop portal, and mobile PWA routes |
| **Styling & UI** | Tailwind CSS, Lucide React, Canvas Confetti | Operational dark/light aesthetic, high-contrast badges, micro-animations |
| **Data Visualization** | Recharts | Sales velocity time-series charts, department category breakdowns |
| **Testing** | Pytest, Fake Supabase client | 158 isolated unit, integration, and E2E regression tests |
| **Hosting & Cloud** | Railway (Backend Docker container), Vercel (Frontend) | Production cloud infrastructure with continuous deployment |

---

## Key Features by Application Route

Scout is organized into 5 purpose-built routes:

- **`/` (Landing & Route Switcher):** Split-card launchpad directing store managers, floor supervisors, and competition judges to their respective views.
- **`/dashboard` (Store Manager Executive Portal - Desktop):**
  - Live KPI Row: LKR Revenue Recovered, Active Phantom Voids, Audit Completion Rate (%), and Inventory Inaccuracy Rate reduction.
  - Sales Velocity Anomaly Chart (Recharts): Dual-line hourly curve illustrating expected velocity vs. sudden zero actual sales.
  - Category Risk Breakdown: Department vulnerability distribution (Chilled Dairy, Biscuits, Confectionery).
  - Live Reconciliations Feed: Real-time chronological audit trail of floor actions.
- **`/floor` (Floor Associate Morning Checklist - Mobile PWA):**
  - Handheld mobile viewport (max-w 420px) optimized for walking supermarket aisles.
  - Natural-language Gemini 3.8 Flash morning briefing card.
  - Aisle-clustered action cards sorted by shortest walking path.
  - Single-tap resolution loop: **[Restocked]**, **[Damaged Write-Off]**, **[False Alarm]**.
  - Audio chimes, haptic feedback, and celebratory confetti upon completing the shift checklist.
- **`/inventory` (Master SKU Explorer & Alert Log - Desktop/Tablet):**
  - Searchable, filterable table across all 200 catalog items.
  - Instant search across Sri Lankan grocery brands (*Munchee*, *Maliban*, *Anchor*, *Highland*).
  - Quick filter tabs: `All Items`, `Critical Voids (P_void >= 0.75)`, `Reconciled Today`.
  - Detailed product telemetry modal: 14-day history, velocity curve, and audit log.
- **`/simulate` (Judge Simulation & Demonstration Hub):**
  - Preset scenario injection buttons: *Inject Phantom Stockout*, *Simulate Normal Peak*, *Reset Store State*.
  - Live streaming code terminal displaying incoming synthetic transactions.
  - Single-click pipeline trigger: *Run Scout Anomaly Detection & Trigger Gemini Agent*.
- **`/evaluation` (Statistical Model Benchmarking Portal):**
  - Side-by-side benchmark metrics (Precision, Recall, F1-Score, False Positive Rate).
  - Proof of Scout's statistical formulation over naive heuristic rules.

---

## Repository Structure

```
backend/
  main.py                    FastAPI application entry point
  app/
    api/v1/                  pos, anomalies, agent, audit, skus, simulate, evaluation routers
    core/                    config.py, database.py, store.py (data layer), timeutil.py
    ml/                      feature_pipeline.py, baseline.py, zip_model.py, isolation_forest.py, evaluation.py
    services/                ingest.py, detection.py, analytics.py
    agent/                   gemini_client.py, prompts.py, explainer.py
    generator/               generate_mock_pos.py, mock_skus.json (200 SKUs), seed.py, load_csv.py
    models/                  Pydantic schemas (sku, transaction, anomaly, evaluation)
  tests/                     Pytest suite (158 passing unit, integration, and E2E tests)
frontend/
  src/app/                   pages: /, /dashboard, /floor, /inventory, /simulate, /evaluation
  src/components/            floor, dashboard, inventory, simulate, and shared UI components
  src/hooks/, src/lib/       data hooks, API client, TypeScript interfaces
supabase/
  schema.sql                 PostgreSQL schema (6 core tables and indexes)
team.md                      System modules, task breakdowns (A1–F8), and delivery matrix
```

---

## Installation & Local Setup (Optional)

> **Note:** Scout is already deployed live on [Vercel](https://vortex-scout.vercel.app/) and [Railway](https://vortexscout-production.up.railway.app). Local setup is only needed if you wish to run the code locally.

### Prerequisites
- Python 3.12+
- Node.js 20+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/ShazminaOudeen/Vortex_Scout.git
cd Vortex_Scout
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000` (Swagger UI at `http://localhost:8000/docs`).

*Optional: To connect a live Supabase PostgreSQL database or Google Gemini key, fill in `SUPABASE_URL`, `SUPABASE_KEY`, and `GEMINI_API_KEY` in `backend/.env`. If left blank, Scout runs automatically on its thread-safe in-memory store with deterministic template briefings.*

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend UI will be running at `http://localhost:3000`.

---

## Interactive Judge Demo Walkthrough

To experience the full end-to-end loop in under 3 minutes (either on the [Live Web App](https://vortex-scout.vercel.app/) or locally):

1. **Open the Simulation Hub (`/simulate`):**
   - Observe the live streaming code terminal showing synthetic POS transactions entering the system.
2. **Inject a Phantom Stockout:**
   - Click **[Inject Phantom Stockout (Munchee Biscuits)]**.
   - *What happens:* Munchee Super Cream Cracker 490g abruptly halts sales for 8 trading hours while the ledger still shows 40 units.
3. **Trigger Detection & AI Agent:**
   - Click **[Run Scout Anomaly Detection & Trigger Gemini Agent]**.
   - *What happens:* The statistical engine flags the SKU ($P_{\text{void}} = 0.94$), and Gemini 3.8 Flash synthesizes the morning aisle briefing.
4. **Inspect Floor Associate View (`/floor`):**
   - Open the `/floor` route. The product appears under *Aisle 03 — Biscuits & Confectionery* with the briefing at the top.
   - Tap **[Restocked from Backroom]**. Hear the audio chime, see haptic feedback, and observe the item resolve.
5. **Review Manager Analytics (`/dashboard`):**
   - Open `/dashboard`. View the dual-line Recharts graph showing expected vs. zero actual sales velocity, updated LKR revenue recovered, and verified audit logging.

---

## API Reference

Base URL: `https://vortexscout-production.up.railway.app/api/v1` (or `http://localhost:8000/api/v1` locally)

| Method | Path | Description |
|---|---|---|
| `POST` | `/pos/stream` | Batch ingest POS transaction rows with partial error handling |
| `POST` | `/pos/stream/csv` | Ingest raw CSV transaction stream |
| `GET` | `/pos/recent` | Retrieve recent transactions for the live streaming terminal |
| `GET` | `/anomalies` | List all detected anomaly alerts |
| `GET` | `/anomalies/metrics` | Dynamically calculated manager dashboard KPIs |
| `POST` | `/anomalies/run` | Execute detection pipeline and refresh open alerts |
| `GET` | `/skus` | Retrieve full 200-SKU catalog with anomaly risk status |
| `GET` | `/skus/{id}` | Detailed SKU metadata and historical audit history |
| `GET` | `/skus/{id}/velocity` | Expected vs. actual hourly sales velocity curve |
| `GET` | `/agent/checklist` | Aisle-grouped morning checklist with Gemini briefing |
| `POST` | `/audit/reconcile` | Submit associate action (`restocked`, `damaged`, `false_alarm`) |
| `GET` | `/audit/stats` | Audit counts and empirical false alarm rate |
| `POST` | `/simulate/{phantom\|normal\|reset}` | Demo scenario injection hooks |
| `GET` | `/evaluation/benchmark` | Statistical evaluation metrics across benchmark datasets |

---

## Testing & Quality Assurance

The backend includes a comprehensive test suite of **158 tests** verifying ingestion, data access fallbacks, baseline detection, ZIP modeling, Isolation Forest scoring, Gemini resilience, and end-to-end reconciliation:

```bash
cd backend
pytest -v
```

*(All tests execute in isolated offline environments without requiring live network access or external API keys.)*

Frontend validation:
```bash
cd frontend
npm run lint
npm run build
```

---

## Empirical Evaluation

Based on simulated benchmark runs across 200 SKUs over 14 days of trading (19,600 individual hourly SKU checks):

- **False Alarm Suppression:** Approximately 2 false alarms in 19,600 checks ($< 0.02\%$), compared to fixed threshold rules (e.g. "no sales for 3 hours") which generated over 420 false alarms due to natural quiet periods in slow-moving grocery SKUs.
- **Fast-Mover Detection:** Fast-selling items (top 25 SKUs) were flagged within 3 to 6 silent trading hours with $P_{\text{void}} > 0.85$.
- **Precision & Recall:** Across simulated phantom scenarios (`frozen`, `damaged`, `backroom_stuck`), Scout achieved $> 91\%$ Precision and $> 88\%$ Recall.

*(Full visual benchmarks and confusion matrices can be inspected directly on the `/evaluation` portal).*

---

## Team & Credits

| Member | Role |
|---|---|
| **G. Shazmina Oudeen** | Team Lead  |
| **Aathika Asmeer** | Member  |
| **Nethmi Weerathunga** | Member  |
| **Noorul Shabeeha** | Member  |

**Event:** IntelliCon '26 Buildathon (AIESEC in SLIIT)  
**Track:** Undergraduate · **Domain:** Retail and Supply Chain AI  
**Detailed Task & Module Plan:** See [team.md](team.md) for full task-by-task specifications (`A1`–`F8`).
