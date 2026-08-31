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

# Run backend tests
python -m pytest backend/tests/ -v
```

### Development

```bash
# Terminal 1: Backend
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Verify

```bash
# Health check
curl http://localhost:8000/api/health
# → {"status": "ok"}
```

## Project Status

| Phase | Description | Status |
|---|---|---|
| 0 | Repository & environment | 🔧 In progress |
| 1 | Synthetic world | ⏳ Pending |
| 2 | Behavioral baseline | ⏳ Pending |
| 3 | Graph intelligence | ⏳ Pending |
| 4 | Temporal intelligence | ⏳ Pending |
| 5 | Adversarial evaluation | ⏳ Pending |
| 6 | Risk API | ⏳ Pending |
| 7 | Dashboard | ⏳ Pending |
| 8 | Investigator | ⏳ Pending |
| 9 | Demo mode | ⏳ Pending |
| 10 | Final audit | ⏳ Pending |

## ML Approach

- **Baseline:** Behavioral + transaction features only (XGBoost / HistGBM)
- **Sentinel:** Behavioral + transaction + graph + temporal features
- **Evaluation:** Group-aware splits, no customer/ring leakage, PR-AUC, financial cost model
- **Ablation:** Behavioral only → + Graph → + Temporal

## Limitations

- All data is synthetic. Results do not represent production performance.
- Prototype economic assumptions are illustrative, not real Razorpay economics.
- The LLM investigator explains structured evidence — it is not the classifier.

## License

MIT — see [LICENSE](LICENSE).
