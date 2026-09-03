"""Sentinel Backend — FastAPI Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.api.risk import router as risk_router
from backend.app.api.cases import router as cases_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.demo import router as demo_router
from backend.app.api.events import router as events_router
from backend.app.api.integration import router as integration_router
from backend.app.models.base import engine
from backend.app.models.risk_case import Base as RiskCaseBase
from backend.app.services.queue_monitor import start_queue_monitor, stop_queue_monitor
import os


def _get_cors_origins() -> list:
    """Get CORS origins from environment variable or use defaults for local development."""
    frontend_origin = os.getenv("FRONTEND_ORIGIN")
    if frontend_origin:
        return [frontend_origin]
    # Default to localhost for development
    return ["http://localhost:5173", "http://localhost:3000"]


app = FastAPI(
    title="Sentinel",
    description="AI-Powered Coordinated Refund Abuse Detection",
    version="0.1.0",
)

# CORS — allow frontend dev server and configured production origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    RiskCaseBase.metadata.create_all(bind=engine)
    # Pre-warm ML service
    from backend.app.services.ml_service import get_inference_service
    get_inference_service()
    # Start queue monitor
    from backend.app.services.queue_monitor import start_queue_monitor
    await start_queue_monitor()

@app.on_event("shutdown")
async def shutdown_event():
    from backend.app.services.queue_monitor import stop_queue_monitor
    await stop_queue_monitor()

# Routers
app.include_router(health_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(integration_router, prefix="/api")