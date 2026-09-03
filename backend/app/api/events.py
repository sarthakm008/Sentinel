"""Refund event ingestion API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.schemas.risk import (
    RefundEventRequest,
    RefundEventResponse,
    EvidenceItem,
)
from backend.app.models.base import get_db
from backend.app.models.risk_case import RiskCase, CaseEvidence
from backend.app.services.ml_service import get_inference_service

router = APIRouter(prefix="/events", tags=["events"])


def _persist_case(db: Session, result: dict) -> RiskCase:
    """Persist a risk case from inference result. Returns the created case."""
    case = RiskCase(
        customer_id=result["customer_id"],
        refund_id=result["refund_id"],
        order_id=result["order_id"],
        risk_score=result["risk_score"],
        risk_band=result["risk_band"],
        recommended_action=result["recommended_action"],
        status="pending",
    )
    db.add(case)
    db.flush()

    for ev in result["evidence"]:
        case_evidence = CaseEvidence(
            case_id=case.id,
            category=ev["category"],
            metric=ev["metric"],
            value=str(ev["value"]),
            description=ev["description"],
        )
        db.add(case_evidence)

    db.commit()
    db.refresh(case)
    return case


@router.post("/refund", response_model=RefundEventResponse, status_code=status.HTTP_201_CREATED)
async def ingest_refund(
    request: RefundEventRequest,
    db: Session = Depends(get_db),
):
    """
    Ingest a merchant refund event and score it with Sentinel.

    This endpoint:
    1. Validates the incoming refund event
    2. Checks for duplicate refund_id
    3. Scores the event using the existing 39-feature production model
    4. Applies the frozen threshold and ActionPolicy
    5. Generates structured evidence
    6. Persists a risk case
    7. Returns the risk assessment and case details

    The inference uses the exact same PIT-correct feature extraction
    and 39-feature Sentinel model as the existing /api/risk/score endpoint.
    """
    service = get_inference_service()

    # Check for duplicate refund_id in existing cases
    existing_case = db.query(RiskCase).filter(RiskCase.refund_id == request.refund_id).first()
    if existing_case:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Refund {request.refund_id} already processed (case #{existing_case.id})",
        )

    # Validate that the refund exists in our historical data
    # The inference service looks up the full event from parquet files
    result = service.score_refund(request.refund_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Refund {request.refund_id} not found in historical data. "
                   f"Ensure the refund_id exists in the benchmark dataset.",
        )

    # Optionally validate that the provided identifiers match the historical record
    if request.customer_id != result["customer_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer ID mismatch: historical record has {result['customer_id']}, "
                   f"request has {request.customer_id}",
        )
    if request.order_id != result["order_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order ID mismatch: historical record has {result['order_id']}, "
                   f"request has {request.order_id}",
        )

    # Persist the case
    case = _persist_case(db, result)

    return RefundEventResponse(
        refund_id=result["refund_id"],
        customer_id=result["customer_id"],
        order_id=result["order_id"],
        risk_score=result["risk_score"],
        risk_band=result["risk_band"],
        recommended_action=result["recommended_action"],
        threshold=result["threshold"],
        evidence=[EvidenceItem(**ev) for ev in result["evidence"]],
        case_id=case.id,
        created_at=case.created_at,
    )


@router.get("/refund/{refund_id}/status", response_model=dict)
async def get_refund_status(
    refund_id: str,
    db: Session = Depends(get_db),
):
    """Check if a refund has been processed and get its case status."""
    case = db.query(RiskCase).filter(RiskCase.refund_id == refund_id).first()
    if not case:
        return {"processed": False, "refund_id": refund_id}

    return {
        "processed": True,
        "refund_id": refund_id,
        "case_id": case.id,
        "risk_score": case.risk_score,
        "risk_band": case.risk_band,
        "recommended_action": case.recommended_action,
        "status": case.status,
        "created_at": case.created_at.isoformat() if case.created_at else None,
    }