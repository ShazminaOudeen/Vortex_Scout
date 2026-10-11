# Vortex Scout — Cloud Deployment Guide

This guide details the deployment of the complete **Vortex Scout** stack:
- **Backend API**: Hosted on **Railway** (Python 3.12 + FastAPI + ML)
- **Frontend App**: Hosted on **Vercel** (Next.js 14 App Router)
- **Database**: In-memory demo store (Default, zero configuration) or **Supabase** (Optional PostgreSQL tier)

---

## Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │            Vercel (Frontend)         │
                      │       Next.js 14 App Router          │
                      │  https://vortex-scout.vercel.app     │
                      └──────────────────┬───────────────────┘
                                         │
                   REST Calls with JSON  │ NEXT_PUBLIC_API_URL
                                         ▼
                      ┌──────────────────────────────────────┐
                      │           Railway (Backend)          │
                      │       FastAPI + Uvicorn + ML         │
                      │   https://vortex-scout-production    │
                      │            .up.railway.app           │
                      └──────────────────┬───────────────────┘
                                         │
                     ┌───────────────────┴───────────────────┐
                     ▼                                       ▼
          [In-Memory Store]                        [Supabase PostgreSQL]
        (Default, zero-config)                    (Optional persistence)
```

---

## Part 1: Deploy Backend to Railway

Railway automatically builds and runs the container using our root [`Dockerfile`](./Dockerfile).

### Step-by-Step Railway Setup

1. In the [Railway Dashboard](https://railway.com), click **+ New Project** → **Deploy from GitHub repo**.
2. Select your **`Vortex_Scout`** repository and click **Deploy Now**.
3. In the project canvas, click on your service box.
4. Go to the **Variables** tab and add:

| Key | Value | Description |
|---|---|---|
| `CORS_ORIGINS` | `*` | Allows browser requests from your Vercel frontend |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Gemini model for AI Floor briefing & reasons |
| `GEMINI_API_KEY` | *(Your key)* | Your Google AI Studio API key |

5. Go to the **Settings** tab:
   - Scroll down to **Networking**.
   - Click **Generate Domain** *(or "Add Domain" → "Railway Domain")*.
   - Copy the generated domain (e.g. `https://vortex-scout-production.up.railway.app`).

### Verify Backend Health
Open these URLs in your browser:
- `https://<your-railway-url>/health` → should return `{"status":"ok"}`
- `https://<your-railway-url>/docs` → interactive Swagger API documentation

---

## Part 2: Deploy Frontend to Vercel

Vercel hosts the Next.js frontend with global edge caching and automatic SSL.

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
| `NEXT_PUBLIC_API_URL` | `https://<your-railway-url>` | Use your live Railway URL from Part 1 (no trailing slash) |

6. Click **Deploy**.
7. In ~1 minute, Vercel gives you your live production URL (e.g. `https://vortex-scout.vercel.app`).

---

## Part 3: Verify the Live Cloud Application

Test the live end-to-end flow directly in your browser:

1. **Simulation Hub (`/simulate`)**:
   - Open `https://<your-vercel-domain>/simulate`.
   - Click **"Simulate Phantom Stockout (Bay 3B)"** → verifies write to cloud backend.
   - Click **"Run Scout Detection & Trigger Agent"** → ML detector flags the shelf void.
2. **Floor App (`/floor`)**:
   - Open `/floor`.
   - Verify the flagged item appears with AI reason and bay number.
   - Tap **"Restocked"** → status changes and audit log updates.
3. **Manager Dashboard (`/dashboard`)**:
   - Open `/dashboard`.
   - Confirm active void KPI counters, velocity charts, and recent reconciliation feed reflect real data.
4. **Evaluation Engine (`/evaluation`)**:
   - Open `/evaluation`.
   - Run the benchmark evaluation and inspect live ROC curves proving 96%+ accuracy.
