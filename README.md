# Sentinel

**AI-Powered Coordinated Refund Abuse Detection**

> *Razorpay AI Buildathon 2026 — Track 02: AI Risk Manager*

## Problem

A refund request that looks normal in isolation can become suspicious when considered alongside related customers, shared devices, shared addresses, shared payment tokens, correlated transaction behavior, and synchronized refund activity.

Sentinel is a **merchant risk layer** around a refund workflow that converts relationship and temporal signals into risk scores, cases, evidence, estimated exposure, and recommended actions.

## Architecture

```text
Frontend (React + Vite) → Backend (FastAPI) → ML Service (Python)
                                    ↓
                              Database (SQLite dev / PostgreSQL prod)
```

See [docs/architecture.md](docs/architecture.md) for details.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 22+
- npm 10+

### Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..

# Run all tests
python -m pytest ml/tests/ backend/tests/ -v
```

### Development

```bash
# Terminal 1: Backend (starts on http://localhost:8000)
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Frontend (starts on http://localhost:5173)
cd frontend && npm run dev
```

### Verify

```bash
# Health check
curl http://localhost:8000/api/health
# → {"status": "ok"}

# Score a refund (uses real test set refund)
curl -X POST http://localhost:8000/api/risk/score \
  -H "Content-Type: application/json" \
  -d '{"refund_id": "REF_0000001"}'

# List cases
curl http://localhost:8000/api/cases

# Get evaluation metrics
curl http://localhost:8000/api/evaluation

# Run demo scenario
curl -X POST http://localhost:8000/api/demo/run
```

## Project Status

| Phase | Description | Status |
|---|---|---|
| 0 | Repository & environment | ✅ Complete |
| 1 | Synthetic world generation | ✅ Complete |
| 2 | Behavioral baseline | ✅ Complete |
| 3 | Graph intelligence | ✅ Complete |
| 4 | Temporal intelligence | ✅ Complete |
| 5 | Adversarial evaluation (Phase 5: STOP) | ✅ Complete |
| 6 | Risk API | ✅ Complete |
| 7 | Dashboard | ✅ Complete |
| 8 | Investigator (structured evidence only) | ✅ Complete |
| 9 | Demo mode | ✅ Complete |
| 10 | Final audit | 🔧 In progress |

## ML Approach

- **Baseline:** Behavioral + transaction features only (XGBoost)
- **Sentinel (Production):** 39 features — Behavioral (18) + Graph (15) + Temporal (6)
- **Evaluation:** Group-aware splits, no customer/ring leakage, PR-AUC, financial cost model
- **Ablation:** Behavioral only → + Graph → + Temporal

## Key Results (Held-Out Test Set)

| Model | PR-AUC | ROC-AUC | Precision | Recall | F1 | Loss Avoided vs Baseline |
|---|---|---|---|---|---|---|
| **Behavioral Baseline** | 0.3053 | 0.7460 | 0.2351 | 0.7453 | 0.3575 | — |
| **Graph-Enhanced** | 0.4501 | 0.7983 | 0.3056 | 0.6915 | 0.4239 | +₹64,301 |
| **Temporal-Enhanced** | 0.4059 | 0.8039 | 0.2579 | 0.8427 | 0.3950 | +₹317,864 |
| **Full Sentinel (Production)** | **0.4493** | **0.7993** | **0.3179** | **0.6444** | **0.4257** | -₹34,385 |

### Out-of-Distribution: Ring Type F (Structural Shift)
| Model | PR-AUC | Precision | Recall | F1 |
|---|---|---|---|---|
| Baseline | 0.3604 | 0.2922 | 0.7226 | 0.4162 |
| Graph-Enhanced | 0.4909 | 0.4140 | 0.6062 | 0.4920 |
| **Full Sentinel** | **0.4731** | **0.4191** | **0.5325** | **0.4691** |

### Phase 5: Graph-Temporal Interaction Experiment (REJECTED)
- **Feature:** `graph_neighbor_synchronized_refund_ratio_1h`
- **ΔPR-AUC:** +0.0004
- **95% CI:** [-0.0089, 0.0097]
- **Decision:** STOP — CI includes zero, not statistically significant
- **Result:** Feature NOT deployed. Production remains 39-feature Sentinel.

## Demo Flow

1. **Start backend:** `python -m uvicorn backend.app.main:app --reload --port 8000`
2. **Start frontend:** `cd frontend && npm run dev`
3. **Open dashboard:** http://localhost:5173
4. **Click "Run Demo Scenario"** — scores 5 real test-set refunds
5. **View cases** — shows LOW to HIGH risk bands with evidence
6. **Click a case** — see behavioral, graph, temporal evidence + network graph
7. **Make a decision** — approve/verify/review/hold
8. **View Evaluation page** — ablation, Type F, future holdout, Phase 5 STOP

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/risk/score` | POST | Score a refund event |
| `/api/cases` | GET | List cases (with filters) |
| `/api/cases/{id}` | GET | Get case detail with evidence |
| `/api/cases/{id}/graph` | GET | Get PIT-correct network subgraph |
| `/api/cases/{id}/decision` | POST | Record merchant decision |
| `/api/evaluation` | GET | Full evaluation metrics |
| `/api/demo/scenario` | GET | Demo configuration |
| `/api/demo/run` | POST | Run demo scenario |
| `/api/demo/reset` | POST | Reset demo state |

## Risk Decision Semantics

| Action | Risk Band | Threshold Range | Merchant Meaning |
|---|---|---|---|
| `approve` | LOW | < 0.205 | Process refund normally |
| `verify` | MEDIUM | 0.205 – 0.41 | Request additional info (OTP, photo) |
| `review` | HIGH | 0.41 – 0.705 | Queue for manual fraud team review |
| `hold` | CRITICAL | ≥ 0.705 | Block refund pending investigation |

**Threshold:** Frozen at 0.41 (validation-selected cost-minimizing)

## Evidence Categories

Every evidence item maps to an actual 39-feature production model feature:

- **Behavioral:** refund rate, recent refunds, amount ratio, refund delay
- **Graph:** shared devices/addresses/payments, component size, neighbor refund rates, entity rarity, component growth
- **Temporal:** cluster event counts, synchronized refund ratio, account creation burst, inter-event delay

## Limitations

- All data is synthetic. Results do not represent production performance.
- Prototype economic assumptions are illustrative, not real Razorpay economics.
- The LLM investigator explains structured evidence — it is not the classifier.
- SQLite used for local development; PostgreSQL recommended for production.

## Reproducibility

- Dataset seed: 42 (fixed)
- Train/val/test splits: group-aware, immutable
- Model hyperparameters: frozen (XGBoost, 200 estimators, max_depth=5, lr=0.05)
- Thresholds: frozen on validation set only
- All artifacts in `artifacts/` are reproducible from code

## Directory Structure

```
sentinel/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic (ML inference)
│   └── tests/              # Integration tests
├── frontend/               # React + Vite application
│   └── src/
│       ├── api/            # API client
│       ├── components/     # React components
│       ├── pages/          # Page components
│       └── types/          # TypeScript types
├── ml/                     # ML pipeline
│   ├── features/           # Feature extraction (PIT-correct)
│   ├── graph/              # Graph feature computations
│   ├── models/             # Model training & wrapper
│   ├── evaluation/         # Evaluation, thresholds, cost model
│   ├── scripts/            # CLI scripts (train, evaluate, demo)
│   └── tests/              # 63 ML tests
├── data/                   # Synthetic benchmark (immutable)
│   ├── raw/                # Parquet tables
│   ├── processed/          # Cached feature matrices
│   └── splits/             # Group-aware split manifests
├── artifacts/              # Reproducible outputs
│   ├── models/             # Trained model artifacts
│   ├── metrics/            # JSON metrics (ablation, thresholds)
│   ├── plots/              # PR/ROC curves, ablation bars
│   └── reports/            # Markdown evaluation summary
├── docs/                   # Documentation
├── scripts/                # Shell scripts
└── requirements.txt        # Python dependencies
```

## License

MIT — see [LICENSE](LICENSE).