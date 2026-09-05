"""SQLAlchemy models for webhook processing."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.orm import DeclarativeBase

from backend.app.models.base import Base


class ProcessedWebhookEvent(Base):
    """Track processed webhook events for idempotency."""
    __tablename__ = "processed_webhook_events"

    event_id = Column(String(128), primary_key=True, index=True)
    event_type = Column(String(64), nullable=False)
    payload_hash = Column(String(64), nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Index for cleanup queries
    __table_args__ = (
        Index("ix_processed_webhook_events_processed_at", "processed_at"),
    )


class RefundEventQueueMixin:
    """Mixin to add webhook provenance fields to RefundEventQueue."""
    # These will be added to the existing RefundEventQueue model
    pass