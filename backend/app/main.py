"""Sentinel Backend — FastAPI Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.api.risk import router as risk_router
from backend.app.api.cases import router as cases_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.demo import router as demo_router
from backend.app.models.base import engine
from backend.app.models.risk_case import Base as RiskCaseBase


app = FastAPI(
    title="Sentinel",
    description="AI-Powered Coordinated Refund Abuse Detection",
    version="0.1.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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

# Routers
app.include_router(health_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")
app.include_router(demo_router, prefix="/api")