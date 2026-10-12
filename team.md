# Scout — System Modules, Tasks & Implementation Plan

> **Team Vortex | IntelliCon '26 Buildathon**  
> **Track:** Undergraduate · **Domain:** Retail & Supply Chain AI  
> **Core Focus:** Autonomous Shelf-Void Detection, Zero-Hardware Inventory Intelligence & GenAI Micro-Audit Routing  
> *(For repository setup, environment configuration, and test instructions, refer to [README.md](README.md))*

---

## 1. System Architecture & The 4 Core Modules

Scout is designed as a decoupled monorepo structured across four primary functional tiers and two support modules:

```
[ Mock POS Event Stream / CSV Feed ]
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Module 1: POS Stream Ingestion & Feature Store                  │
│ (FastAPI, Pandas, Supabase PostgreSQL / In-Memory Store)        │
│ • Batch & CSV ingestion (POST /api/v1/pos/stream)               │
│ • Dense hourly velocity & silence duration feature store        │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼ Hourly sales velocity & silent gap duration
┌─────────────────────────────────────────────────────────────────┐
│ Module 2: Applied ML Anomaly Detection Engine                   │
│ (Zero-Inflated Poisson + Isolation Forest + Baseline Scorer)    │
│ • Likelihood-ratio statistical baseline                         │
│ • Alert trigger filter: P_void >= 0.75 AND POS Ledger Stock > 0 │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼ Flagged anomalies with aisle, bay & loss risk
┌─────────────────────────────────────────────────────────────────┐
│ Module 3: GenAI Floor Action Agent                              │
│ (Gemini 3.8 Flash Reasoning & Aisle Cluster Routing)            │
│ • Shortest physical walking route (Aisle & Bay clustering)      │
│ • Revenue-at-risk ranking & plain-English "Why Flagged" context │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼ Natural briefing & prioritized task cards
┌─────────────────────────────────────────────────────────────────┐
│ Module 4: Supervisor Mobile PWA & Executive Analytics Portal    │
│ (Next.js 14 App Router, Tailwind CSS, Lucide, Recharts)         │
│ • Floor Associate PWA (/floor): Handheld 3-min aisle checklist  │
│   One-tap actions: [Restocked] [Damaged Write-Off] [False Alarm]│
│ • Store Manager Portal (/dashboard): Recharts velocity drop     │
│   charts, LKR revenue recovered, chronic phantom categories     │
│ • Master Inventory Explorer (/inventory): 200-item inspection   │
└─────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ Live trigger & evaluation
┌────────────────────────────────┴────────────────────────────────┐
│ Modules 5 & 6: Simulation Hub & Model Evaluation Harness        │
│ • Judge Simulation Hub (/simulate): 1-click phantom injections  │
│ • Live Scrolling POS Terminal: Real-time transaction feed       │
│ • Evaluation Portal (/evaluation): Precision, Recall, FPR proof │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Modules at a Glance

| # | Module | Core Functionality | Primary Tech Stack | Status |
|---|---|---|---|---|
| **1** | **POS Ingestion & Feature Store** | Ingests raw POS sales, manages database storage, computes dense hourly velocity and silence metrics, handles audit ledger sync. | FastAPI, Pandas, Supabase PostgreSQL, Python | ✅ Complete & Tested |
| **2** | **Applied ML Anomaly Engine** | Evaluates silence durations against expected demand using statistical likelihood ratio, ZIP zero-separation, and Isolation Forest. | NumPy, Scipy, Statsmodels, Scikit-learn | ✅ Complete & Tested |
| **3** | **GenAI Floor Action Agent** | Groups flagged items by physical aisle/bay, prioritizes by revenue risk, and uses Gemini 3.8 Flash to generate a natural morning briefing. | Google Gen AI SDK, Gemini 3.8 Flash, Python | ✅ Complete & Tested |
| **4** | **Floor Associate Mobile PWA** | Mobile-first viewport (`/floor`) providing a 3-minute walking audit with single-tap resolutions (`Restocked`, `Damaged`, `False Alarm`). | Next.js 14, Tailwind CSS, SWR, Lucide, Web Audio | ✅ Complete & Tested |
| **5** | **Store Manager Analytics Portal** | Desktop portal (`/dashboard`, `/inventory`) visualizing recovered revenue, velocity drop curves, chronic departments, and catalog search. | Next.js 14, Recharts, TypeScript, Tailwind CSS | ✅ Complete & Tested |
| **6** | **Simulation Hub & Delivery** | Interactive judge testing hub (`/simulate`, `/evaluation`), real-time streaming POS terminal, synthetic test harness, and pitch assets. | Next.js 14, Pytest, Docker, Vercel | ✅ Complete & Tested |

---

## 3. Detailed Module Breakdown & Task Specifications

### Module 1: POS Ingestion, Data Store & Feature Store
*Backend: `backend/app/api/v1/pos.py`, `backend/app/services/ingest.py`, `backend/app/core/store.py`, `backend/app/generator/`*

Module 1 serves as the foundational data backbone. It continuously ingests point-of-sale transaction rows, manages relational storage in Supabase PostgreSQL (with automatic zero-config fallback to an in-memory store), maintains pre-aggregated hourly velocity features, and syncs physical shelf audits back to store inventory ledgers.

| ID | Feature | Effort | Primary Files | Technical Specifications & Deliverables | Status |
|---|---|---|---|---|---|
| **A1 ★** | **Synthetic POS Transaction Generator** | M | `app/generator/generate_mock_pos.py`, `mock_skus.json` | Generates 1,200–2,000 POS sale lines per day across 200 Sri Lankan grocery SKUs (Keells/Cargills brands like Munchee, Maliban, Anchor, Elephant House). Models peak shopping hours (11:00–13:00, 18:00–21:00 at 2x), weekend surges (1.2x), and payday cycles (1.12x). Injects 3 distinct phantom stockout scenarios: `frozen` (abrupt stop while ledger stays > 30), `damaged` (spoilage requiring ledger write-off), and `backroom_stuck` (gradual 3-hr sales drain as shelf empties). | ✅ Done |
| **A2 ★** | **High-Throughput Batch Stream Endpoint** | S | `app/api/v1/pos.py`, `app/services/ingest.py` | Endpoints `POST /api/v1/pos/stream` (JSON) and `POST /api/v1/pos/stream/csv` (raw CSV stream). Implements resilient row-by-row validation: invalid quantities, unknown SKUs, or unrecognized stores are rejected individually and reported in `errors[]`, while valid rows are ingested (status 200 with partial success report; 422 only if 100% of batch fails). Ingests in chunks of 500 rows (`INGEST_CHUNK_SIZE`). | ✅ Done |
| **A3 ★** | **Supabase PostgreSQL Schema & In-Memory Engine** | M | `supabase/schema.sql`, `app/core/store.py`, `database.py` | Relational schema with 6 tables: `stores`, `skus` (ID, name, category, aisle, bay, ledger_stock, unit_cost), `pos_transactions` (ID, sku_id, timestamp, quantity, unit_price), `hourly_velocity`, `stockout_anomalies` (void score, confidence, status), and `audit_log`. Includes a transparent, thread-safe in-memory store that activates automatically when Supabase keys are not set, guaranteeing 100% offline hackathon testability. | ✅ Done |
| **A4 ★** | **Rolling Hourly Feature Store Pipeline** | M | `app/ml/feature_pipeline.py` | Aggregates raw POS lines into dense hourly sales buckets per SKU across store trading hours (08:00–22:00 Asia/Colombo, UTC+5:30). Fills non-purchase hours with explicit zeroes (crucial for silence detection). Computes `hours_since_last_sale` wall-clock gaps and rolling SKU sales velocity. | ✅ Done |
| **A5 ★** | **Audit Reconciliation Flow & ERP Ledger Sync** | S | `app/api/v1/audit.py`, `app/core/store.py` | Endpoint `POST /api/v1/audit/reconcile` processes floor actions (`restocked`, `damaged`, `false_alarm`). Idempotent execution. When an associate flags `damaged`, the system automatically writes off units from `skus.ledger_stock` (clamped at zero) to prevent ledger bloat, logging the permanent action in `audit_log`. | ✅ Done |
| **A6** | **Catalog Seeder & Streaming CSV Loader** | S | `app/generator/seed.py`, `load_csv.py` | CLI utility to pre-populate 14 days of realistic transaction history (~20,000 transactions across 200 SKUs) and CLI loader to pipe external CSV files directly into the live running API. | ✅ Done |

---

### Module 2: Applied ML Anomaly Detection Engine
*Backend: `backend/app/ml/`, `backend/app/api/v1/anomalies.py`, `backend/app/services/detection.py`*

Module 2 transforms passive transaction streams into high-confidence shelf-void probabilities ($P_{\text{void}} \in [0, 1]$). It eliminates the false alarms typical of crude rules (such as "flag any product with no sales for 3 hours") by conditioning expected sales on store rhythms and individual SKU velocities.

| ID | Feature | Effort | Primary Files | Technical Specifications & Deliverables | Status |
|---|---|---|---|---|---|
| **B1 ★** | **Likelihood-Ratio Statistical Baseline** | M | `app/ml/baseline.py` | Computes expected sales $\lambda_{i,t}$ conditioned on day-of-week and time-of-day store footfall patterns. For a trailing silence of consecutive open hours, computes $P_{\text{void}} = 1 - \exp(-\sum \lambda_{i,t})$ via a likelihood-ratio test with a small prior. Fast-moving items flag in 3–5 silent hours; slow-moving items safely remain quiet for 24+ hours without false alarms. | ✅ Done |
| **B2 ★** | **Detection Pipeline API Wiring** | S | `app/api/v1/anomalies.py`, `app/services/detection.py` | Endpoint `POST /api/v1/anomalies/run` connects feature store velocity directly to the scoring engine. Filters candidates with $P_{\text{void}} \ge 0.75$ AND POS ledger stock $> 0$. Manages alert lifecycle: creates new alerts, refreshes numbers for ongoing voids, and clears alerts if sales resume naturally. Resolved alerts remain immutable. | ✅ Done |
| **B3** | **Zero-Inflated Poisson (ZIP) Engine** | L | `app/ml/zip_model.py` | Implements Zero-Inflated Poisson modeling to statistically decouple structural zeros (natural non-purchase quiet periods during slow hours) from sampling zeros (shelf-void freezes where customers intended to buy but found an empty bay). | ✅ Done |
| **B4** | **Isolation Forest Ensemble Scorer** | M | `app/ml/isolation_forest.py` | Unsupervised scikit-learn anomaly scoring across feature vectors: zero-streak length, ratio of observed to expected volume, and days since last replenishment. Blended with statistical baseline into an ensemble void score. | ✅ Done |
| **B5** | **Dynamic Threshold Calibration** | M | `app/api/v1/audit.py`, `app/ml/feature_pipeline.py` | Ingests historical audit results (`GET /audit/stats`) to compute the store-wide false alarm rate. Dynamically calibrates `VOID_THRESHOLD` to eliminate alert fatigue for floor staff. | ✅ Done |
| **B6** | **Multi-Variant Void Classifier** | M | `app/ml/void_classifier.py` | Classifies the underlying operational reason for the anomaly: abrupt freeze (misplaced item), slow decay (stock trapped in backroom), or sudden zero with ledger discrepancy (damaged/spoiled goods). Suggests appropriate remediation actions. | ✅ Done |

---

### Module 3: GenAI Floor Action Agent
*Backend: `backend/app/agent/`, `backend/app/api/v1/agent.py`*

Module 3 converts cold, tabular anomaly alerts into a human-friendly, localized physical action plan. It clusters tasks physically so floor associates do not crisscross the supermarket, explains *why* each alert was triggered in plain English, and delivers a 3-minute morning briefing via Gemini 3.8 Flash (`gemini-3.8-flash`).

| ID | Feature | Effort | Primary Files | Technical Specifications & Deliverables | Status |
|---|---|---|---|---|---|
| **C1 ★** | **Gemini 3.8 Flash Reasoning Engine** | S | `app/agent/gemini_client.py`, `prompts.py` | Integrates Google Gen AI SDK (`google-genai`). Formulates system prompts to ingest flagged anomaly JSON payloads and generate concise, professional 2-sentence morning briefings for store supervisors. | ✅ Done |
| **C2** | **Aisle Cluster Routing & Revenue Ranking** | M | `app/agent/gemini_client.py`, `store.py` | Sorts and groups tasks by physical store geography (Aisle 01 → 02 → 05, then Bay sequence) to produce the optimal walking route. Prioritizes items within aisles by revenue-at-risk ($\text{Velocity} \times \text{Price} \times \text{Silent Hours}$). | ✅ Done |
| **C3** | **"Why Flagged?" Root-Cause Context** | M | `app/agent/explainer.py` | Generates a 1-sentence plain-English explanation per item for judges and staff: e.g., *"Munchee Cracker usually sells 4.2 units/hr on Saturday lunch; zero sales recorded for 9 consecutive trading hours while ledger shows 40 units."* | ✅ Done |
| **C4** | **Structured JSON Schema Formulation** | M | `app/agent/prompts.py` | Uses typed JSON schema generation to extract structured morning walk metadata: estimated walk time, urgent items count, and primary aisle targets. | ✅ Done |
| **C5** | **Production Reliability & Caching** | S | `app/agent/gemini_client.py` | 5-minute memory caching for identical alert sets, exponential retry on API timeouts, and a deterministic fallback template so the application and demo never fail even during network outages. | ✅ Done |

---

### Module 4: Supervisor Mobile PWA (`/floor`)
*Frontend: `frontend/src/app/floor/`, `frontend/src/components/floor/`, `frontend/src/hooks/`*

Module 4 is the mobile-optimized floor interface used by shelf restockers and store supervisors during their morning walk. Constrained to a handheld mobile viewport (max-width 420px), it eliminates operational friction through single-tap resolution buttons and instant sensory feedback.

| ID | Feature | Effort | Primary Files | Technical Specifications & Deliverables | Status |
|---|---|---|---|---|---|
| **D1 ★** | **Floor Associate Real-Time Checklist** | S | `src/app/floor/page.tsx`, `ChecklistCard.tsx` | Mobile-first viewport connecting directly to `GET /api/v1/agent/checklist`. Renders live aisle-grouped cards displaying product name, barcode, shelf bay, POS ledger units, silent duration, and unit price. Handles loading, empty ("All shelves verified ✓"), and error states. | ✅ Done |
| **D2** | **One-Tap Resolution Actions & Feedback** | S | `ChecklistCard.tsx`, `QuickStatsBar.tsx` | Single-tap resolution loop: **[Restocked]** (found in backroom), **[Damaged]** (spoiled/broken, writes off ledger), **[False Alarm]** (shelf full, genuine lull). Includes web audio chime and haptic vibration on tap. | ✅ Done |
| **D3** | **Shift Progress Bar & Completion Celebration** | S | `src/app/floor/page.tsx` | Real-time shift progress tracker (*"3 of 7 items verified — 4 min remaining"*). Triggers celebratory confetti animation when the final aisle item is verified. | ✅ Done |
| **D4** | **Installable Progressive Web App (PWA)** | M | `public/manifest.json`, `public/icons/` | PWA manifest configuration with app icons, standalone mobile display mode, theme color meta tags, and mobile home-screen installability. | ✅ Done |
| **D5** | **Item Inspection Detail Sheet & Undo** | M | `ChecklistCard.tsx`, `useChecklist.ts` | Expandable bottom sheet showing mini-sales velocity context, last transaction timestamp, and the Gemini explanation. Supports capturing the associate's name and single-tap undo of the last action. | ✅ Done |

---

### Module 5: Store Manager Analytics & Inventory Portal (`/dashboard`, `/inventory`)
*Frontend: `frontend/src/app/dashboard/`, `frontend/src/app/inventory/`, `frontend/src/components/dashboard/`*

Module 5 provides store general managers and category replenishment leads with an executive overview of financial return on investment (ROI), sales velocity divergence, and store-wide inventory record accuracy.

| ID | Feature | Effort | Primary Files | Technical Specifications & Deliverables | Status |
|---|---|---|---|---|---|
| **E1** | **Executive ROI & Financial KPI Stats** | M | `src/app/dashboard/page.tsx`, `MetricCards.tsx` | Dynamic KPI row computing: Estimated Revenue Recovered (LKR), Active Phantom Voids, Audit Completion Rate (%), and Inventory Record Inaccuracy (IRI) reduction percentage. | ✅ Done |
| **E2** | **Sales Velocity Divergence Chart** | M | `VelocityChart.tsx` | Recharts dual-line time-series graph visualizing expected baseline sales velocity vs. actual sales velocity for flagged SKUs, illustrating the sudden drop to zero despite positive ledger stock. | ✅ Done |
| **E3** | **High-Risk Anomaly Category Breakdown** | S | `CategoryBreakdown.tsx` | Bar chart displaying phantom void concentration across store departments (e.g., Chilled Dairy 38%, Biscuits & Confectionery 26%, Dry Staples 18%). | ✅ Done |
| **E4** | **Live Reconciliations Activity Feed** | S | `RecentActivityFeed.tsx` | Chronological audit log showing associate floor resolutions: e.g., *"Munchee Super Cream Cracker 490g — 24 units restocked from Bay 3B by Associate Nimal"*. | ✅ Done |
| **E5** | **Master 200-SKU Inventory Explorer** | M | `src/app/inventory/page.tsx` | Searchable, filterable table covering all 200 items. Instant search by product name/brand, quick filter tabs (`All Items`, `Critical Voids P_void >= 0.75`, `Reconciled Today`), and risk badges. | ✅ Done |
| **E6** | **Deep SKU Inspection Drilldown** | M | `src/app/inventory/[id]/page.tsx` | Product-level telemetry page displaying 14-day sales velocity history, trailing hourly sales, void risk score over time, and past audit actions. | ✅ Done |

---

### Module 6: Demo Simulation, Evaluation & Delivery (`/simulate`, `/evaluation`)
*Frontend & Backend: `frontend/src/app/simulate/`, `frontend/src/app/evaluation/`, `backend/tests/`*

Module 6 provides competition judges with an interactive testing environment. It solves the demo dilemma by allowing judges to inject phantom stockouts and watch the ML engine and Gemini agent detect and route them in real time without waiting for real-world transaction hours.

| ID | Feature | Effort | Primary Files | Technical Specifications & Deliverables | Status |
|---|---|---|---|---|---|
| **F1 ★** | **Interactive Judge Simulation Hub** | S | `src/app/simulate/page.tsx`, `backend/app/api/v1/simulate.py` | 1-click preset scenario triggers: **[Inject Phantom Stockout]** (Munchee Biscuits freeze for 8 hrs), **[Simulate Normal Peak]** (high sales volume across all 200 items), and **[Reset Store State]**. One-click trigger button: **[Run Scout Anomaly Detection & Trigger Gemini Agent]**. | ✅ Done |
| **F2** | **Live Streaming POS Terminal** | M | `src/components/simulate/LiveTerminal.tsx` | Compact, authentic black terminal box displaying incoming synthetic transactions streaming into FastAPI in real time `[timestamp, sku_id, quantity, unit_price]`. | ✅ Done |
| **F3** | **Statistical Model Evaluation Harness** | L | `backend/app/ml/evaluation.py`, `tests/test_evaluation_harness.py` | Automated testing harness executing simulated trading across quiet days, peak weekends, and 3 void scenarios. Computes empirical Precision, Recall, and False Positive Rates comparing Scout against naive threshold rules. | ✅ Done |
| **F4** | **Dedicated Model Evaluation Portal** | M | `src/app/evaluation/page.tsx` | Interactive UI showing benchmark metrics, ROC/confusion matrix insights, and side-by-side performance comparison proving Scout's statistical superiority over fixed heuristic rules. | ✅ Done |
| **F5** | **End-to-End Automated Integration Test** | S | `backend/tests/test_e2e_flow.py` | Automated verification test: Injects phantom stockout → Runs detection engine → Validates alert creation → Fetches Gemini briefing → Executes staff reconciliation → Verifies ledger deduction and audit row. | ✅ Done |
| **F6** | **Production Cloud Deployment** | M | `Dockerfile`, `docker-compose.yml`, `DEPLOYMENT.md` | Deployment configuration: FastAPI backend containerized on Render/Railway, Next.js frontend on Vercel, Supabase PostgreSQL in the cloud. | ✅ Done |
| **F7** | **Competition Demonstration Script & Video** | M | `README.md` | Standardized hackathon pitch flow and demonstration artifacts for judges. | ✅ Done |
| **F8** | **Final Architectural & ROI Documentation** | M | `README.md`, `team.md` | Comprehensive system documentation detailing architecture, mathematical formulation, operational workflows, and financial impact. | ✅ Done |

---

## 4. Core Application Routes & Screen Breakdown

Scout features 4 core operational pages, 1 interactive landing hub, and 1 dedicated evaluation page:

```
/ (Home / Portal Switcher)
 ├── /dashboard      (Store Manager Web Portal - Desktop)
 ├── /floor          (Floor Associate Morning Walk - Mobile PWA)
 ├── /inventory      (Master SKU & Phantom Alert Log - Desktop/Tablet)
 ├── /simulate       (Judge Demo / Trigger Simulation Hub - Any Device)
 └── /evaluation     (Statistical Benchmark & Model Performance Portal)
