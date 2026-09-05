"""Merchant context resolution for Razorpay webhook events.

This module resolves Razorpay webhook fields into the full set of fields
required by Sentinel's 39-feature model. It attempts to resolve merchant
context using existing identifiers (order_id, payment_id).

IMPORTANT: Does NOT fabricate identifiers. If context cannot be resolved,
the event is marked as enrichment_required.
"""

from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.app.models.risk_case import RefundEventQueue, RiskCase
from backend.app.schemas.webhook import (
    RazorpayWebhookEvent,
    NormalizedRefundEvent,
    WebhookEventType,
    RazorpayRefundEntity,
    RazorpayPaymentEntity,
)


class MerchantContextResolution:
    """Result of merchant context resolution attempt."""

    def __init__(
        self,
        customer_id: Optional[str] = None,
        device_id: Optional[str] = None,
        address_id: Optional[str] = None,
        payment_token: Optional[str] = None,
        product_category: Optional[str] = None,
        enrichment_required: bool = False,
        enrichment_reason: Optional[str] = None,
    ):
        self.customer_id = customer_id
        self.device_id = device_id
        self.address_id = address_id
        self.payment_token = payment_token
        self.product_category = product_category
        self.enrichment_required = enrichment_required
        self.enrichment_reason = enrichment_reason

    def is_complete(self) -> bool:
        """Check if all required fields are resolved."""
        return all([
            self.customer_id,
            self.device_id,
            self.address_id,
            self.payment_token,
            self.product_category,
        ]) and not self.enrichment_required


