# Vortex Scout — Cloud Deployment Guide

[![Live Frontend](https://img.shields.io/badge/Vercel-Live%20Frontend-000000?style=for-the-badge&logo=vercel)](https://vortex-scout.vercel.app/)
[![Live Backend](https://img.shields.io/badge/Railway-Live%20Backend-0B0D0E?style=for-the-badge&logo=railway)](https://vortexscout-production.up.railway.app)
[![Swagger Docs](https://img.shields.io/badge/FastAPI-Swagger%20Docs-009688?style=for-the-badge&logo=fastapi)](https://vortexscout-production.up.railway.app/docs)

This guide details the deployment of the complete **Vortex Scout** production stack:
- **Backend API**: Hosted on **Railway** (Python 3.12 + FastAPI + Applied ML Engine)
- **Frontend App**: Hosted on **Vercel** (Next.js 14 App Router)
- **Database**: Thread-safe in-memory store (Default, zero configuration) or **Supabase** (Optional PostgreSQL tier)

---

## 🌐 Live Production Endpoints

The system is deployed and fully operational:

| Service | Platform | Direct Link | Status / Purpose |
|---|---|---|---|
| **Web App & Mobile PWA** | Vercel | [https://vortex-scout.vercel.app/](https://vortex-scout.vercel.app/) | Production UI (Desktop & Mobile) |
| **Backend REST API** | Railway | [https://vortexscout-production.up.railway.app](https://vortexscout-production.up.railway.app) | FastAPI streaming & anomaly scoring engine |
| **API Health Check** | Railway | [https://vortexscout-production.up.railway.app/health](https://vortexscout-production.up.railway.app/health) | Live service status (`{"status":"ok"}`) |
| **Interactive Swagger Docs** | Railway | [https://vortexscout-production.up.railway.app/docs](https://vortexscout-production.up.railway.app/docs) | Interactive OpenAPI / Swagger UI |

### Direct Application Routes
- 📊 **Executive Dashboard:** [https://vortex-scout.vercel.app/dashboard](https://vortex-scout.vercel.app/dashboard)
- 📱 **Floor Associate Mobile PWA:** [https://vortex-scout.vercel.app/floor](https://vortex-scout.vercel.app/floor)
- 📦 **Master 200-SKU Explorer:** [https://vortex-scout.vercel.app/inventory](https://vortex-scout.vercel.app/inventory)
- ⚡ **Simulation Demo Playground:** [https://vortex-scout.vercel.app/simulate](https://vortex-scout.vercel.app/simulate)
- 📈 **Model Evaluation Benchmark:** [https://vortex-scout.vercel.app/evaluation](https://vortex-scout.vercel.app/evaluation)

---

## Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │            Vercel (Frontend)         │
                      │       Next.js 14 App Router          │
                      │    https://vortex-scout.vercel.app   │
                      └──────────────────┬───────────────────┘
                                         │
                    REST Calls with JSON │ NEXT_PUBLIC_API_URL
                                         ▼
                      ┌──────────────────────────────────────┐
                      │           Railway (Backend)          │
                      │       FastAPI + Uvicorn + ML         │
                      │   https://vortexscout-production     │
                      │            .up.railway.app           │
                      └──────────────────┬───────────────────┘
                                         │
                      ┌──────────────────┴───────────────────┐
                      ▼                                      ▼
           [In-Memory Store]                        [Supabase PostgreSQL]
         (Default, zero-config)                    (Optional persistence)
```

---

## Part 1: Deploy Backend to Railway

Railway automatically builds and runs the backend container using our root [`Dockerfile`](./Dockerfile).

### Step-by-Step Railway Setup

1. In the [Railway Dashboard](https://railway.com), click **+ New Project** → **Deploy from GitHub repo**.
2. Select your **`Vortex_Scout`** repository and click **Deploy Now**.
3. In the project canvas, click on your service box.
4. Go to the **Variables** tab and configure:

| Key | Value | Description |
|---|---|---|
| `CORS_ORIGINS` | `*` | Allows browser requests from your Vercel frontend |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Gemini model for AI Floor briefing & reasons |
| `GEMINI_API_KEY` | *(Your key)* | Your Google AI Studio API key |

5. Go to the **Settings** tab:
   - Scroll down to **Networking**.
   - Click **Generate Domain** *(or "Add Domain" → "Railway Domain")*.
   - Copy the generated domain (e.g. `https://vortexscout-production.up.railway.app`).

### Verify Backend Health
Open these URLs in your browser:
- [https://vortexscout-production.up.railway.app/health](https://vortexscout-production.up.railway.app/health) → returns `{"status":"ok"}`
- [https://vortexscout-production.up.railway.app/docs](https://vortexscout-production.up.railway.app/docs) → interactive Swagger API documentation

---

## Part 2: Deploy Frontend to Vercel

Vercel hosts the Next.js frontend with global edge caching, serverless routing, and automatic SSL.

### Step-by-Step Vercel Setup

1. Sign up or log in to [Vercel](https://vercel.com) using GitHub.
2. Click **Add New…** → **Project**.
3. Import your `Vortex_Scout` GitHub repository.
4. In the **Configure Project** screen:
   - **Framework Preset**: `Next.js` (automatically detected)
   - **Root Directory**: Click **Edit** and choose `frontend` *(⚠️ Crucial monorepo setting!)*
5. Expand **Environment Variables** and add:

| Name | Value | Note |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://vortexscout-production.up.railway.app` | The live Railway API URL (no trailing slash) |

6. Click **Deploy**.
7. In ~1 minute, Vercel gives you your live production URL: [https://vortex-scout.vercel.app](https://vortex-scout.vercel.app).

---

## Part 3: Verify the Live Cloud Application

Test the live end-to-end flow directly in your browser:

1. **Simulation Hub ([/simulate](https://vortex-scout.vercel.app/simulate))**:
   - Open [https://vortex-scout.vercel.app/simulate](https://vortex-scout.vercel.app/simulate).
   - Observe incoming synthetic transactions streaming into the black terminal code box.
   - Click **"Inject Phantom Stockout (Munchee Biscuits)"** → injects anomaly into the Railway cloud backend.
   - Click **"Run Scout Anomaly Detection & Trigger Agent"** → ML engine detects the void ($P_{\text{void}} > 0.90$) and triggers Gemini 3.8 Flash.
2. **Floor App ([/floor](https://vortex-scout.vercel.app/floor))**:
   - Open [https://vortex-scout.vercel.app/floor](https://vortex-scout.vercel.app/floor).
   - Verify the flagged Munchee Biscuits item appears under *Aisle 03* with the Gemini briefing at the top.
   - Tap **"Restocked"** → audio chime triggers, status updates, and audit trail records.
3. **Manager Dashboard ([/dashboard](https://vortex-scout.vercel.app/dashboard))**:
   - Open [https://vortex-scout.vercel.app/dashboard](https://vortex-scout.vercel.app/dashboard).
   - Confirm active void KPI counters, dual-line velocity charts, and the recent reconciliation feed reflect live data.
4. **Master SKU Explorer ([/inventory](https://vortex-scout.vercel.app/inventory))**:
   - Open [https://vortex-scout.vercel.app/inventory](https://vortex-scout.vercel.app/inventory).
   - Filter and search across all 200 items in the catalog.
5. **Evaluation Portal ([/evaluation](https://vortex-scout.vercel.app/evaluation))**:
   - Open [https://vortex-scout.vercel.app/evaluation](https://vortex-scout.vercel.app/evaluation).
   - Inspect benchmark evaluation metrics (Precision, Recall, FPR) proving Scout's statistical formulation over fixed heuristics.
