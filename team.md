# Scout — Team Plan: Modules, Features & Pages

Pick a feature, put your name next to it in the **Claim board** (bottom), make a branch named after the feature ID, build it, open a PR.
Example: `feat/B1-baseline-detector`.

**Effort:** S = small, M = medium, L = large. **★** = needed for the first working demo.

---

## The first demo (do these four first ★)

One thin slice through the whole product. Four small features, so four people can each take one and have something to show quickly:

```
/simulate  →  Detect  →  /floor checklist  →  tap "Restocked"
  (F1)        (B1+B2)        (D1)
```

1. **F1** Simulate button injects a phantom stockout, then calls detection.
2. **B1 + B2** A simple detector flags the frozen SKU and saves it as an anomaly.
3. **D1** `/floor` shows that real alert and the Restocked / Damaged / False alarm buttons write back.

When these work together, the main story is working end to end: *stock sits in the system, sales stop, Scout flags it, staff fix it.* Everything else improves or proves that story.

---

## Modules at a glance

| # | Module | What it does | Status |
|---|---|---|---|
| 1 | **Data & Ingestion** | POS ingest, feature store, audit flow, 200-SKU generator, Supabase seed | ✅ Done (merged) |
| 2 | **Detection Engine** | Turns sales history into a "shelf void" probability per SKU | ✅ Done (merged) |
| 3 | **AI Agent (Gemini)** | Turns flagged SKUs into a prioritised, aisle-grouped checklist | In progress (C1 verified) |
| 4 | **Floor App** | Mobile page for the 3-minute morning audit | UI stub exists |
| 5 | **Manager Portal** | Dashboard, KPIs, charts, SKU explorer | UI stub exists |
| 6 | **Demo, Evaluation & Delivery** | Simulation hub, accuracy numbers, deployment, pitch | To do |

---

## Module 2 — Detection Engine
*Python · pandas · statsmodels · scikit-learn. Files: `backend/app/ml/`, `backend/app/api/v1/anomalies.py`*

| ID | Feature | Effort | Depends on | Notes |
|---|---|---|---|---|
| **B1 ★** | **Baseline detector** | M | Module 1 | Learn each SKU's normal sales by day-of-week and hour. For a run of zero-sale open hours, `p_void = 1 − exp(−Σ expected_sales)`: the chance that a silence this long is NOT normal. Simple, explainable, works now. New file `ml/baseline.py` with `score_voids(velocity) -> sku_id, p_void, hours_since_last_sale`. |
| **B2 ★** | **Wire detection into the API** | S | B1 | `POST /api/v1/anomalies/run` currently returns the 3 hardcoded sample alerts. Replace with: get velocity → score → keep rows where `p_void ≥ 0.75` AND ledger stock > 0 → save to `stockout_anomalies` → return them. Use `get_velocity()` and `hours_since_last_sale()` from the new data layer (check the exact signatures in `store.py`). |
| B3 | Zero-Inflated Poisson model | L | B1 | `ml/zip_model.py`. Separates "normally nobody buys this" zeros from "shelf is empty" zeros. Compare against B1 and keep whichever scores better. |
| B4 | Isolation Forest + combined score | M | B1 | `ml/isolation_forest.py`. Features: zero streak, ratio to expected, days since last restock. Blend with B1/B3 into the final `p_void`. |
| B5 | Threshold calibration + feedback | M | B2, audit data | Use `GET /audit/stats` (false-alarm rate) to adjust `VOID_THRESHOLD`. Fewer false alarms means less alert fatigue. |
| B6 | Detect other void types | M | B1 | Damaged-not-written-off and backroom-stuck scenarios (the generator already makes these). Suggest a different action for each. |

## Module 3 — AI Agent (Gemini)
*Python · google-genai. Files: `backend/app/agent/`*

| ID | Feature | Effort | Depends on | Notes |
|---|---|---|---|---|
| C1 | Verify live Gemini call | S | API key | Put a real `GEMINI_API_KEY` in `.env` and confirm the briefing works (never tested with a real key). Model name is the `GEMINI_MODEL` setting. |
| C2 | Smart prioritisation | M | B2 | Rank items by revenue at risk (units sold per hour × price × hours silent), not just probability. Shorter walk path = better. |
| C3 | "Why was this flagged?" | M | B2 | One plain-English sentence per item, e.g. "Usually sells 4/hr at this time, none in 9 hours, ledger says 32." Great for judges. |
| C4 | Structured JSON output | M | C1 | Ask Gemini for a typed schema (priority, reason, suggested action) instead of free text. |
| C5 | Reliability | S | C1 | Timeouts, retries, cache the briefing, always fall back to the template so the demo never breaks. |

## Module 4 — Floor App (`/floor`, mobile)
*Next.js · Tailwind. Files: `frontend/src/app/floor/`, `frontend/src/components/floor/`*

| ID | Feature | Effort | Depends on | Notes |
|---|---|---|---|---|
| **D1 ★** | **Connect to real data** | S | B2 | `useChecklist()` and `api.reconcile()` already exist. Make sure real alerts show and each button writes back (and survives a page refresh). Handle loading, empty ("All clear ✓") and error states. |
| D2 | Completion moment | S | D1 | Progress bar, checkmark/confetti animation, vibration + sound on tap. |
| D3 | Installable PWA | M | D1 | Add to home screen, icons, offline message. Test on a real phone. |
| D4 | Item detail sheet | M | B2 | Tap a card → mini sales chart, last sale time, Gemini "why flagged" (C3). |
| D5 | Associate name + undo | S | D1 | Enter name once (sent as `associate`), undo the last action. |

