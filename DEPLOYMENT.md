# Sentinel Deployment Guide

## Overview

Sentinel consists of two deployable components:
- **Frontend**: React/Vite SPA → Deploy to **Vercel**
- **Backend**: FastAPI + Uvicorn → Deploy to **Render Web Service**

---

## Architecture Overview

```
┌─────────────────┐     HTTPS      ┌─────────────────┐
│   Frontend      │ ◄────────────► │   Backend       │
│   (Vercel)      │   API Calls    │  (Render)       │
│                 │                │                 │
│ React/Vite      │                │  FastAPI        │
│ Static Files    │                │  ML Inference   │
└─────────────────┘                └────────┬────────┘
                                             │
                                ┌────────────┴────────┐
                                │  Supabase PostgreSQL │
                                │  (Session Pooler)   │
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
| `DATABASE_URL` | `postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres` | Supabase Session Pooler connection string (use `postgresql+psycopg://` driver) |
| `RANDOM_SEED` | `42` | ML reproducibility |
| `DATA_DIR` | `./data` | Raw data directory |
| `ARTIFACTS_DIR` | `./artifacts` | Model artifacts directory |
| `FRONTEND_ORIGIN` | `https://your-frontend.vercel.app` | **Set after Step 3** — Vercel frontend URL for CORS |
| `RAZORPAY_WEBHOOK_SECRET` | `<generated-secret>` | **Required for webhook** — Generate with `openssl rand -hex 32` |
| `PYTHON_VERSION` | `3.11` | Optional, but recommended |

### 1.4 PostgreSQL Database Provisioning (Supabase)

**Provision a Supabase PostgreSQL database** before deploying the backend:

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Go to **Settings** → **Database** → **Connection pooling**
3. Enable **Session Pooler** (port 5432)
4. Note the connection string format:
   ```
   postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```
5. Set this as `DATABASE_URL` in Render environment variables

**Important**: Use the **Session Pooler** (not Transaction Pooler) on port 5432. The application uses `psycopg v3` with `prepare_threshold=0` to avoid prepared statement caching issues with PgBouncer.

**Alternative**: You can also use Render PostgreSQL, Neon, AWS RDS, or any managed PostgreSQL service. The connection string format will vary.

**Note**: No persistent disk is required for PostgreSQL - the database is hosted externally.

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
| `DATABASE_URL` | Yes | - | Supabase Session Pooler connection string (e.g., `postgresql+psycopg://postgres.<ref>:<pwd>@aws-0-<region>.pooler.supabase.com:5432/postgres`) |
| `PORT` | Auto | Set by Render | Port to bind (provided by Render) |
| `RANDOM_SEED` | No | `42` | ML reproducibility |
| `DATA_DIR` | No | `./data` | Raw data directory |
| `ARTIFACTS_DIR` | No | `./artifacts` | Model artifacts directory |
| `FRONTEND_ORIGIN` | **Yes (prod)** | - | Vercel frontend URL for CORS (e.g., `https://your-frontend.vercel.app`) |
| `BACKEND_RELOAD` | No | `false` | Disable in production |
| `RAZORPAY_WEBHOOK_SECRET` | **Yes (webhook)** | - | Secret for HMAC-SHA256 webhook verification. Generate with `openssl rand -hex 32` |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE` | **Yes** | Backend API URL including `/api` suffix (e.g., `https://api.onrender.com/api`) |

---

## Razorpay Webhook Configuration

### 1. Configure Webhook in Razorpay Dashboard

1. Log in to [Razorpay Dashboard](https://dashboard.razorpay.com)
2. Navigate to **Settings** → **Webhooks**
2. Click **Add New Webhook**
3. **Webhook URL**: `https://<your-render-backend>.onrender.com/api/webhooks/razorpay`
   - Replace `<your-render-backend>` with your actual Render service name
   - Must use HTTPS (port 443)
4. **Secret**: Generate a secure secret:
   ```bash
   openssl rand -hex 32
   ```
   Copy this value - you'll need it for the `RAZORPAY_WEBHOOK_SECRET` environment variable
5. **Events**: Select **refund.created** (only this event is processed for scoring)
6. Click **Create Webhook**

### 2. Configure Environment Variable on Render

Add `RAZORPAY_WEBHOOK_SECRET` to your Render backend environment variables with the secret you generated above.

**Important**: 
- Never expose this secret to the frontend/Vercel
- Store only in Render backend environment variables
- If you rotate the secret, keep the old one for 24h to handle retries

### 3. Verify Webhook Delivery

Test locally:
```bash
cd sentinel
RAZORPAY_WEBHOOK_SECRET=your_secret python scripts/test_webhook.py --host localhost --port 8000
```

Or test against deployed backend:
```bash
RAZORPAY_WEBHOOK_SECRET=your_secret python scripts/test_webhook.py --host sentinel-api.onrender.com --port 443
```

### 4. Razorpay Webhook Requirements

- **HTTPS required**: Webhook URL must use HTTPS (port 443)
- **Response time**: Must return 2xx within 5 seconds
- **Retries**: Razorpay retries failed deliveries with exponential backoff for 24 hours
- **IP Whitelist**: Ensure [Razorpay webhook IPs](https://razorpay.com/docs/security/whitelists#webhook-ips) are allowed through any firewall/WAF
- **At-least-once delivery**: Handle duplicate deliveries using `x-razorpay-event-id` header

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

---

## Important Notes

### Database Support

**Production**: PostgreSQL via Supabase Session Pooler (or any managed PostgreSQL) is the required production database. SQLite is only supported for local development.

**Local Development (SQLite)**:
```bash
DATABASE_URL=sqlite:///./sentinel.db
```

**Production (PostgreSQL / Supabase Session Pooler)**:
```bash
DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

The application automatically detects the database type from `DATABASE_URL` and configures appropriately:
- For PostgreSQL: Sets `prepare_threshold=0` to avoid PgBouncer prepared statement issues
- For SQLite: Sets `check_same_thread=False` for FastAPI async usage

### PostgreSQL on Render with Supabase

When deploying to Render with Supabase PostgreSQL:
- Provision a Supabase project and enable Session Pooler (port 5432)
- Set `DATABASE_URL` to the Supabase Session Pooler connection string
- Use `postgresql+psycopg://` driver (psycopg v3)
- No persistent disk required for the database

### Bundled Assets

The following are **bundled in the repository/deployment** (not downloaded at runtime):
- `data/raw/*.parquet` - Raw synthetic benchmark data
- `data/processed/*.parquet` - Pre-computed feature matrices  
- `data/splits/*.json` - Train/val/test split manifests
- `artifacts/models/sentinel_model.joblib` - Frozen 39-feature production model
- `artifacts/metrics/threshold.json` - Frozen threshold (0.41)

### Queue Monitor Limitation

The background queue monitor runs **in-process** within the FastAPI application (started via lifespan). This design works for single-worker deployments (Render Free/Starter tiers). 

**Limitation**: If you scale to multiple workers or processes, each worker runs its own queue monitor instance polling the same database queue. This can lead to duplicate processing or race conditions. For multi-worker deployments, consider:
- Running the queue monitor as a separate service (e.g., Render Background Worker)
- Using a distributed task queue (Redis/RQ, Celery)
- Implementing PostgreSQL advisory locks or `SELECT ... FOR UPDATE SKIP LOCKED`

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