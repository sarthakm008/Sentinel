# Architecture

## Overview

```text
                     SENTINEL
                        |
          +-----------+-----------+
          |           |           |
       Frontend    Backend     ML Service
        React      FastAPI      Python
          |           |           |
          +-----------+-----------+
                        |
                     Database
                  SQLite (dev) / PostgreSQL (prod)
```

## Stack

| Area | Choice |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI |
| ML | scikit-learn, XGBoost/HistGBM |
| Graph | NetworkX |
| Database | SQLite (dev), PostgreSQL (Docker) |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Testing | pytest |

## Design Decisions

- SQLite used for Phase 0 development; PostgreSQL via Docker Compose when available.
- XGBoost preferred for gradient boosting; sklearn HistGBM as fallback.
