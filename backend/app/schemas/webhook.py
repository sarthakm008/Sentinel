"""Pydantic schemas for Razorpay webhook payloads."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RazorpayRefundEntityMinimal(BaseModel):
    """Minimal Razorpay refund entity for initial event type detection."""
    id: Optional[str] = None
    entity: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    payment_id: Optional[str] = None
    notes: Optional[Dict[str, str]] = None
    receipt: Optional[str] = None
    acquirer_data: Optional[Dict[str, Any]] = None
    created_at: Optional[int] = None
    batch_id: Optional[str] = None
    status: Optional[str] = None
    speed_processed: Optional[str] = None
    speed_requested: Optional[str] = None


class RazorpayPaymentEntityMinimal(BaseModel):
    """Minimal Razorpay payment entity for initial event type detection."""
    id: Optional[str] = None
    entity: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    base_amount: Optional[int] = None
    status: Optional[str] = None
    order_id: Optional[str] = None
    invoice_id: Optional[str] = None
    international: Optional[bool] = None
    method: Optional[str] = None
    amount_refunded: Optional[int] = None
    amount_transferred: Optional[int] = None
    refund_status: Optional[str] = None
    captured: Optional[bool] = None
    description: Optional[str] = None
    card_id: Optional[str] = None
    bank: Optional[str] = None
    wallet: Optional[str] = None
    vpa: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    notes: Optional[List[Dict[str, str]]] = None
    fee: Optional[int] = None
    tax: Optional[int] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_source: Optional[str] = None
    error_step: Optional[str] = None
    error_reason: Optional[str] = None
    acquirer_data: Optional[Dict[str, Any]] = None
    created_at: Optional[int] = None


class RazorpayWebhookPayloadMinimal(BaseModel):
    """Minimal Razorpay webhook payload structure for event type detection."""
    refund: Optional[RazorpayRefundEntityMinimal] = None
    payment: Optional[RazorpayPaymentEntityMinimal] = None


class RazorpayWebhookEventMinimal(BaseModel):
    """Minimal top-level Razorpay webhook event structure for event type detection."""
    entity: Optional[str] = None
    account_id: Optional[str] = None
    event: Optional[str] = None
    contains: Optional[List[str]] = None
    payload: Optional[RazorpayWebhookPayloadMinimal] = None
    created_at: Optional[int] = None


class RazorpayRefundEntity(BaseModel):
    """Razorpay refund entity from webhook payload."""
    id: str = Field(..., description="Razorpay refund ID (rfnd_...)")
    entity: str = Field(default="refund")
    amount: int = Field(..., description="Refund amount in paise")
    currency: str = Field(default="INR")
    payment_id: str = Field(..., description="Associated payment ID (pay_...)")
    notes: Optional[Dict[str, str]] = None
    receipt: Optional[str] = None
    acquirer_data: Optional[Dict[str, Any]] = None
    created_at: int = Field(..., description="Unix timestamp")
    batch_id: Optional[str] = None
    status: str = Field(..., description="Refund status: processed, failed, etc.")
    speed_processed: Optional[str] = None
    speed_requested: Optional[str] = None


class RazorpayPaymentEntity(BaseModel):
    """Razorpay payment entity from webhook payload."""
    id: str = Field(..., description="Razorpay payment ID (pay_...)")
    entity: str = Field(default="payment")
    amount: int = Field(..., description="Payment amount in paise")
    currency: str = Field(default="INR")
    base_amount: int = Field(..., description="Base amount in paise")
    status: str = Field(..., description="Payment status: captured, failed, etc.")
    order_id: str = Field(..., description="Associated order ID (order_...)")
    invoice_id: Optional[str] = None
    international: bool = False
    method: Optional[str] = Field(None, description="Payment method: card, netbanking, upi, etc.")
    amount_refunded: int = 0
    amount_transferred: int = 0
    refund_status: Optional[str] = None
    captured: bool = False
    description: Optional[str] = None
    card_id: Optional[str] = None
    bank: Optional[str] = None
    wallet: Optional[str] = None
    vpa: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    notes: List[Dict[str, str]] = []
    fee: int = 0
    tax: int = 0
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_source: Optional[str] = None
    error_step: Optional[str] = None
    error_reason: Optional[str] = None
    acquirer_data: Optional[Dict[str, Any]] = None
    created_at: int = Field(..., description="Unix timestamp")


class RazorpayWebhookPayload(BaseModel):
    """Complete Razorpay webhook payload structure."""
    refund: Optional[RazorpayRefundEntity] = None
    payment: Optional[RazorpayPaymentEntity] = None


class RazorpayWebhookEvent(BaseModel):
    """Top-level Razorpay webhook event structure."""
    entity: str = Field(default="event")
    account_id: str = Field(..., description="Razorpay account ID")
    event: str = Field(..., description="Event type: refund.created, refund.processed, etc.")
    contains: List[str] = Field(default_factory=list)
    payload: RazorpayWebhookPayload = Field(default_factory=RazorpayWebhookPayload)
    created_at: int = Field(..., description="Unix timestamp of event creation")


class RazorpayWebhookHeaders(BaseModel):
    """Expected headers for Razorpay webhook verification."""
    x_razorpay_signature: str = Field(..., alias="X-Razorpay-Signature")
    x_razorpay_event_id: str = Field(..., alias="x-razorpay-event-id")
    content_type: Optional[str] = Field(None, alias="Content-Type")


# Supported webhook event types
class WebhookEventType:
    REFUND_CREATED = "refund.created"
    REFUND_PROCESSED = "refund.processed"
    REFUND_FAILED = "refund.failed"
    REFUND_SPEED_CHANGED = "refund.speed_changed"

    # Events that should be enqueued for scoring
    SCORING_EVENTS = {REFUND_CREATED}

    # Events that should be acknowledged but not scored
    ACKNOWLEDGE_ONLY_EVENTS = {REFUND_PROCESSED, REFUND_FAILED, REFUND_SPEED_CHANGED}

    ALL_EVENTS = SCORING_EVENTS | ACKNOWLEDGE_ONLY_EVENTS


class NormalizedRefundEvent(BaseModel):
    """Normalized refund event ready for Sentinel queue."""
    refund_id: str
    order_id: str
    amount_inr: float
    event_time: datetime
    order_amount_inr: float
    order_time: datetime
    # Fields that require merchant context resolution
    customer_id: Optional[str] = None
    device_id: Optional[str] = None
    address_id: Optional[str] = None
    payment_token: Optional[str] = None
    product_category: Optional[str] = None
    # Metadata
    webhook_event_id: str
    source: str = "webhook"
    enrichment_required: bool = False
    enrichment_reason: Optional[str] = None