"""SQLAlchemy models for risk cases and evidence."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class RiskCase(Base):
    """Risk case from Sentinel scoring."""
    __tablename__ = "risk_cases"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(64), index=True, nullable=False)
    refund_id = Column(String(64), index=True, nullable=False)
    order_id = Column(String(64), index=True, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_band = Column(String(16), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    recommended_action = Column(String(16), nullable=False)  # approve, verify, review, hold
    status = Column(String(16), default="pending", nullable=False)  # pending, decided
    decision = Column(String(16), nullable=True)  # approve, verify, review, hold
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    decided_at = Column(DateTime, nullable=True)

    evidence = relationship("CaseEvidence", back_populates="case", cascade="all, delete-orphan")
    decisions = relationship("CaseDecision", back_populates="case", cascade="all, delete-orphan")


class CaseEvidence(Base):
    """Structured evidence for a risk case."""
    __tablename__ = "case_evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("risk_cases.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(16), nullable=False)  # behavioral, graph, temporal
    metric = Column(String(64), nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    case = relationship("RiskCase", back_populates="evidence")


class CaseDecision(Base):
    """Decision history for a risk case."""
    __tablename__ = "case_decisions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("risk_cases.id", ondelete="CASCADE"), nullable=False)
    decision = Column(String(16), nullable=False)  # approve, verify, review, hold
    user_id = Column(String(64), default="merchant", nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    case = relationship("RiskCase", back_populates="decisions")


class RefundEventQueue(Base):
    """Queued refund events from merchant's refund system awaiting Sentinel processing."""
    __tablename__ = "refund_event_queue"

    id = Column(Integer, primary_key=True, index=True)
    refund_id = Column(String(64), index=True, nullable=False)
    customer_id = Column(String(64), index=True, nullable=True)
    order_id = Column(String(64), nullable=False)
    amount_inr = Column(Float, nullable=False)
    event_time = Column(DateTime, nullable=False)
    device_id = Column(String(64), nullable=True)
    address_id = Column(String(64), nullable=True)
    payment_token = Column(String(64), nullable=True)
    product_category = Column(String(32), nullable=True)
    order_amount_inr = Column(Float, nullable=False)
    order_time = Column(DateTime, nullable=False)
    status = Column(SQLEnum("pending", "processing", "completed", "failed", "enrichment_required", name="queue_status"), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    # Webhook provenance
    webhook_event_id = Column(String(128), index=True, nullable=True)
    source = Column(String(16), default="api", nullable=False)  # 'api' | 'webhook'