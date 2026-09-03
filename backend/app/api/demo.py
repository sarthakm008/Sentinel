"""Demo API endpoints."""

import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.app.schemas.risk import DemoScenario, DemoResetResponse
from backend.app.models.base import get_db
from backend.app.models.risk_case import RiskCase, CaseEvidence, CaseDecision
from backend.app.services.ml_service import get_inference_service
from backend.app.api.events import _persist_case
from backend.app.models.risk_case import RefundEventQueue
from backend.app.services.queue_monitor import get_queue_monitor

router = APIRouter(prefix="/demo", tags=["demo"])

# Deterministic demo scenario using REAL test set refund IDs
# These are selected from the test set to show a range of risk levels
# High risk (label=1): REF_0028458, REF_0028520, REF_0031741, REF_0031713, REF_0028822
# Low risk (label=0): REF_0025456, REF_0007580, REF_0005717, REF_0005738, REF_0006308
DEMO_REFUND_IDS = [
    "REF_0028458",  # High risk - coordinated abuse (label=1)
    "REF_0028520",  # High risk - coordinated abuse (label=1)
    "REF_0031741",  # High risk - coordinated abuse (label=1)
    "REF_0025456",  # Low risk - legitimate (label=0)
    "REF_0007580",  # Low risk - legitimate (label=0)
]


@router.get("/scenario", response_model=DemoScenario)
async def get_demo_scenario():
    """Get the deterministic demo scenario configuration."""
    return DemoScenario(
        refund_ids=DEMO_REFUND_IDS,
        description="Deterministic demo using 5 real test set refunds showing LOW to CRITICAL risk bands"
    )


@router.post("/reset", response_model=DemoResetResponse)
async def reset_demo(
    db: Session = Depends(get_db),
):
    """Reset demo state by clearing all cases and decisions."""
    # Delete in correct order due to foreign keys
    db.query(CaseDecision).delete()
    db.query(CaseEvidence).delete()
    db.query(RiskCase).delete()
    db.query(RefundEventQueue).delete()
    db.commit()

    return DemoResetResponse(
        success=True,
        message="Demo state reset. All cases, decisions, and queued events cleared."
    )


@router.post("/run", response_model=Dict[str, Any])
async def run_demo(
    db: Session = Depends(get_db),
):
    """Run the full demo scenario: process all demo refunds through the ingestion pipeline."""
    service = get_inference_service()

    # Clear existing demo data
    db.query(CaseDecision).delete()
    db.query(CaseEvidence).delete()
    db.query(RiskCase).delete()
    db.query(RefundEventQueue).delete()
    db.commit()

    results = []
    for refund_id in DEMO_REFUND_IDS:
        # Process each refund through the ingestion pipeline (synchronous for demo)
        # This mimics the /api/events/refund endpoint logic
        result = service.score_refund(refund_id)
        if not result:
            # Skip refunds not found in historical data
            continue

        # Check for duplicate (simulating the ingestion endpoint's check)
        existing_case = db.query(RiskCase).filter(RiskCase.refund_id == refund_id).first()
        if existing_case:
            results.append({
                "refund_id": refund_id,
                "case_id": existing_case.id,
                "customer_id": result["customer_id"],
                "risk_score": result["risk_score"],
                "risk_band": result["risk_band"],
                "recommended_action": result["recommended_action"],
                "evidence_count": len(result["evidence"]),
            })
            continue

        # Persist case using the same persistence logic as the ingestion endpoint
        case = _persist_case(db, result)

        results.append({
            "refund_id": refund_id,
            "case_id": case.id,
            "customer_id": result["customer_id"],
            "risk_score": result["risk_score"],
            "risk_band": result["risk_band"],
            "recommended_action": result["recommended_action"],
            "evidence_count": len(result["evidence"]),
        })

    return {
        "success": True,
        "message": f"Demo completed: {len(results)} cases created via ingestion pipeline",
        "cases": results,
    }