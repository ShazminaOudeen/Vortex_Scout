# Vortex Scout — Cloud Deployment Guide

This guide details the deployment of the complete **Vortex Scout** stack:
- **Backend API**: Hosted on **Render** (Free Web Service)
- **Frontend App**: Hosted on **Vercel** (Free Hobby Tier)
- **Database**: In-memory demo store (Default, zero-configuration) or **Supabase** (Optional PostgreSQL tier)

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
                      │  https://vortex-scout-backend        │
                      │          .onrender.com               │
                      └──────────────────┬───────────────────┘
                                         │
                     ┌───────────────────┴───────────────────┐
                     ▼                                       ▼
          [In-Memory Store]                        [Supabase PostgreSQL]
        (Default, zero-config)                    (Optional persistence)
```

---

## Part 1: Deploy Backend to Render (Free Web Service)

Render provides a free Web Service tier that natively runs Python with Uvicorn.

### Step-by-Step Render Setup

1. In the [Render Dashboard](https://dashboard.render.com), click **+ New** → **Web Service**.
2. Select **Build and deploy from a Git repository** → click **Next**.
3. Select your **`Vortex_Scout`** repository and click **Connect**.
4. Configure the service settings:
   - **Name**: `vortex-scout-backend`
   - **Region**: Oregon (US West) or Frankfurt (EU)
   - **Branch**: `main`
   - **Root Directory**: `backend` *(⚠️ Make sure to enter `backend` here)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Scroll down to **Instance Type** and select **Free** ($0/month).
6. Under **Environment Variables**, click **Add Environment Variable** and add:

| Key | Value | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.11.9` | Ensures a stable Python 3.11 runtime on Render |
| `CORS_ORIGINS` | `*` | Allows browser requests from your Vercel frontend |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Gemini model for AI Floor briefing & reasons |
| `GEMINI_API_KEY` | *(Optional)* | Your Google AI Studio API key |
| `SUPABASE_URL` | *(Optional)* | Supabase URL (leave blank for in-memory) |
| `SUPABASE_KEY` | *(Optional)* | Supabase anon key (leave blank for in-memory) |

7. Set **Health Check Path** (under Advanced): `/health`
8. Click **Create Web Service**.

### Verify Backend Health
Once Render finishes building and the badge says **Live**:
- Copy your service URL (e.g. `https://vortex-scout-backend.onrender.com`).
- Open `https://<your-render-url>/health` in your browser → should return `{"status":"ok"}`.
- Open `https://<your-render-url>/docs` in your browser → interactive Swagger API documentation.

> [!NOTE]
> **Render Free Tier Cold Starts**: Render's free services sleep after 15 minutes of inactivity. When you visit the site after it has been idle, the first request may take 30–50 seconds to boot up. Subsequent requests respond immediately.

---

## Part 2: Deploy Frontend to Vercel (Free Tier)

Vercel hosts the Next.js frontend with global edge caching and automatic SSL. No credit card required.

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
| `NEXT_PUBLIC_API_URL` | `https://vortex-scout-backend.onrender.com` | Use your live Render URL from Part 1 (no trailing slash) |

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

---

## Part 4: Production Checklist & Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| Frontend displays "Failed to fetch" on first visit | Render backend is cold-starting | Wait 30 seconds for Render container to wake up, or ping `/health` |
| CORS error in browser | Backend `CORS_ORIGINS` mismatch | In Render environment variables, verify `CORS_ORIGINS` is set to `*` or your Vercel URL |
| Monorepo build error on Vercel | Root Directory not set to `frontend` | Go to Project Settings → General → Root Directory → set to `frontend` and redeploy |
| Supabase connection error | Invalid credentials or blank | Leave both `SUPABASE_URL` and `SUPABASE_KEY` empty to run on the zero-config in-memory store |
