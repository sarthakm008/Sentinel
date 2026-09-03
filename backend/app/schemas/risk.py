"""Pydantic schemas for Sentinel API."""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class RiskScoreRequest(BaseModel):
    """Request to score a refund event."""
    refund_id: str = Field(..., description="Refund event ID to score")
    customer_id: Optional[str] = Field(None, description="Customer ID (optional, for validation)")
    order_id: Optional[str] = Field(None, description="Order ID (optional, for validation)")


class EvidenceItem(BaseModel):
    """Single evidence item for human-readable explanation."""
    category: str = Field(..., description="Evidence category: behavioral, graph, temporal")
    metric: str = Field(..., description="Internal metric name")
    value: Any = Field(..., description="Metric value")
    description: str = Field(..., description="Human-readable description")


class RiskScoreResponse(BaseModel):
    """Response from risk scoring endpoint."""
    refund_id: str
    customer_id: str
    order_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score [0,1]")
    risk_band: str = Field(..., description="Risk band: LOW, MEDIUM, HIGH, CRITICAL")
    recommended_action: str = Field(..., description="Recommended action: approve, verify, review, hold")
    threshold: float = Field(..., description="Frozen decision threshold")
    evidence: List[EvidenceItem] = Field(default_factory=list)
    case_id: Optional[int] = Field(None, description="Created case ID if persisted")


class GraphNode(BaseModel):
    """Graph node for visualization."""
    id: str
    type: str = Field(..., description="Node type: customer, device, address, payment")
    label: str
    is_target: bool = False
    risk_score: Optional[float] = None


class GraphEdge(BaseModel):
    """Graph edge for visualization."""
    source: str
    target: str
    relationship: str


class GraphResponse(BaseModel):
    """Graph subgraph response."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    target_customer: str
    stats: Dict[str, Any]


class CaseBase(BaseModel):
    """Base case schema."""
    customer_id: str
    refund_id: str
    order_id: str
    risk_score: float
    risk_band: str
    recommended_action: str
    status: str = "pending"


class CaseCreate(CaseBase):
    """Create case request."""
    pass


class CaseResponse(CaseBase):
    """Case response with metadata."""
    id: int
    created_at: datetime
    decided_at: Optional[datetime] = None
    decision: Optional[str] = None
    evidence: List[EvidenceItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class DecisionRequest(BaseModel):
    """Decision request for a case."""
    decision: str = Field(..., description="Decision: approve, verify, review, hold")


class DecisionResponse(BaseModel):
    """Decision response."""
    success: bool
    case_id: int
    decision: str
    timestamp: datetime


class EvaluationMetrics(BaseModel):
    """Model evaluation metrics."""
    model_name: str
    pr_auc: float
    roc_auc: float
    precision: float
    recall: float
    f1: float
    total_expected_loss: float
    loss_avoided_vs_baseline: float
    frozen_threshold: float
    sample_count: int
    positive_count: int


class EvaluationResponse(BaseModel):
    """Full evaluation response."""
    production_candidate: EvaluationMetrics
    ablation: List[EvaluationMetrics]
    type_f: List[EvaluationMetrics]
    future_period: List[EvaluationMetrics]
    phase5_experiment: Dict[str, Any]
    thresholds: Dict[str, float]


class DemoScenario(BaseModel):
    """Demo scenario configuration."""
    refund_ids: List[str]
    description: str


class DemoResetResponse(BaseModel):
    """Demo reset response."""
    success: bool
    message: str


class TimelineEvent(BaseModel):
    """Single timeline event."""
    customer_id: str
    timestamp: str
    event_type: str  # "order" or "refund"
    is_target: bool


class TimelineResponse(BaseModel):
    """Timeline events response."""
    target_customer: str
    target_refund_id: str
    target_timestamp: str
    window_hours: int
    events: List[TimelineEvent]
    component_size: int


class RefundEventRequest(BaseModel):
    """Incoming refund event from merchant."""
    refund_id: str = Field(..., description="Unique refund event identifier")
    customer_id: str = Field(..., description="Customer identifier")
    order_id: str = Field(..., description="Order identifier")
    amount_inr: float = Field(..., gt=0, description="Refund amount in INR")
    event_time: str = Field(..., description="ISO8601 timestamp of refund request")
    device_id: str = Field(..., description="Device identifier")
    address_id: str = Field(..., description="Address identifier")
    payment_token: str = Field(..., description="Payment token identifier")
    product_category: str = Field(..., description="Product category of the order")
    order_amount_inr: float = Field(..., gt=0, description="Original order amount in INR")
    order_time: str = Field(..., description="ISO8601 timestamp of original order")


class RefundEventResponse(BaseModel):
    """Response from refund ingestion endpoint."""
    refund_id: str
    customer_id: str
    order_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score [0,1]")
    risk_band: str = Field(..., description="Risk band: LOW, MEDIUM, HIGH, CRITICAL")
    recommended_action: str = Field(..., description="Recommended action: approve, verify, review, hold")
    threshold: float = Field(..., description="Frozen decision threshold")
    evidence: List[EvidenceItem] = Field(default_factory=list)
    case_id: int = Field(..., description="Created case ID")
    created_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    threshold_loaded: bool


class RefundQueueItem(BaseModel):
    """Single refund event in the queue."""
    id: int
    refund_id: str
    customer_id: str
    order_id: str
    amount_inr: float
    event_time: datetime
    device_id: str
    address_id: str
    payment_token: str
    product_category: str
    order_amount_inr: float
    order_time: datetime
    status: str  # pending, processing, completed, failed
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class RefundQueueListResponse(BaseModel):
    """Response for listing queued refund events."""
    items: List[RefundQueueItem]
    total: int
    page: int
    size: int
    pages: int


class IntegrationStatusResponse(BaseModel):
    """Integration status for merchant refund monitoring."""
    connected: bool
    monitoring: bool
    last_processed_event: Optional[datetime] = None
    events_received: int
    events_processed: int
    events_failed: int
    queue_pending: int
    last_processed_refund_id: Optional[str] = None
    last_processed_risk_band: Optional[str] = None
    last_processed_action: Optional[str] = None


class QueueControlRequest(BaseModel):
    """Request to control queue monitoring."""
    action: str  # "start", "stop", "pause", "resume"


class QueueControlResponse(BaseModel):
    """Response for queue control actions."""
    success: bool
    message: str
    monitoring: bool


class EnqueueRefundResponse(BaseModel):
    """Response for enqueue refund endpoint."""
    success: bool
    message: str
    queue_id: int
    status: str