"""Sentinel Backend — FastAPI Application."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file before any other imports
# This must happen before any modules that read env vars at import time
# Only load if DATABASE_URL is not already set (preserves test env var precedence)
if "DATABASE_URL" not in os.environ:
    load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.api.risk import router as risk_router
from backend.app.api.cases import router as cases_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.demo import router as demo_router
from backend.app.api.events import router as events_router
from backend.app.api.integration import router as integration_router
from backend.app.api.webhooks import router as webhooks_router
from backend.app.models.base import engine
from backend.app.models.risk_case import Base as RiskCaseBase
from backend.app.models.webhook import Base as WebhookBase
from backend.app.services.queue_monitor import start_queue_monitor, stop_queue_monitor
import os


def _get_cors_origins() -> list:
    """Get CORS origins from environment variable or use defaults for local development."""
    frontend_origin = os.getenv("FRONTEND_ORIGIN")
    if frontend_origin:
        return [frontend_origin]
    # Default to localhost for development
    return ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    RiskCaseBase.metadata.create_all(bind=engine)
    WebhookBase.metadata.create_all(bind=engine)
    # Pre-warm ML service
    from backend.app.services.ml_service import get_inference_service
    get_inference_service()
    # Start queue monitor
    from backend.app.services.queue_monitor import start_queue_monitor
    await start_queue_monitor()
    yield
    # Shutdown
    from backend.app.services.queue_monitor import stop_queue_monitor
    await stop_queue_monitor()


def _get_cors_origins() -> list:
    """Get CORS origins from environment variable or use defaults for local development."""
    frontend_origin = os.getenv("FRONTEND_ORIGIN")
    if frontend_origin:
        return [frontend_origin]
    # Default to localhost for development
    return ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]


app = FastAPI(
    title="Sentinel",
    description="AI-Powered Coordinated Refund Abuse Detection",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and configured production origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(integration_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")