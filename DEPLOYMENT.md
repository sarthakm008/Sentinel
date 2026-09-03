# Sentinel Deployment Guide

## Overview

Sentinel consists of two deployable components:
- **Frontend**: React/Vite SPA → Deploy to **Vercel**
- **Backend**: FastAPI + Uvicorn → Deploy to **Render Free Web Service**

---

## Architecture Overview

```
┌─────────────────┐     HTTPS      ┌─────────────────┐
│   Frontend      │ ◄────────────► │   Backend       │
│   (Vercel)      │   API Calls    │  (Render Free)  │
│                 │                │                 │
│ React/Vite      │                │  FastAPI        │
│ Static Files    │                │  SQLite + ML    │
└─────────────────┘                └────────┬────────┘
                                            │
                               ┌────────────┴────────┐
                               │   SQLite Database   │
                               │   (Ephemeral on     │
                               │   Render Free)      │
                               └─────────────────────┘
```

---

## Step 1: Deploy Backend to Render

### 1.1 Prepare Repository

Ensure these directories are committed (not in `.gitignore`):
- `data/` - Raw and processed benchmark data
- `artifacts/` - Trained models and metrics

### 1.2 Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `sentinel-api` (or your choice)
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your default branch)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m backend.run`
   - **Root Directory**: (repository root)

### 1.3 Configure Environment Variables

Add these environment variables in Render dashboard:

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | `sqlite:///./data/sentinel.db` | SQLite file in persistent disk |
| `RANDOM_SEED` | `42` | ML reproducibility |
| `DATA_DIR` | `./data` | Raw data directory |
| `ARTIFACTS_DIR` | `./artifacts` | Model artifacts directory |
| `FRONTEND_ORIGIN` | `https://your-frontend.vercel.app` | **Set after Step 3** |
| `PYTHON_VERSION` | `3.11.0` | Optional, but recommended |

### 1.4 Add Persistent Disk (Required for SQLite)

1. In Render service settings, go to **Disks**
2. Click **Add Disk**
   - **Name**: `sentinel-data`
   - **Mount Path**: `/app/data` (or just `/app` if using root)
   - **Size**: 1 GB (minimum for free tier)

**Important**: The SQLite database is stored on this disk. On Render Free tier, the disk persists across deploys but **not** across service restarts due to inactivity. Treat SQLite state as ephemeral demo/runtime data.

### 1.5 Deploy Backend

Click **Create Web Service**. Render will:
1. Install dependencies from `requirements.txt`
2. Start the server with `python -m backend.run`
3. Provide a URL like `https://sentinel-api.onrender.com`

---

## Step 2: Obtain Backend URL

Once deployed, note your backend URL:
```
https://sentinel-api.onrender.com
```

Test it:
```bash
curl https://sentinel-api.onrender.com/api/health
# Should return: {"status":"ok"}
```

---

## Step 3: Deploy Frontend to Vercel

### 3.1 Prepare Vercel Configuration

The `vercel.json` file is already created in `frontend/vercel.json`:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### 3.2 Create Vercel Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### 3.2 Configure Environment Variables

In Vercel project settings → **Environment Variables**:

| Variable | Value | Environment |
|----------|-------|-------------|
| `VITE_API_BASE` | `https://your-render-url.onrender.com/api` | Production |
| `VITE_API_BASE` | `http://localhost:8000/api` | Development (optional) |

### 3.3 Deploy Frontend

Click **Deploy**. Vercel will:
1. Run `npm install`
2. Run `npm run build` (outputs to `dist/`)
3. Deploy static files to global CDN
4. Provide URL like `https://sentinel-frontend.vercel.app`

---

## Step 4: Connect Frontend to Backend

1. Copy your Render backend URL (e.g., `https://sentinel-api.onrender.com`)
2. In Vercel project settings → **Environment Variables**
3. Set `VITE_API_BASE` = `https://sentinel-api.onrender.com/api`
4. Redeploy frontend (Vercel auto-redeploys on env var change)

---

## Step 5: Verify End-to-End

1. Open your Vercel URL (e.g., `https://sentinel-frontend.vercel.app`)
2. Verify dashboard loads
3. Click **"Run Demo Scenario"** - should create 5 cases
4. Click a case → verify **Evidence**, **Graph**, **Timeline**, **Decision** tabs
5. Test `/api/health` on Render URL

---

## Required Environment Variables Summary

### Backend (Render)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///./data/sentinel.db` | SQLite path |
| `PORT` | Auto | Set by Render | Port to bind (provided by Render) |
| `RANDOM_SEED` | No | `42` | ML reproducibility |
| `DATA_DIR` | No | `./data` | Raw data directory |
| `ARTIFACTS_DIR` | No | `./artifacts` | Model artifacts directory |
| `FRONTEND_ORIGIN` | **Yes (prod)** | - | Vercel frontend URL for CORS |
| `BACKEND_RELOAD` | No | `false` | Disable in production |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE` | **Yes** | Backend API URL (e.g., `https://api.onrender.com/api`) |