```

| Route | Viewport | Target User | Core Value & Job to be Done |
|---|---|---|---|
| **`/`** | Desktop / Mobile | Evaluators & Staff | Split-card portal switcher directing users to Manager Portal, Floor Associate PWA, Simulation Playground, or Model Evaluation. |
| **`/dashboard`** | Desktop (1280px+) | Store GM, Regional Directors | Proves ROI and operational vigilance: recovered LKR revenue, active void count, Recharts velocity drop curve, and chronic department breakdown. |
| **`/floor`** | Mobile PWA (max-w 420px) | Floor Supervisors, Restockers | Frictionless 3-minute morning walk physically clustered by aisle/bay with Gemini 3.8 Flash briefing and single-tap resolution buttons (`Restocked`, `Damaged`, `False Alarm`). |
| **`/inventory`** | Desktop / Tablet | Inventory Controllers | Search, filter, and inspect the complete 200-SKU supermarket catalog and audit logs with instant search, status badges, and $P_{\text{void}}$ risk scores. |
| **`/simulate`** | Any Screen | Competition Judges | Solves the demo dilemma: 1-click phantom injection triggers, real-time streaming POS code terminal, and immediate detection pipeline execution. |
| **`/evaluation`** | Desktop / Tablet | Technical Judges & Evaluators | Empirical proof of ML detection accuracy: benchmark metrics (Precision, Recall, F1, FPR) across 19,600 checks, comparing Scout to naive threshold rules. |

---

## 5. Complete System Implementation & Delivery Matrix

Every feature across all six modules is tracked in this delivery matrix. All core features have been implemented and validated against the comprehensive 158-test Pytest suite.

| ID | Module | Feature Description | Complexity | Primary Code Layer | Implementation Status |
|:---:|---|---|:---:|---|:---:|
| **A1** | Module 1 | 200-SKU Synthetic POS Generator (Peak/Weekend/3 Phantom Scenarios) | M | `backend/app/generator/` | ✅ Complete & Tested |
| **A2** | Module 1 | FastAPI Batch & CSV POS Streaming Ingestion Endpoints | S | `backend/app/api/v1/pos.py` | ✅ Complete & Tested |
| **A3** | Module 1 | Supabase PostgreSQL Schema & Zero-Config In-Memory Store | M | `supabase/schema.sql`, `app/core/store.py` | ✅ Complete & Tested |
| **A4** | Module 1 | Pre-Aggregated Hourly Sales Feature Store & Silent Gap Tracker | M | `backend/app/ml/feature_pipeline.py` | ✅ Complete & Tested |
| **A5** | Module 1 | Audit Reconciliation Flow & Atomic ERP Ledger Write-Off | S | `backend/app/api/v1/audit.py` | ✅ Complete & Tested |
| **A6** | Module 1 | Catalog Pre-Seeder CLI & Bulk CSV Streaming Utility | S | `backend/app/generator/seed.py` | ✅ Complete & Tested |
| **B1** | Module 2 | Likelihood-Ratio Statistical Baseline Detector | M | `backend/app/ml/baseline.py` | ✅ Complete & Tested |
| **B2** | Module 2 | Anomaly Detection API Wiring & Alert Lifecycle Management | S | `backend/app/api/v1/anomalies.py` | ✅ Complete & Tested |
| **B3** | Module 2 | Zero-Inflated Poisson (ZIP) Demand vs. Void Model | L | `backend/app/ml/zip_model.py` | ✅ Complete & Tested |
| **B4** | Module 2 | Isolation Forest Ensemble Scoring Pipeline | M | `backend/app/ml/isolation_forest.py` | ✅ Complete & Tested |
| **B5** | Module 2 | Audit-Driven Threshold Sensitivity Calibration | M | `backend/app/api/v1/audit.py` | ✅ Complete & Tested |
| **B6** | Module 2 | Multi-Scenario Void Reason Classifier | M | `backend/app/ml/void_classifier.py` | ✅ Complete & Tested |
| **C1** | Module 3 | Gemini 3.8 Flash Live Briefing Generation Engine | S | `backend/app/agent/gemini_client.py` | ✅ Complete & Tested |
| **C2** | Module 3 | Physical Aisle Clustering & Revenue-at-Risk Prioritization | M | `backend/app/agent/gemini_client.py` | ✅ Complete & Tested |
| **C3** | Module 3 | Plain-English "Why Flagged?" Root-Cause Explainer | M | `backend/app/agent/explainer.py` | ✅ Complete & Tested |
| **C4** | Module 3 | Structured JSON Schema Formulation for Floor Routing | M | `backend/app/agent/prompts.py` | ✅ Complete & Tested |
| **C5** | Module 3 | 5-Minute In-Memory Caching & Deterministic Fallback Template | S | `backend/app/agent/gemini_client.py` | ✅ Complete & Tested |
| **D1** | Module 4 | Floor Associate Real-Time Mobile Checklist View | S | `frontend/src/app/floor/page.tsx` | ✅ Complete & Tested |
| **D2** | Module 4 | Single-Tap Reconcile Actions with Audio/Haptic Confirmation | S | `frontend/src/components/floor/` | ✅ Complete & Tested |
| **D3** | Module 4 | Shift Progress Tracker & Celebratory Completion Confetti | S | `frontend/src/components/floor/` | ✅ Complete & Tested |
| **D4** | Module 4 | Progressive Web App (PWA) Manifest & App Icons | M | `frontend/public/manifest.json` | ✅ Complete & Tested |
| **D5** | Module 4 | Item Detail Inspection Sheet & Action Undo Support | M | `frontend/src/components/floor/` | ✅ Complete & Tested |
| **E1** | Module 5 | Executive ROI Metrics (LKR Recovered, IRI Reduction, Voids) | M | `frontend/src/app/dashboard/` | ✅ Complete & Tested |
| **E2** | Module 5 | Sales Velocity Divergence Time-Series Chart (Recharts) | M | `frontend/src/components/dashboard/` | ✅ Complete & Tested |
| **E3** | Module 5 | Department Anomaly Concentration Bar Breakdown | S | `frontend/src/components/dashboard/` | ✅ Complete & Tested |
| **E4** | Module 5 | Live Chronological Floor Reconciliations Feed | S | `frontend/src/components/dashboard/` | ✅ Complete & Tested |
| **E5** | Module 5 | Master 200-SKU Filterable Inventory Explorer Table | M | `frontend/src/app/inventory/page.tsx` | ✅ Complete & Tested |
| **E6** | Module 5 | Deep SKU Historical Sales & Void Telemetry Drilldown | M | `frontend/src/app/inventory/[id]/` | ✅ Complete & Tested |
| **F1** | Module 6 | Interactive Judge Simulation Playground & Scenario Triggers | S | `frontend/src/app/simulate/page.tsx` | ✅ Complete & Tested |
| **F2** | Module 6 | Live Streaming POS Code Terminal Feed | M | `frontend/src/components/simulate/` | ✅ Complete & Tested |
| **F3** | Module 6 | Statistical Evaluation Benchmark Test Harness | L | `backend/app/ml/evaluation.py` | ✅ Complete & Tested |
| **F4** | Module 6 | Model Benchmark & Metrics Comparison Portal | M | `frontend/src/app/evaluation/page.tsx` | ✅ Complete & Tested |
| **F5** | Module 6 | Full End-to-End Automated Integration Test Suite | S | `backend/tests/test_e2e_flow.py` | ✅ Complete & Tested |
| **F6** | Module 6 | Cloud Deployment Setup (Docker, Render, Vercel, Supabase) | M | `Dockerfile`, `DEPLOYMENT.md` | ✅ Complete & Tested |
| **F7** | Module 6 | Competition Demonstration Script & Video | M | `README.md` | ✅ Complete & Tested |
| **F8** | Module 6 | Final Architecture, Mathematical Formulation & Slide Assets | M | `README.md`, `team.md` | ✅ Complete & Tested |
