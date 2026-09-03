"""Cases API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from backend.app.schemas.risk import (
    CaseResponse,
    DecisionRequest,
    DecisionResponse,
    EvidenceItem,
    GraphResponse,
    TimelineResponse,
)
from backend.app.models.base import get_db
from backend.app.models.risk_case import RiskCase, CaseDecision, CaseEvidence
from backend.app.services.ml_service import get_inference_service

router = APIRouter(prefix="/cases", tags=["cases"])


def _case_to_response(case: RiskCase) -> CaseResponse:
    """Convert RiskCase ORM to CaseResponse schema with evidence conversion."""
    evidence_items = [
        EvidenceItem(
            category=ev.category,
            metric=ev.metric,
            value=ev.value,
            description=ev.description,
        )
        for ev in case.evidence
    ]
    return CaseResponse(
        id=case.id,
        customer_id=case.customer_id,
        refund_id=case.refund_id,
        order_id=case.order_id,
        risk_score=case.risk_score,
        risk_band=case.risk_band,
        recommended_action=case.recommended_action,
        status=case.status,
        decision=case.decision,
        created_at=case.created_at,
        decided_at=case.decided_at,
        evidence=evidence_items,
    )


@router.get("", response_model=dict)
async def list_cases(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status: pending, decided"),
    band: Optional[str] = Query(None, description="Filter by risk band: LOW, MEDIUM, HIGH, CRITICAL"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """List risk cases with optional filters and pagination."""
    query = db.query(RiskCase)

    if status:
        query = query.filter(RiskCase.status == status)
    if band:
        query = query.filter(RiskCase.risk_band == band)

    total = query.count()
    cases = query.order_by(desc(RiskCase.created_at)).offset((page - 1) * size).limit(size).all()

    return {
        "cases": [_case_to_response(c) for c in cases],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    db: Session = Depends(get_db),
):
    """Get full case detail with evidence."""
    case = db.query(RiskCase).filter(RiskCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    return _case_to_response(case)


@router.post("/{case_id}/decision", response_model=DecisionResponse)
async def record_decision(
    case_id: int,
    request: DecisionRequest,
    db: Session = Depends(get_db),
):
    """Record a merchant decision on a risk case."""
    valid_decisions = ["approve", "verify", "review", "hold"]
    if request.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision. Must be one of: {valid_decisions}"
        )

    case = db.query(RiskCase).filter(RiskCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    # Record decision
    decision = CaseDecision(
        case_id=case_id,
        decision=request.decision,
        user_id="merchant",  # In real system, get from auth
    )
    db.add(decision)

    # Update case
    case.status = "decided"
    case.decision = request.decision
    case.decided_at = datetime.utcnow()

    db.commit()

    return DecisionResponse(
        success=True,
        case_id=case_id,
        decision=request.decision,
        timestamp=decision.timestamp,
    )


@router.get("/{case_id}/graph", response_model=GraphResponse)
async def get_case_graph(
    case_id: int,
    db: Session = Depends(get_db),
):
    """Get PIT-correct network subgraph for a risk case."""
    case = db.query(RiskCase).filter(RiskCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    service = get_inference_service()
    graph = service.get_graph_subgraph(case.refund_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"Could not build graph for refund {case.refund_id}")

    return GraphResponse(**graph)


@router.get("/{case_id}/timeline", response_model=TimelineResponse)
async def get_case_timeline(
    case_id: int,
    db: Session = Depends(get_db),
    window_hours: int = Query(48, ge=1, le=168),
):
    """Get PIT-correct timeline events for a risk case's connected component."""
    case = db.query(RiskCase).filter(RiskCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    service = get_inference_service()
    timeline = service.get_timeline_events(case.refund_id, window_hours)
    if timeline is None:
        raise HTTPException(status_code=404, detail=f"Could not build timeline for refund {case.refund_id}")

    return TimelineResponse(**timeline)