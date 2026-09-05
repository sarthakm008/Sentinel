"""Razorpay webhook endpoint for refund events."""

import hashlib
import json
import logging
from typing import Optional

from fastapi import APIRouter, Request, Response, HTTPException, Depends, Header, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.models.base import get_db
from backend.app.models.risk_case import RefundEventQueue, RiskCase
from backend.app.models.webhook import ProcessedWebhookEvent
from backend.app.schemas.webhook import (
    RazorpayWebhookEvent,
    RazorpayWebhookEventMinimal,
    WebhookEventType,
    NormalizedRefundEvent,
)
from backend.app.services.webhook_verifier import verify_razorpay_signature, get_webhook_secret
from backend.app.services.merchant_context_resolver import MerchantContextResolver

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/razorpay", status_code=status.HTTP_200_OK)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: Optional[str] = Header(None, alias="x-razorpay-event-id"),
    db: Session = Depends(get_db),
):
    """
    Razorpay refund webhook endpoint.

    Handles refund.created events by:
    1. Verifying HMAC-SHA256 signature on raw body
    2. Checking idempotency via x-razorpay-event-id
    3. Parsing and validating event payload
    4. Normalizing to Sentinel-compatible format
    5. Resolving merchant context
    6. Enqueueing for async scoring via QueueMonitor

    Returns 200 quickly after durable enqueue/acknowledgement.
    """
    # Read raw body FIRST - before any JSON parsing
    raw_body = await request.body()

    # 1. Verify signature
    if not x_razorpay_signature:
        logger.warning("Webhook request missing X-Razorpay-Signature header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature"
        )

    try:
        secret = get_webhook_secret()
    except RuntimeError as e:
        logger.error("Webhook secret not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook not configured"
        )

    if not verify_razorpay_signature(raw_body, x_razorpay_signature, secret):
        logger.warning("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    # 2. Check event ID header
    if not x_razorpay_event_id:
        logger.warning("Webhook request missing x-razorpay-event-id header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event ID"
        )

    # 3. Parse JSON payload (after signature verification)
    try:
        payload = json.loads(raw_body.decode("utf-8"))
        # First, extract just the event type to decide validation strategy
        event_type = payload.get("event", "")
        
        # For unsupported/acknowledge-only events, do minimal validation
        if event_type in WebhookEventType.ACKNOWLEDGE_ONLY_EVENTS or event_type not in WebhookEventType.SCORING_EVENTS:
            # Minimal validation - just ensure it's a valid event structure
            event = RazorpayWebhookEventMinimal(**payload)
        else:
            # Full validation for scoring events
            event = RazorpayWebhookEvent(**payload)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    except Exception as e:
        logger.warning(f"Invalid webhook payload structure: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload structure"
        )

    # 4. Idempotency check - use database constraint as authoritative
    try:
        processed_event = ProcessedWebhookEvent(
            event_id=x_razorpay_event_id,
            event_type=event_type,
            payload_hash=hashlib.sha256(raw_body).hexdigest()[:64],
        )
        db.add(processed_event)
        db.commit()
    except IntegrityError:
        # Duplicate event - already processed, acknowledge with 200
        db.rollback()
        logger.info(f"Duplicate webhook event acknowledged: {x_razorpay_event_id}")
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during idempotency check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error"
        )

    # 5. Handle event type
    if event.event not in WebhookEventType.ALL_EVENTS:
        logger.info(f"Unsupported webhook event type: {event.event}")
        return Response(status_code=status.HTTP_200_OK)

    if event.event in WebhookEventType.ACKNOWLEDGE_ONLY_EVENTS:
        # Acknowledge but don't enqueue for scoring
        logger.info(f"Acknowledged {event.event} event (no scoring): {x_razorpay_event_id}")
        return Response(status_code=status.HTTP_200_OK)

    # 5. Only process refund.created for scoring
    if event.event != WebhookEventType.REFUND_CREATED:
        logger.info(f"Event type {event.event} not configured for scoring")
        return Response(status_code=status.HTTP_200_OK)

    # 6. Validate required payload entities
    if not event.payload.refund or not event.payload.payment:
        logger.warning(f"Missing refund or payment entity in refund.created event: {x_razorpay_event_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing refund or payment entity"
        )

    refund = event.payload.refund
    payment = event.payload.payment

    # Validate required fields
    if not refund.id or not payment.order_id:
        logger.warning(f"Missing required fields in refund.created: {x_razorpay_event_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required refund or payment fields"
        )

    # Currency validation - only INR supported
    if refund.currency != "INR":
        logger.warning(f"Unsupported currency {refund.currency} for refund {refund.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported currency: {refund.currency}. Only INR is supported."
        )

    # 7. Normalize and resolve merchant context
    try:
        resolver = MerchantContextResolver(db)
        normalized, resolution = resolver.resolve(event, x_razorpay_event_id)
    except Exception as e:
        logger.error(f"Error during normalization/resolution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Normalization error"
        )

    # 8. Check for duplicate refund_id in queue (regardless of source)
    existing_queue = db.query(RefundEventQueue).filter(
        RefundEventQueue.refund_id == refund.id
    ).first()
    if existing_queue:
        logger.info(f"Refund {refund.id} already in queue (status: {existing_queue.status})")
        return Response(status_code=status.HTTP_200_OK)

    # Check if already processed as a case
    existing_case = db.query(RiskCase).filter(
        RiskCase.refund_id == refund.id
    ).first()
    if existing_case:
        logger.info(f"Refund {refund.id} already processed as case #{existing_case.id}")
        return Response(status_code=status.HTTP_200_OK)

    # 9. Handle enrichment_required case - acknowledge but don't enqueue for scoring
    if resolution.enrichment_required:
        logger.info(f"Webhook refund {refund.id} requires enrichment: {resolution.enrichment_reason}")
        # Store as a record for tracking but don't enqueue for scoring
        tracking_entry = RefundEventQueue(
            refund_id=normalized.refund_id,
            customer_id=normalized.customer_id,
            order_id=normalized.order_id,
            amount_inr=normalized.amount_inr,
            event_time=normalized.event_time,
            device_id=normalized.device_id,
            address_id=normalized.address_id,
            payment_token=normalized.payment_token,
            product_category=normalized.product_category,
            order_amount_inr=normalized.order_amount_inr,
            order_time=normalized.order_time,
            status="enrichment_required",
            webhook_event_id=x_razorpay_event_id,
            source="webhook",
            error_message=f"Enrichment required: {resolution.enrichment_reason}",
        )
        try:
            db.add(tracking_entry)
            db.commit()
            logger.info(f"Tracked webhook refund {refund.id} for enrichment: {resolution.enrichment_reason}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to track webhook refund for enrichment: {e}")
        return Response(status_code=status.HTTP_200_OK)

    # 9. Create queue entry for scoring (only when all context is available)
    # All required fields are guaranteed to be present when enrichment_required=False
    queue_entry = RefundEventQueue(
        refund_id=normalized.refund_id,
        customer_id=normalized.customer_id,
        order_id=normalized.order_id,
        amount_inr=normalized.amount_inr,
        event_time=normalized.event_time,
        device_id=normalized.device_id,
        address_id=normalized.address_id,
        payment_token=normalized.payment_token,
        product_category=normalized.product_category,
        order_amount_inr=normalized.order_amount_inr,
        order_time=normalized.order_time,
        status="pending",
        webhook_event_id=x_razorpay_event_id,
        source="webhook",
    )

    try:
        db.add(queue_entry)
        db.commit()
        db.refresh(queue_entry)

        # Increment monitor counter
        from backend.app.services.queue_monitor import get_queue_monitor
        monitor = get_queue_monitor()
        monitor.increment_received()

        logger.info(f"Enqueued webhook refund {refund.id} for scoring (queue_id: {queue_entry.id})")

        return Response(status_code=status.HTTP_200_OK)

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to enqueue webhook refund: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enqueue refund"
        )


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint."""
    return {"status": "ok", "service": "razorpay-webhook"}