## Module 5 — Manager Portal (`/dashboard`, `/inventory`, desktop)
*Next.js · Recharts. Files: `frontend/src/app/dashboard/`, `frontend/src/app/inventory/`, `frontend/src/components/dashboard/`*

| ID | Feature | Effort | Depends on | Notes |
|---|---|---|---|---|
| E1 | Real KPIs | M | Audit data | `GET /anomalies/metrics` returns hardcoded numbers (LKR 482,500, 94%, 4.8%). Compute from real data: active voids, audit completion rate, revenue recovered. Backend + frontend. |
| E2 | Expected-vs-actual velocity chart | M | B1 | New endpoint e.g. `GET /anomalies/{id}/velocity`. The chart currently draws a fake curve. This is the best visual for the pitch: the line falling to zero while the ledger says stock exists. |
| E3 | High-risk category chart | S | E1 | Bar chart: which categories hide the most phantom stock. |
| E4 | Recent reconciliations feed | S | Audit data | "24 units of Munchee Cracker restocked from Bay 3B by Nimal". |
| E5 | `/inventory` full explorer | M | New `GET /api/v1/skus` | All 200 SKUs, search, filter tabs (All · Critical voids · Reconciled today), risk badge. Currently only shows anomalies. |
| E6 | SKU detail page | M | E2, E5 | `/inventory/[id]`: history, void score over time, past audits. |

## Module 6 — Demo, Evaluation & Delivery
*Mixed. Files: `frontend/src/app/simulate/`, `backend/tests/`, `docs/`*

| ID | Feature | Effort | Depends on | Notes |
|---|---|---|---|---|
| **F1 ★** | **Simulation hub flow** | S | B2 | Buttons already inject scenarios. Make "Run Scout Detection & Trigger Agent" call detection and then show links/result for `/floor` and `/dashboard`. |
| F2 | Live POS terminal | M | F1 | Scrolling black box of incoming transactions streaming in during the demo. |
| F3 | Evaluation harness | L | B1 | Run many generated scenarios (quiet days, peak weekends, all three void types), measure **precision, recall, false-positive rate**. Compare B1 vs B3/B4. Needed for the final evaluation. |
| F4 | `/evaluation` page | M | F3 | Show the metrics and a comparison chart: simple rule vs Scout. Strong proof for judges. |
| F5 | End-to-end test | S | D1, F1 | One automated test: inject phantom → detect → appears in checklist → reconcile → resolved. |
| F6 | Deployment | M | Working app | Frontend on Vercel, backend on a free host (Render/Railway), Supabase live, so judges can open a link. |
| F7 | Demo script + video | M | F1 | The storyline: stockout happens → Scout flags → phone buzzes → staff tap → fixed. |
| F8 | Slides + final documentation | M | F3 | Problem, solution, results, architecture, ROI. |

---

## Pages

| Page | Who uses it | Module | Status |
|---|---|---|---|
| `/` | Anyone | — | Done (links to portals) |
| `/floor` | Floor staff (phone) | 4 | Stub → D1–D5 |
| `/dashboard` | Store manager | 5 | Stub → E1–E4 |
| `/inventory` | Inventory controller | 5 | Stub → E5, E6 |
| `/simulate` | Judges / demo | 6 | Working buttons → F1, F2 |
| `/evaluation` *(new)* | Judges | 6 | F4 |
| `/inventory/[id]` *(new)* | Inventory controller | 5 | E6 |

---

## Suggested picks (change freely)

- **Likes statistics / Python:** B1 → B3 → B4 → B5
- **Likes data / backend:** B2 → E1 → E5 endpoint → F3
- **Likes UI:** D1 → D2 → E2 chart → E3/E4
- **Likes presenting / testing:** F1 → F5 → F7 → F8, plus C1/C3 for Gemini

## Rules so we don't collide

- One feature = one branch = one PR. Don't push to `main`.
- Sync your fork and `git pull` before starting a feature.
- If you change an API response, update the Pydantic model **and** `frontend/src/lib/types.ts` in the same PR, and tell the group.
- Before a PR: `pytest` (backend) and `npm run lint && npm run build` (frontend).
- Done means: it works in the running app, has a test if it's backend logic, and you've shown the group a screenshot or a quick demo.

---

## Claim board

| ID | Feature | Owner | Status |
|---|---|---|---|
| B1 | Baseline detector | Shazmina | Done |
| B2 | Wire detection into API | Shazmina | Done |
| D1 | Floor app real data | | |
| F1 | Simulation hub flow | | |
| B3 | ZIP model | Shazmina | Done |
| B4 | Isolation Forest + combined score | Shazmina | Done |
| B5 | Threshold calibration | Shazmina | Done |
| B6 | Other void types | Shazmina | Done |
| C1 | Verify live Gemini | Shazmina | Done |
| C2 | Smart prioritisation | | |
| C3 | "Why flagged" | | |
| C4 | Structured JSON output | | |
| C5 | Reliability | | |
| D2 | Completion moment | | |
| D3 | Installable PWA | | |
| D4 | Item detail sheet | | |
| D5 | Associate name + undo | | |
| E1 | Real KPIs | | |
| E2 | Velocity chart | | |
| E3 | Category chart | | |
| E4 | Reconciliations feed | | |
| E5 | `/inventory` explorer | | |
| E6 | SKU detail page | | |
| F2 | Live POS terminal | | |
| F3 | Evaluation harness | | |
| F4 | `/evaluation` page | | |
| F5 | End-to-end test | | |
| F6 | Deployment | | |
| F7 | Demo script + video | | |
| F8 | Slides + docs | | |

*Status values: To do · In progress · In review · Done*
