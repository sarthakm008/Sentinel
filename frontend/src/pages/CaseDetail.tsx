// Case Detail page

import { useEffect, useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { casesApi, riskApi } from '../api';
import { CaseResponse, GraphResponse, EvidenceItem, TimelineResponse, TimelineEvent } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { EvidenceCard } from '../components/EvidenceCard';
import { GraphViz } from '../components/GraphViz';

export function CaseDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState<CaseResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState(false);
  const [activeTab, setActiveTab] = useState<'evidence' | 'graph' | 'decision' | 'timeline'>('evidence');

  useEffect(() => {
    if (id) {
      loadCase();
    }
  }, [id]);

  const loadCase = async () => {
    try {
      setLoading(true);
      const [caseRes, graphRes, timelineRes] = await Promise.all([
        casesApi.get(parseInt(id!)),
        riskApi.getGraph(parseInt(id!)),
        casesApi.getTimeline(parseInt(id!)),
      ]);
      setCaseData(caseRes);
      setGraphData(graphRes);
      setTimelineData(timelineRes);
    } catch (err) {
      console.error('Failed to load case:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision: 'approve' | 'verify' | 'review' | 'hold') => {
    if (!caseData) return;
    try {
      setDeciding(true);
      await casesApi.decide(caseData.id, decision);
      await loadCase();
    } catch (err) {
      console.error('Decision failed:', err);
    } finally {
      setDeciding(false);
    }
  };

  const groupEvidence = (evidence: EvidenceItem[]) => {
    return {
      behavioral: evidence.filter(e => e.category === 'behavioral'),
      graph: evidence.filter(e => e.category === 'graph'),
      temporal: evidence.filter(e => e.category === 'temporal'),
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="text-center py-12">
        <p className="text-text-muted">Case not found</p>
        <button
          onClick={() => navigate('/cases')}
          className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary-hover"
        >
          Back to Cases
        </button>
      </div>
    );
  }

  const evidenceGroups = groupEvidence(caseData.evidence);

  const bandColors: Record<string, string> = {
    LOW: 'bg-success-light text-success-foreground',
    MEDIUM: 'bg-warning-light text-warning-foreground',
    HIGH: 'bg-danger-light text-danger-foreground',
    CRITICAL: 'bg-critical-light text-critical-foreground',
  };

  const actionColors: Record<string, string> = {
    approve: 'bg-success-light text-success-foreground',
    verify: 'bg-primary-light text-primary',
    review: 'bg-warning-light text-warning-foreground',
    hold: 'bg-danger-light text-danger-foreground',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => navigate('/cases')}
            className="text-text-muted hover:text-text-secondary mb-2"
          >
            ← Back to Cases
          </button>
          <h1 className="text-2xl font-bold text-text-primary">Case #{caseData.id}</h1>
          <p className="text-text-secondary">{caseData.refund_id} • {caseData.customer_id}</p>
        </div>
        <div className="flex items-center gap-4">
          <Link to={`/cases/${caseData.id}`} className="text-sm text-primary hover:text-primary-hover">
            Refresh
          </Link>
        </div>
      </div>

      {/* Risk Summary */}
      <div className="card p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <RiskBadge
              score={caseData.risk_score}
              band={caseData.risk_band}
              action={caseData.recommended_action}
            />
            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-text-secondary">Order ID</p>
                <p className="font-mono font-medium">{caseData.order_id}</p>
              </div>
              <div>
                <p className="text-text-secondary">Threshold</p>
                <p className="font-mono font-medium">{caseData.risk_score > 0.41 ? '0.41 (exceeded)' : '0.41'}</p>
              </div>
              <div>
                <p className="text-text-secondary">Status</p>
                <p className={`font-medium capitalize ${caseData.status === 'decided' ? 'text-text-primary' : 'text-primary'}`}>
                  {caseData.status}
                </p>
              </div>
              <div>
                <p className="text-text-secondary">Created</p>
                <p className="font-mono font-medium">{new Date(caseData.created_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
          <div className="lg:col-span-1">
            <div className="space-y-3">
              <div className="p-4 bg-bg-tertiary rounded-lg">
                <p className="text-sm text-text-secondary">Recommended Action</p>
                <p className="font-semibold px-3 py-1 rounded inline-block badge-info">
                  {caseData.recommended_action.toUpperCase()}
                </p>
              </div>
              {caseData.status === 'pending' && (
                <div className="space-y-2">
                  {(['approve', 'verify', 'review', 'hold'] as const).map((action) => (
                    <button
                      key={action}
                      onClick={() => handleDecision(action)}
                      disabled={deciding}
                      className={`w-full px-4 py-2 rounded-lg font-medium transition ${
                        action === 'approve' ? 'btn-success' :
                        action === 'verify' ? 'btn-primary' :
                        action === 'review' ? 'btn-warning' :
                        'btn-danger'
                      }`}
                    >
                      {deciding ? 'Processing...' : action.charAt(0).toUpperCase() + action.slice(1)}
                    </button>
                  ))}
                </div>
              )}
              {caseData.status === 'decided' && (
                <div className="p-4 bg-success-light border border-success-light rounded-lg">
                  <p className="text-sm text-success">Decision Made</p>
                  <p className="text-success">
                    Action: <strong>{caseData.decision?.toUpperCase()}</strong>
                    {caseData.decided_at && ` • ${new Date(caseData.decided_at).toLocaleString()}`}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="card overflow-hidden">
        <div className="border-b border-border">
          <nav className="flex -mb-px" aria-label="Tabs">
            {([
              { key: 'evidence', label: 'Evidence' },
              { key: 'graph', label: 'Network Graph' },
              { key: 'decision', label: 'Decision' },
              { key: 'timeline', label: 'Timeline' },
            ] as const).map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-6 py-3 text-sm font-medium border-b-2 transition ${
                  activeTab === tab.key
                    ? 'border-primary text-primary'
                    : 'border-transparent text-text-secondary hover:text-text-primary hover:border-border'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'evidence' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <EvidenceCard
                title="Behavioral Evidence"
                category="behavioral"
                items={evidenceGroups.behavioral}
              />
              <EvidenceCard
                title="Graph Evidence"
                category="graph"
                items={evidenceGroups.graph}
              />
              <EvidenceCard
                title="Temporal Evidence"
                category="temporal"
                items={evidenceGroups.temporal}
              />
            </div>
          )}

          {activeTab === 'graph' && (
            <div>
              <GraphViz data={graphData} width={800} height={500} />
              {graphData && (
                <div className="mt-4 grid grid-cols-4 gap-4 text-sm">
                  <div className="bg-bg-tertiary p-3 rounded">
                    <p className="text-text-secondary">Connected Customers</p>
                    <p className="font-bold text-text-primary">{graphData.stats.connected_customers}</p>
                  </div>
                  <div className="bg-bg-tertiary p-3 rounded">
                    <p className="text-text-secondary">Shared Devices</p>
                    <p className="font-bold text-text-primary">{graphData.stats.shared_devices}</p>
                  </div>
                  <div className="bg-bg-tertiary p-3 rounded">
                    <p className="text-text-secondary">Shared Addresses</p>
                    <p className="font-bold text-text-primary">{graphData.stats.shared_addresses}</p>
                  </div>
                  <div className="bg-bg-tertiary p-3 rounded">
                    <p className="text-text-secondary">Shared Payments</p>
                    <p className="font-bold text-text-primary">{graphData.stats.shared_payments}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'decision' && (
            <div className="space-y-4">
              <div className="p-4 bg-bg-tertiary rounded-lg">
                <h3 className="font-semibold text-text-primary mb-2">Risk Assessment Summary</h3>
                <p className="text-text-secondary">
                  This refund event was scored <strong>{caseData.risk_score.toFixed(3)}</strong>
                  by the Sentinel production model (39 features: 18 behavioral + 15 graph + 6 temporal).
                  The frozen decision threshold is <strong>0.41</strong>.
                </p>
                <p className="text-text-secondary mt-2">
                  Based on the ActionPolicy, this places the event in the
                  <strong className={`badge-info px-2 py-0.5 rounded inline-block`}>
                    {caseData.risk_band}
                  </strong>
                  band, recommending <strong className="badge-info px-2 py-0.5 rounded inline-block">
                    {caseData.recommended_action.toUpperCase()}
                  </strong>.
                </p>
              </div>

              {caseData.status === 'decided' && (
                <div className="p-4 bg-success-light border border-success-light rounded-lg">
                  <h3 className="font-semibold text-success mb-2">Decision Recorded</h3>
                  <p className="text-success">
                    Action: <strong>{caseData.decision?.toUpperCase()}</strong>
                    {caseData.decided_at && ` • ${new Date(caseData.decided_at).toLocaleString()}`}
                  </p>
                </div>
              )}

              <div className="p-4 bg-bg-tertiary rounded-lg">
                <h3 className="font-semibold text-text-primary mb-2">Feature Values (Production Model)</h3>
                <details className="text-sm">
                  <summary className="cursor-pointer text-primary hover:text-primary-hover">Show all 39 features</summary>
                  <pre className="mt-2 p-3 bg-surface border border-border rounded overflow-auto text-xs">
                    {JSON.stringify(caseData, null, 2)}
                  </pre>
                </details>
              </div>
            </div>
          )}

          {activeTab === 'timeline' && (
            <div>
              {timelineData ? (
                <div className="space-y-4">
                  <div className="bg-bg-tertiary p-4 rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-text-secondary">Target Customer</p>
                        <p className="font-mono font-medium">{timelineData.target_customer}</p>
                      </div>
                      <div>
                        <p className="text-text-secondary">Target Refund</p>
                        <p className="font-mono font-medium">{timelineData.target_refund_id}</p>
                      </div>
                      <div>
                        <p className="text-text-secondary">Refund Time</p>
                        <p className="font-mono font-medium">{new Date(timelineData.target_timestamp).toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-text-secondary">Component Size</p>
                        <p className="font-bold text-text-primary">{timelineData.component_size} accounts</p>
                      </div>
                    </div>
                  </div>
                  {timelineData.events.length === 0 ? (
                    <div className="text-text-muted text-center py-8">
                      No events in the connected component within the {timelineData.window_hours}-hour window before the refund.
                    </div>
                  ) : (
                    <div className="card overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-bg-tertiary border-b border-border">
                            <tr>
                              <th className="px-4 py-3 text-left font-semibold text-text-secondary">Time (Relative)</th>
                              <th className="px-4 py-3 text-left font-semibold text-text-secondary">Absolute Time</th>
                              <th className="px-4 py-3 text-left font-semibold text-text-secondary">Customer</th>
                              <th className="px-4 py-3 text-left font-semibold text-text-secondary">Event Type</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border">
                            {timelineData.events.map((event, idx) => {
                              const eventTime = new Date(event.timestamp);
                              const targetTime = new Date(timelineData.target_timestamp);
                              const diffMinutes = Math.round((eventTime.getTime() - targetTime.getTime()) / 60000);
                              const relativeTime = diffMinutes < 0
                                ? `${Math.abs(diffMinutes)} min before`
                                : diffMinutes > 0
                                ? `${diffMinutes} min after`
                                : 'at refund time';
                              return (
                                <tr key={idx} className={event.is_target ? 'bg-primary-light' : ''}>
                                  <td className="px-4 py-3 font-mono text-text-secondary">{relativeTime}</td>
                                  <td className="px-4 py-3 font-mono text-text-secondary">{eventTime.toLocaleString()}</td>
                                  <td className="px-4 py-3">
                                    <span className={event.is_target ? 'font-mono font-medium text-primary' : 'font-mono text-text-primary'}>
                                      {event.customer_id}
                                      {event.is_target && ' (target)'}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                      event.event_type === 'refund'
                                        ? 'bg-danger-light text-danger-foreground'
                                        : 'bg-success-light text-success-foreground'
                                    }`}>
                                        {event.event_type.toUpperCase()}
                                      </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-text-muted text-center py-8">
                  Loading timeline...
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function formatCurrency(n: number): string {
  return `₹${n.toLocaleString(undefined, { minimumFractionDigits: 0 })}`;
}