class MerchantContextResolver:
    """
    Resolves Razorpay webhook data into Sentinel-compatible refund event.

    Uses existing synthetic/historical data to resolve merchant context.
    Does NOT fabricate identifiers - if context cannot be resolved,
    marks event as enrichment_required.
    """

    def __init__(self, db: Session):
        self.db = db

    def resolve(self, event: RazorpayWebhookEvent, event_id: str) -> Tuple[NormalizedRefundEvent, MerchantContextResolution]:
        """
        Resolve a Razorpay webhook event into a normalized refund event.

        Args:
            event: Parsed Razorpay webhook event
            event_id: The x-razorpay-event-id header value for idempotency tracking

        Returns:
            Tuple of (NormalizedRefundEvent, MerchantContextResolution)
        """
        if not event.payload.refund or not event.payload.payment:
            return self._create_failed_normalization(
                event,
                "Missing refund or payment entity in payload"
            )

        refund = event.payload.refund
        payment = event.payload.payment

        # Extract directly available fields
        refund_id = refund.id
        order_id = payment.order_id
        amount_inr = refund.amount / 100.0  # paise to INR
        event_time = datetime.utcfromtimestamp(refund.created_at)
        order_amount_inr = payment.amount / 100.0
        order_time = datetime.utcfromtimestamp(payment.created_at)

        # Attempt to resolve merchant context
        resolution = self._resolve_merchant_context(refund, payment)

        # Build normalized event
        normalized = NormalizedRefundEvent(
            refund_id=refund_id,
            order_id=order_id,
            amount_inr=amount_inr,
            event_time=event_time,
            order_amount_inr=order_amount_inr,
            order_time=order_time,
            customer_id=resolution.customer_id,
            device_id=resolution.device_id,
            address_id=resolution.address_id,
            payment_token=resolution.payment_token,
            product_category=resolution.product_category,
            webhook_event_id=event_id,
            source="webhook",
            enrichment_required=resolution.enrichment_required,
            enrichment_reason=resolution.enrichment_reason,
        )

        return normalized, resolution

    def _resolve_merchant_context(
        self,
        refund: RazorpayRefundEntity,
        payment: RazorpayPaymentEntity
    ) -> MerchantContextResolution:
        """
        Attempt to resolve merchant context from existing data.

        Strategy:
        1. Check if we have an existing RiskCase with this refund_id
        2. Check if we have an existing RefundEventQueue entry
        3. Look up order by payment.order_id in historical data (orders_df)
           - This gives us customer_id, device_id, address_id, payment_token_id, product_category
        4. Verify customer exists in customers_df

        Returns resolution with whatever fields could be resolved.
        """
        # Try to find existing case with this refund_id
        existing_case = self.db.query(RiskCase).filter(
            RiskCase.refund_id == refund.id
        ).first()

        if existing_case:
            return MerchantContextResolution(
                customer_id=existing_case.customer_id,
                enrichment_required=True,
                enrichment_reason="Found existing case but missing device/address/payment context"
            )

        # Try to find in historical queue
        existing_queue = self.db.query(RefundEventQueue).filter(
            RefundEventQueue.refund_id == refund.id
        ).first()

        if existing_queue:
            return MerchantContextResolution(
                customer_id=existing_queue.customer_id,
                device_id=existing_queue.device_id,
                address_id=existing_queue.address_id,
                payment_token=existing_queue.payment_token,
                product_category=existing_queue.product_category,
            )

        # Look up order by payment.order_id in historical data
        order_data = self._resolve_order_data(payment.order_id)
        if not order_data:
            return MerchantContextResolution(
                enrichment_required=True,
                enrichment_reason=f"Order {payment.order_id} not found in historical data"
            )

        customer_id = order_data.get("customer_id")
        if not customer_id:
            return MerchantContextResolution(
                enrichment_required=True,
                enrichment_reason=f"Order {payment.order_id} missing customer_id"
            )

        # Verify customer exists in customers data
        if not self._verify_customer_exists(customer_id):
            return MerchantContextResolution(
                enrichment_required=True,
                enrichment_reason=f"Customer {customer_id} not found in historical data"
            )

        device_id = order_data.get("device_id")
        address_id = order_data.get("address_id")
        payment_token = order_data.get("payment_token_id")
        product_category = order_data.get("product_category")

        missing = []
        if not device_id:
            missing.append("device_id")
        if not address_id:
            missing.append("address_id")
        if not payment_token:
            missing.append("payment_token")
        if not product_category:
            missing.append("product_category")

        if missing:
            return MerchantContextResolution(
                customer_id=customer_id,
                device_id=device_id,
                address_id=address_id,
                payment_token=payment_token,
                product_category=product_category,
                enrichment_required=True,
                enrichment_reason=f"Missing context fields: {', '.join(missing)}"
            )

        return MerchantContextResolution(
            customer_id=customer_id,
            device_id=device_id,
            address_id=address_id,
            payment_token=payment_token,
            product_category=product_category,
        )

    def _resolve_order_data(self, order_id: str) -> Optional[dict]:
        """Look up order data from historical orders DataFrame."""
        from backend.app.services.ml_service import get_inference_service

        try:
            service = get_inference_service()
            if service.orders_df is not None:
                order_matches = service.orders_df[service.orders_df["order_id"] == order_id]
                if len(order_matches) == 1:
                    order = order_matches.iloc[0]
                    return {
                        "customer_id": order.get("customer_id"),
                        "device_id": order.get("device_id"),
                        "address_id": order.get("address_id"),
                        "payment_token_id": order.get("payment_token_id"),
                        "product_category": order.get("product_category"),
                    }
        except Exception:
            pass

        return None

    def _verify_customer_exists(self, customer_id: str) -> bool:
        """Verify customer exists in historical customers DataFrame."""
        from backend.app.services.ml_service import get_inference_service

        try:
            service = get_inference_service()
            if service.customers_df is not None:
                matches = service.customers_df[service.customers_df["customer_id"] == customer_id]
                return len(matches) == 1
        except Exception:
            pass

        return False

    def _create_failed_normalization(
        self,
        event: RazorpayWebhookEvent,
        reason: str
    ) -> Tuple[NormalizedRefundEvent, MerchantContextResolution]:
        """Create a failed normalization result."""
        resolution = MerchantContextResolution(
            enrichment_required=True,
            enrichment_reason=reason
        )
        normalized = NormalizedRefundEvent(
            refund_id="",
            order_id="",
            amount_inr=0.0,
            event_time=datetime.utcnow(),
            order_amount_inr=0.0,
            order_time=datetime.utcnow(),
            webhook_event_id="",
            source="webhook",
            enrichment_required=True,
            enrichment_reason=reason,
        )
        return normalized, resolution