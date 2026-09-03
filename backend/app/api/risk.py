"""Risk scoring API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.schemas.risk import (
    RiskScoreRequest,
    RiskScoreResponse,
)
from backend.app.services.ml_service import get_inference_service
from backend.app.models.base import get_db
from backend.app.models.risk_case import RiskCase, CaseEvidence

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post("/score", response_model=RiskScoreResponse)
async def score_refund(
    request: RiskScoreRequest,
    db: Session = Depends(get_db),
):
    """Score a refund event using the Sentinel production model.

    Returns risk score, band, recommended action, and structured evidence.
    """
    service = get_inference_service()

    result = service.score_refund(request.refund_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Refund {request.refund_id} not found")

    # Optionally validate customer_id and order_id match
    if request.customer_id and request.customer_id != result["customer_id"]:
        raise HTTPException(
            status_code=400,
            detail=f"Customer ID mismatch: expected {result['customer_id']}, got {request.customer_id}"
        )
    if request.order_id and request.order_id != result["order_id"]:
        raise HTTPException(
            status_code=400,
            detail=f"Order ID mismatch: expected {result['order_id']}, got {request.order_id}"
        )

    # Persist case
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
    db.flush()  # Get case ID

    # Persist evidence
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

    result["case_id"] = case.id
    return RiskScoreResponse(**result)