// API client for Sentinel backend

// VITE_API_BASE should be set in production (e.g., https://your-api.onrender.com/api)
// Falls back to localhost for local development
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const riskApi = {
  score: (refundId: string, customerId?: string, orderId?: string) =>
    fetchJson<RiskScoreResponse>('/risk/score', {
      method: 'POST',
      body: JSON.stringify({ refund_id: refundId, customer_id: customerId, order_id: orderId }),
    }),

  getGraph: (caseId: number) =>
    fetchJson<GraphResponse>(`/cases/${caseId}/graph`),
};

export const casesApi = {
  list: (params?: { status?: string; band?: string; page?: number; size?: number }) => {
    const search = new URLSearchParams();
    if (params?.status) search.set('status', params.status);
    if (params?.band) search.set('band', params.band);
    if (params?.page) search.set('page', params.page.toString());
    if (params?.size) search.set('size', params.size.toString());
    return fetchJson<CasesListResponse>(`/cases?${search.toString()}`);
  },

  get: (caseId: number) =>
    fetchJson<CaseResponse>(`/cases/${caseId}`),

  decide: (caseId: number, decision: 'approve' | 'verify' | 'review' | 'hold') =>
    fetchJson<DecisionResponse>(`/cases/${caseId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision }),
    }),

  getTimeline: (caseId: number, windowHours?: number) => {
    const params = new URLSearchParams();
    if (windowHours) params.set('window_hours', windowHours.toString());
    return fetchJson<TimelineResponse>(`/cases/${caseId}/timeline?${params.toString()}`);
  },
};

export const evaluationApi = {
  get: () =>
    fetchJson<EvaluationResponse>('/evaluation'),
};

export const demoApi = {
  getScenario: () =>
    fetchJson<DemoScenario>('/demo/scenario'),

  reset: () =>
    fetchJson<DemoResetResponse>('/demo/reset', { method: 'POST' }),

  run: () =>
    fetchJson<DemoRunResponse>('/demo/run', { method: 'POST' }),
};

export const healthApi = {
  check: () =>
    fetchJson<HealthResponse>('/health'),
};

export const eventsApi = {
  ingestRefund: (request: RefundEventRequest) =>
    fetchJson<RefundEventResponse>('/events/refund', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  getRefundStatus: (refundId: string) =>
    fetchJson<RefundStatusResponse>(`/events/refund/${refundId}/status`),
};

export const integrationApi = {
  getStatus: () =>
    fetchJson<IntegrationStatusResponse>('/integration/status'),

  control: (action: 'start' | 'stop' | 'pause' | 'resume') =>
    fetchJson<QueueControlResponse>('/integration/control', {
      method: 'POST',
      body: JSON.stringify({ action }),
    }),

  getQueue: (params?: { status?: string; page?: number; size?: number }) => {
    const search = new URLSearchParams();
    if (params?.status) search.set('status', params.status);
    if (params?.page) search.set('page', params.page.toString());
    if (params?.size) search.set('size', params.size.toString());
    return fetchJson<RefundQueueListResponse>(`/integration/queue?${search.toString()}`);
  },

  enqueueRefund: (request: EnqueueRefundRequest) =>
    fetchJson<{ success: boolean; message: string; queue_id: number; status: string }>('/integration/refund', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  processRefundNow: (refundId: string) =>
    fetchJson<RefundEventResponse>(`/integration/refund/${refundId}/process`, {
      method: 'POST',
    }),
};