"""Refund event queue and integration status API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from backend.app.schemas.risk import (
    RefundEventRequest,
    RefundQueueItem,
    RefundQueueListResponse,
    IntegrationStatusResponse,
    QueueControlRequest,
    QueueControlResponse,
    RefundEventResponse,
    EvidenceItem,
    EnqueueRefundResponse,
)
from backend.app.models.base import get_db
from backend.app.models.risk_case import RefundEventQueue, RiskCase
from backend.app.services.ml_service import get_inference_service
from backend.app.services.queue_monitor import get_queue_monitor, start_queue_monitor
from backend.app.api.events import _persist_case

router = APIRouter(prefix="/integration", tags=["integration"])


def _queue_item_to_response(item: RefundEventQueue) -> RefundQueueItem:
    """Convert RefundEventQueue ORM to RefundQueueItem schema."""
    return RefundQueueItem(
        id=item.id,
        refund_id=item.refund_id,
        customer_id=item.customer_id,
        order_id=item.order_id,
        amount_inr=item.amount_inr,
        event_time=item.event_time,
        device_id=item.device_id,
        address_id=item.address_id,
        payment_token=item.payment_token,
        product_category=item.product_category,
        order_amount_inr=item.order_amount_inr,
        order_time=item.order_time,
        status=item.status,
        created_at=item.created_at,
        processed_at=item.processed_at,
        error_message=item.error_message,
    )


@router.get("/status", response_model=IntegrationStatusResponse)
async def get_integration_status():
    """Get the current integration status for merchant refund monitoring."""
    monitor = get_queue_monitor()
    stats = monitor.get_stats()
    return IntegrationStatusResponse(**stats)


@router.post("/control", response_model=QueueControlResponse)
async def control_queue_monitoring(
    request: QueueControlRequest,
):
    """Control the queue monitoring (start, stop, pause, resume)."""
    monitor = get_queue_monitor()
    action = request.action.lower()

    if action == "start":
        if not monitor.running:
            await start_queue_monitor()
        else:
            await monitor.resume()
        return QueueControlResponse(
            success=True,
            message="Queue monitoring started",
            monitoring=True,
        )
    elif action == "stop":
        if monitor.running:
            await monitor.stop()
        return QueueControlResponse(
            success=True,
            message="Queue monitoring stopped",
            monitoring=False,
        )
    elif action == "pause":
        await monitor.pause()
        return QueueControlResponse(
            success=True,
            message="Queue monitoring paused",
            monitoring=False,
        )
    elif action == "resume":
        await monitor.resume()
        return QueueControlResponse(
            success=True,
            message="Queue monitoring resumed",
            monitoring=True,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}. Valid actions: start, stop, pause, resume",
        )


@router.get("/queue", response_model=RefundQueueListResponse)
async def list_queued_events(
    db: Session = Depends(get_db),
    status_filter: Optional[str] = None,
    page: int = 1,
    size: int = 20,
):
    """List queued refund events with optional status filter and pagination."""
    query = db.query(RefundEventQueue)

    if status_filter:
        query = query.filter(RefundEventQueue.status == status_filter)

    total = query.count()
    items = query.order_by(desc(RefundEventQueue.created_at)).offset((page - 1) * size).limit(size).all()

    return RefundQueueListResponse(
        items=[_queue_item_to_response(item) for item in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.post("/refund", response_model=EnqueueRefundResponse, status_code=status.HTTP_201_CREATED)
async def enqueue_refund(
    request: RefundEventRequest,
    db: Session = Depends(get_db),
):
    """
    Enqueue a refund event from the merchant's refund system.
    This simulates a merchant's refund system pushing a refund event to Sentinel.
    """
    monitor = get_queue_monitor()

    # Check for duplicate refund_id in queue
    existing_in_queue = db.query(RefundEventQueue).filter(
        RefundEventQueue.refund_id == request.refund_id
    ).first()
    if existing_in_queue:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Refund {request.refund_id} already in queue (status: {existing_in_queue.status})",
        )

    # Check if already processed as a case
    existing_case = db.query(RiskCase).filter(RiskCase.refund_id == request.refund_id).first()
    if existing_case:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Refund {request.refund_id} already processed as case #{existing_case.id}",
        )

    # Create queue entry
    event = RefundEventQueue(
        refund_id=request.refund_id,
        customer_id=request.customer_id,
        order_id=request.order_id,
        amount_inr=request.amount_inr,
        event_time=datetime.fromisoformat(request.event_time.replace('Z', '+00:00')),
        device_id=request.device_id,
        address_id=request.address_id,
        payment_token=request.payment_token,
        product_category=request.product_category,
        order_amount_inr=request.order_amount_inr,
        order_time=datetime.fromisoformat(request.order_time.replace('Z', '+00:00')),
        status="pending",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Increment received counter
    monitor = get_queue_monitor()
    monitor.increment_received()

    return {
        "success": True,
        "message": f"Refund {request.refund_id} enqueued for processing",
        "queue_id": event.id,
        "status": "pending",
    }


@router.post("/refund/{refund_id}/process", response_model=RefundEventResponse)
async def process_refund_now(
    refund_id: str,
    db: Session = Depends(get_db),
):
    """Manually trigger processing of a specific refund in the queue."""
    event = db.query(RefundEventQueue).filter(RefundEventQueue.refund_id == refund_id).first()
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Refund {refund_id} not found in queue",
        )

    if event.status == "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Refund {refund_id} already processed",
        )

    # Reuse the existing ingestion logic
    service = get_inference_service()
    result = service.score_refund(refund_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Refund {refund_id} not found in historical data",
        )

    # Persist case
    case = _persist_case(db, result)

    # Update queue status
    event.status = "completed"
    event.processed_at = datetime.utcnow()
    db.commit()

    # Update monitor stats
    monitor = get_queue_monitor()
    monitor.events_processed += 1
    monitor.last_processed_event = datetime.utcnow()
    monitor.last_processed_refund_id = result["refund_id"]
    monitor.last_processed_risk_band = result["risk_band"]
    monitor.last_processed_action = result["recommended_action"]

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