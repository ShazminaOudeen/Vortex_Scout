# Vortex Scout — Cloud Deployment Guide

This guide walks through deploying the complete **Vortex Scout** stack using free cloud tiers:
- **Backend API**: Hosted on **Hugging Face Spaces** (100% Free · No credit card required · 16 GB RAM) or **Render**
- **Frontend App**: Hosted on **Vercel** (Free Hobby Tier)
- **Database**: In-memory demo store (Zero-config default) or **Supabase** (Free PostgreSQL tier)

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
                      │     Hugging Face Spaces (Backend)    │
                      │       FastAPI + Uvicorn + ML         │
                      │  https://<user>-vortex-scout-backend │
                      │              .hf.space               │
                      └──────────────────┬───────────────────┘
                                         │
                     ┌───────────────────┴───────────────────┐
                     ▼                                       ▼
          [In-Memory Store]                        [Supabase PostgreSQL]
        (Default, zero-config)                    (Optional persistence)
```

---

## Part 1: Deploy Backend to Hugging Face Spaces (No Credit Card)

Hugging Face Spaces runs our FastAPI container on a dedicated **16 GB RAM, 2 vCPU machine**. It never requires a credit card or billing details.

### Step 1: Create the Space on Hugging Face
1. Log in to [huggingface.co](https://huggingface.co) (sign in with GitHub or email).
2. Click your avatar (top right) → **New Space** (or visit `https://huggingface.co/new-space`).
3. Fill in the options:
   - **Space name**: `vortex-scout-backend`
   - **License**: `mit`
   - **Space SDK**: Select **Docker** → choose **Blank**
   - **Space hardware**: `Free (CPU basic · 2 vCPU · 16 GB)`
   - **Visibility**: `Public`
4. Click **Create Space**.

---

### Step 2: Push Your Code to Hugging Face
Once the Space is created, copy your Space URL shown on the screen (e.g. `https://huggingface.co/spaces/<your-username>/vortex-scout-backend`).

1. **Create an Access Token** (if you don't have one):
   - Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
   - Click **Create new token** → Name: `scout-deploy` → Type: **Write**.
   - Copy the token (`hf_...`).

2. **In your local Git Bash terminal** (at `c:\Dev-Projects\Vortex_Scout`):
   ```bash
   git remote add hf https://huggingface.co/spaces/<your-username>/vortex-scout-backend
   git push hf main
   ```
   *When prompted:*
   - Username: `<your-huggingface-username>`
   - Password: `<your-huggingface-token>` (the `hf_...` token you copied)

---

### Step 3: Obtain Your Direct API URL
Once pushed, Hugging Face will automatically build the `Dockerfile` and start the FastAPI server.
Your direct API URL follows this format:
```
https://<your-username>-vortex-scout-backend.hf.space
```
*(Notice the hyphen between username and space name, ending in `.hf.space`)*

**Verify it:**
- Open `https://<your-username>-vortex-scout-backend.hf.space/health` → returns `{"status":"ok"}`
- Open `https://<your-username>-vortex-scout-backend.hf.space/docs` → interactive Swagger documentation

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
| `NEXT_PUBLIC_API_URL` | `https://<your-username>-vortex-scout-backend.hf.space` | Use your live Hugging Face API URL from Part 1 |

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
| Hugging Face Space says `Building` or `Paused` | First time build takes ~2 minutes | Check the Space logs; once it says `Running`, it is active |
| Direct API URL returns 404 on `/` | Root path `/` redirects to docs | Test `https://<username>-<space>.hf.space/health` or `/docs` |
| CORS error in browser | Backend `CORS_ORIGINS` mismatch | The backend defaults to `*` to allow all Vercel origins |
| Monorepo build error on Vercel | Root Directory not set to `frontend` | Go to Project Settings → General → Root Directory → set to `frontend` and redeploy |
| Git push to Hugging Face rejected | Password asked instead of token | Use a Hugging Face Access Token with **Write** permission instead of your account password |
