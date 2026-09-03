// TypeScript types for Sentinel API

export interface EvidenceItem {
  category: 'behavioral' | 'graph' | 'temporal';
  metric: string;
  value: string | number;
  description: string;
}

export interface RiskScoreRequest {
  refund_id: string;
  customer_id?: string;
  order_id?: string;
}

export interface RiskScoreResponse {
  refund_id: string;
  customer_id: string;
  order_id: string;
  risk_score: number;
  risk_band: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommended_action: 'approve' | 'verify' | 'review' | 'hold';
  threshold: number;
  evidence: EvidenceItem[];
  case_id?: number;
}

export interface GraphNode {
  id: string;
  type: 'customer' | 'device' | 'address' | 'payment';
  label: string;
  is_target: boolean;
  risk_score?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  target_customer: string;
  stats: {
    total_nodes: number;
    total_edges: number;
    connected_customers: number;
    shared_devices: number;
    shared_addresses: number;
    shared_payments: number;
  };
}

export interface CaseResponse {
  id: number;
  customer_id: string;
  refund_id: string;
  order_id: string;
  risk_score: number;
  risk_band: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommended_action: 'approve' | 'verify' | 'review' | 'hold';
  status: 'pending' | 'decided';
  decision?: string;
  created_at: string;
  decided_at?: string;
  evidence: EvidenceItem[];
}

export interface CasesListResponse {
  cases: CaseResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface DecisionRequest {
  decision: 'approve' | 'verify' | 'review' | 'hold';
}

export interface DecisionResponse {
  success: boolean;
  case_id: number;
  decision: string;
  timestamp: string;
}

export interface EvaluationMetrics {
  model_name: string;
  pr_auc: number;
  roc_auc: number;
  precision: number;
  recall: number;
  f1: number;
  total_expected_loss: number;
  loss_avoided_vs_baseline: number;
  frozen_threshold: number;
  sample_count: number;
  positive_count: number;
}

export interface EvaluationResponse {
  production_candidate: EvaluationMetrics;
  ablation: EvaluationMetrics[];
  type_f: EvaluationMetrics[];
  future_period: EvaluationMetrics[];
  phase5_experiment: {
    feature: string;
    delta_pr_auc: number;
    ci_lower: number;
    ci_upper: number;
    decision: string;
    reason: string;
    model: string;
  };
  thresholds: Record<string, number>;
}

export interface DemoScenario {
  refund_ids: string[];
  description: string;
}

export interface DemoResetResponse {
  success: boolean;
  message: string;
}

export interface DemoRunResponse {
  success: boolean;
  message: string;
  cases: Array<{
    refund_id: string;
    case_id: number;
    customer_id: string;
    risk_score: number;
    risk_band: string;
    recommended_action: string;
    evidence_count: number;
  }>;
}

export interface TimelineEvent {
  customer_id: string;
  timestamp: string;
  event_type: 'order' | 'refund';
  is_target: boolean;
}

export interface TimelineResponse {
  target_customer: string;
  target_refund_id: string;
  target_timestamp: string;
  window_hours: int;
  events: TimelineEvent[];
  component_size: number;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  threshold_loaded: boolean;
}

// Refund Event types
export interface RefundEventRequest {
  refund_id: string;
  customer_id: string;
  order_id: string;
  amount_inr: number;
  event_time: string;
  device_id: string;
  address_id: string;
  payment_token: string;
  product_category: string;
  order_amount_inr: number;
  order_time: string;
}

export interface RefundEventResponse {
  refund_id: string;
  customer_id: string;
  order_id: string;
  risk_score: number;
  risk_band: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommended_action: 'approve' | 'verify' | 'review' | 'hold';
  threshold: number;
  evidence: EvidenceItem[];
  case_id: number;
  created_at: string;
}

export interface RefundStatusResponse {
  processed: boolean;
  refund_id: string;
  case_id?: number;
  risk_score?: number;
  risk_band?: string;
  recommended_action?: string;
  status?: string;
  created_at?: string;
}

// Integration types
export interface RefundQueueItem {
  id: number;
  refund_id: string;
  customer_id: string;
  order_id: string;
  amount_inr: number;
  event_time: string;
  device_id: string;
  address_id: string;
  payment_token: string;
  product_category: string;
  order_amount_inr: number;
  order_time: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  processed_at?: string;
  error_message?: string;
}

export interface RefundQueueListResponse {
  items: RefundQueueItem[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface IntegrationStatusResponse {
  connected: boolean;
  monitoring: boolean;
  last_processed_event?: string;
  events_received: number;
  events_processed: number;
  events_failed: number;
  queue_pending: number;
  last_processed_refund_id?: string;
  last_processed_risk_band?: string;
  last_processed_action?: string;
}

export interface QueueControlRequest {
  action: 'start' | 'stop' | 'pause' | 'resume';
}

export interface QueueControlResponse {
  success: boolean;
  message: string;
  monitoring: boolean;
}

export interface EnqueueRefundRequest {
  refund_id: string;
  customer_id: string;
  order_id: string;
  amount_inr: number;
  event_time: string;
  device_id: string;
  address_id: string;
  payment_token: string;
  product_category: string;
  order_amount_inr: number;
  order_time: string;
}

export interface EnqueueRefundResponse {
  success: boolean;
  message: string;
  queue_id: number;
  status: string;
}

export interface RefundQueueResponse {
  items: RefundQueueItem[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface IntegrationStatusResponse {
  connected: boolean;
  monitoring: boolean;
  last_processed_event?: string;
  events_received: number;
  events_processed: number;
  events_failed: number;
  queue_pending: number;
  last_processed_refund_id?: string;
  last_processed_risk_band?: string;
  last_processed_action?: string;
}

export interface QueueControlRequest {
  action: 'start' | 'stop' | 'pause' | 'resume';
}

export interface QueueControlResponse {
  success: boolean;
  message: string;
  monitoring: boolean;
}