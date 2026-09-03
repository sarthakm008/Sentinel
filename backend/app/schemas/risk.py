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


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    threshold_loaded: bool