---

## Local Development

### Backend
```bash
# Terminal 1
cd sentinel
python -m uvicorn backend.app.main:app --reload --port 8000
# Or using the entry point:
python -m backend.run
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens http://localhost:5173
```

### Full Local Stack
```bash
# Terminal 1: Backend
python -m backend.run

# Terminal 2: Frontend  
cd frontend && npm run dev
```

---

## Important Notes

### SQLite on Render Free Tier

**⚠️ IMPORTANT**: Render Free tier provides an **ephemeral filesystem**. 
- The SQLite database (`sentinel.db`) is stored on the persistent disk
- **However**: The disk is only attached when the service is running
- After ~15 minutes of inactivity, Render spins down the service
- On restart, the disk is re-attached but **SQLite state persists** (it's on the disk)
- **Exception**: If Render migrates your service to a new host, the disk may be recreated
- **Treat all SQLite state as ephemeral demo/runtime state** — cases, queue, decisions may reset

### Bundled Assets

The following are **bundled in the repository/deployment** (not downloaded at runtime):
- `data/raw/*.parquet` - Raw synthetic benchmark data
- `data/processed/*.parquet` - Pre-computed feature matrices  
- `data/splits/*.json` - Train/val/test split manifests
- `artifacts/models/sentinel_model.joblib` - Frozen 39-feature production model
- `artifacts/metrics/threshold.json` - Frozen threshold (0.41)

### Health Check

```bash
curl https://your-api.onrender.com/api/health
# {"status":"ok"}
```

---

## Verification Checklist

After deployment, verify:

- [ ] `GET /api/health` → `{"status":"ok"}`
- [ ] `POST /api/risk/score` with valid `refund_id` → returns risk score
- [ ] `GET /api/cases` → returns list of cases
- [ ] `GET /api/cases/{id}/graph` → returns graph nodes/edges
- [ ] `GET /api/cases/{id}/timeline` → returns timeline events
- [ ] `GET /api/evaluation` → returns all evaluation metrics
- [ ] `POST /api/demo/run` → creates 5 cases via queue
- [ ] Dashboard shows "Connected" and "Active" status
- [ ] "Send Test Refund" creates case via queue
- [ ] Frontend loads on Vercel URL
- [ ] Frontend correctly calls Render backend API

---

## Local Verification Before Deploy

```bash
# 1. Backend tests
cd sentinel
python -m pytest ml/tests/ backend/tests/ -v

# 2. Frontend build
cd frontend
npm run build

# 3. Local integration test
# Terminal 1: python -m backend.run
# Terminal 2: cd frontend && npm run dev
# Open http://localhost:5173
# Click "Run Demo Scenario" → verify cases created
# Click a case → verify graph, timeline, evidence
```

---

## Summary: Files Changed for Deployment

### New Files
- `backend/run.py` - Entry point reading PORT from env
- `frontend/vercel.json` - Vercel SPA routing config

### Modified Files
- `backend/app/main.py` - Configurable CORS, PORT from env
- `backend/app/services/ml_service.py` - Absolute paths via project root
- `.env.example` - Added deployment variables
- `frontend/vercel.json` - Vercel SPA routing
- `.env.example` - Updated with deployment variables
- `README.md` - Updated deployment section (to be updated)
- `DEPLOYMENT.md` - This file (new)

---

## Render Configuration Summary

| Setting | Value |
|---------|-------|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python -m backend.run` |
| **Root Directory** | Repository root |
| **Python Version** | 3.11 (recommended) |
| **Disk** | 1 GB, mount at `/app/data` |
| **Health Check** | `GET /api/health` |
| **Auto-Deploy** | Yes (on push to main) |

---

## Vercel Configuration Summary

| Setting | Value |
|---------|-------|
| Framework | Vite |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm install` |
| SPA Fallback | Configured in `vercel.json` |

---

## Quick Start Commands

```bash
# Backend (local)
python -m backend.run

# Frontend (local)
cd frontend && npm run dev

# Frontend build (for Vercel)
cd frontend && npm run build

# Backend tests
python -m pytest backend/tests/ -v

# ML tests
python -m pytest ml/tests/ -v

# All tests
python -m pytest ml/tests/ backend/tests/ -v
```

---

## Explicit Confirmation

> **No code was deployed or pushed remotely.** All changes are local to the repository. The deployment process requires manual steps in Render and Vercel dashboards as outlined above.