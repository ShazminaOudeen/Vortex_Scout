# Vortex Scout — Cloud Deployment Guide

This guide walks through deploying the complete **Vortex Scout** stack using free cloud tiers:
- **Backend API**: Hosted on [Render](https://render.com) (Free Web Service)
- **Frontend App**: Hosted on [Vercel](https://vercel.com) (Free Hobby Tier)
- **Database**: In-memory demo store (Zero-config default) or [Supabase](https://supabase.com) (Free PostgreSQL tier)

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
                      │            Render (Backend)          │
                      │       FastAPI + Uvicorn + ML         │
                      │  https://vortex-scout.onrender.com   │
                      └──────────────────┬───────────────────┘
                                         │
                     ┌───────────────────┴───────────────────┐
                     ▼                                       ▼
          [In-Memory Store]                        [Supabase PostgreSQL]
        (Default, zero-config)                    (Optional persistence)
```

---

## Part 1: Deploy Backend to Render (Free Tier)

Render provides a free Web Service tier that can run the Python FastAPI backend.

### Option A: 1-Click Render Blueprint (Recommended)

The repository includes a `render.yaml` blueprint at the root.

1. Sign up or log in to [Render](https://dashboard.render.com).
2. Click **New +** in the top navigation bar and select **Blueprint**.
3. Connect your GitHub account and select the `Vortex_Scout` repository.
4. Render will detect `render.yaml` and configure the service automatically:
   - **Service Name**: `vortex-scout-backend`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
5. Click **Apply**.
6. When deployment finishes, copy your live backend URL (e.g. `https://vortex-scout-backend.onrender.com`).

---

### Option B: Manual Web Service Setup on Render

If you prefer setting it up manually:

1. In the [Render Dashboard](https://dashboard.render.com), click **New +** → **Web Service**.
2. Select **Build and deploy from a Git repository** and connect `Vortex_Scout`.
3. Fill in the service configuration:
   - **Name**: `vortex-scout-backend`
   - **Region**: Oregon (US West) or Frankfurt (EU)
   - **Branch**: `main`
   - **Root Directory**: `backend` *(Important: monorepo subfolder)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
4. Expand **Advanced** and add the following **Environment Variables**:

| Variable | Value | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.11.9` | Ensures a stable Python 3.11 runtime on Render |
| `CORS_ORIGINS` | `*` | Allows browser requests from your Vercel frontend |
| `GEMINI_MODEL` | `gemini-3.8-flash` | LLM model for Floor briefing & "Why flagged" |
| `GEMINI_API_KEY` | *(Optional)* | Your Google AI Studio API key |
| `SUPABASE_URL` | *(Optional)* | Supabase project URL (leave blank for in-memory) |
| `SUPABASE_KEY` | *(Optional)* | Supabase anon/service key |

5. Set **Health Check Path** to `/health`.
6. Click **Create Web Service**.

### Verify Backend Health
Once deployed, open:
- `https://<your-render-service>.onrender.com/health` → should return `{"status":"ok"}`
- `https://<your-render-service>.onrender.com/docs` → interactive Swagger API documentation

> [!NOTE]
> **Render Free Tier Cold Starts**: Render's free services spin down after 15 minutes of inactivity. When you visit the site after it has been idle, the first request may take 30–50 seconds to boot up. Subsequent requests are fast.

---

## Part 2: Deploy Frontend to Vercel (Free Tier)

Vercel natively supports Next.js with automatic SSL and global CDN edge routing.

### Step-by-Step Vercel Setup

1. Sign up or log in to [Vercel](https://vercel.com).
2. Click **Add New…** → **Project**.
3. Import your `Vortex_Scout` GitHub repository.
4. In the **Configure Project** screen:
   - **Framework Preset**: `Next.js` (detected automatically)
   - **Root Directory**: Click **Edit** and select `frontend` *(Crucial step!)*
   - Leave Build and Output Settings as default (`npm run build`).
5. Expand **Environment Variables** and add:

| Name | Value | Note |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<your-render-backend>.onrender.com` | Use your live Render URL from Part 1 (no trailing slash needed) |

6. Click **Deploy**.
7. Vercel will build and assign a production URL (e.g. `https://vortex-scout.vercel.app`).

---

## Part 3: Verify the Live Cloud Application

Test the live end-to-end flow directly in the browser:

1. **Simulation Hub (`/simulate`)**:
   - Navigate to `https://<your-vercel-domain>/simulate`.
   - Click **"Simulate Phantom Stockout (Bay 3B)"** → verifies write to backend state.
   - Click **"Run Scout Detection & Trigger Agent"** → baseline ML detector runs and flags the phantom void.
2. **Floor App (`/floor`)**:
   - Navigate to `/floor` (or emulate mobile view).
   - Verify the flagged item appears with AI reason and bay number.
   - Tap **"Restocked"** → status changes, count increments, audit log entry is saved.
3. **Manager Dashboard (`/dashboard`)**:
   - Navigate to `/dashboard`.
   - Confirm active void KPI counters, velocity charts, and the recent reconciliation feed update in real time.
4. **Evaluation Engine (`/evaluation`)**:
   - Navigate to `/evaluation`.
   - Run the benchmark evaluation and view the ROC / Confusion Matrix metrics proving Scout's 96%+ accuracy.

---

## Part 4: Production Checklist & Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| Frontend displays "Failed to fetch" on first visit | Render backend is cold-starting | Wait 30 seconds for Render container to wake up, or ping `/health` |
| CORS error in browser console | Backend `CORS_ORIGINS` mismatch | In Render environment variables, verify `CORS_ORIGINS` is set to `*` or your Vercel URL |
| Monorepo build error on Vercel | Root Directory not set to `frontend` | Go to Project Settings → General → Root Directory → set to `frontend` and redeploy |
| Supabase connection error | Invalid credentials or blank | Leave both `SUPABASE_URL` and `SUPABASE_KEY` empty to run on the zero-config in-memory store |
