// CaseDetail Page - Analyst Workstation

import { useEffect, useState, useCallback } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { casesApi, riskApi } from '../api';
import { CaseResponse, GraphResponse, EvidenceItem, TimelineResponse, TimelineEvent } from '../types';
import { ScoreDisplay } from '../components/ScoreDisplay';
import { StatusBadge } from '../components/StatusBadge';
import { EvidenceCard } from '../components/EvidenceCard';
import { GraphViz } from '../components/GraphViz';
import { MetricRowWithDescription } from '../components/MetricRow';
import { CompactTable } from '../components/CompactTable';
import { formatTimestamp } from '../utils/format';
import { WorkstationPane } from '../components/WorkstationPane';
import { Divider } from '../components/Divider';
import { Callout } from '../components/Callout';

export function CaseDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState<CaseResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'evidence' | 'decision' | 'timeline'>('evidence');

  const loadCase = useCallback(async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [caseRes, graphRes, timelineRes] = await Promise.all([
        casesApi.get(parseInt(id, 10)),
        riskApi.getGraph(parseInt(id, 10)),
        casesApi.getTimeline(parseInt(id, 10)),
      ]);
      setCaseData(caseRes);
      setGraphData(graphRes);
      setTimelineData(timelineRes);
    } catch (err) {
      console.error('Failed to load case:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadCase();
  }, [loadCase]);

  const handleDecision = async (decision: 'approve' | 'verify' | 'review' | 'hold') => {
    if (!caseData) return;
    try {
      setDeciding(decision);
      await casesApi.decide(caseData.id, decision);
      await loadCase();
    } catch (err) {
      console.error('Decision failed:', err);
    } finally {
      setDeciding(null);
    }
  };

  const groupEvidence = (evidence: EvidenceItem[]) => {
    return {
      behavioral: evidence.filter((e) => e.category === 'behavioral'),
      graph: evidence.filter((e) => e.category === 'graph'),
      temporal: evidence.filter((e) => e.category === 'temporal'),
    };
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
        <div className="spinner-lg" />
      </div>
    );
  }

  if (!caseData) {
    return (
      <div style={{ textAlign: 'center', padding: '48px', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
        <p style={{ color: 'var(--color-text-muted)', marginBottom: '16px' }}>Case not found</p>
        <Link to="/cases" className="btn btn-primary">Back to Cases</Link>
      </div>
    );
  }

  const evidenceGroups = groupEvidence(caseData.evidence);
  const exceeded = caseData.risk_score > 0.41;

  return (
    <div>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        marginBottom: 'var(--space-loose)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => navigate('/cases')}
            className="btn btn-ghost btn-sm"
            aria-label="Back to Cases"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 'var(--font-semibold)', color: 'var(--color-text-primary)' }}>Case #{caseData.id}</h1>
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>{caseData.refund_id} · {caseData.customer_id}</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button onClick={loadCase} className="btn btn-secondary btn-sm">Refresh</button>
        </div>
      </div>

      {/* Three-pane Workstation */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '320px 1fr 360px',
        gap: 'var(--space-normal)',
        height: 'calc(100vh - var(--header-height) - 140px)',
        minHeight: '600px'
      }}>
        {/* Risk Panel - Left */}
        <WorkstationPane title="Risk Assessment" sticky className="workstation-pane-sticky">
          <ScoreDisplay
            score={caseData.risk_score}
            band={caseData.risk_band}
            threshold={0.41}
            recommendedAction={caseData.recommended_action}
            meta={[
              { label: 'Order ID', value: caseData.order_id },
              { label: 'Threshold', value: exceeded ? '0.41 (EXCEEDED)' : '0.41', valueClassName: exceeded ? 'risk-high' : '' },
              { label: 'Status', value: caseData.status === 'decided' ? 'DECIDED' : 'PENDING', valueClassName: caseData.status === 'decided' ? '' : 'accent' },
              { label: 'Created', value: formatTimestamp(caseData.created_at) },
            ]}
            onAction={handleDecision}
            disabled={caseData.status === 'decided' || !!deciding}
            loadingAction={deciding}
          />

          <Divider label="Key Metrics" />

          <MetricRowWithDescription
            label="Order ID"
            value={caseData.order_id}
            description="Original order reference"
          />
        </WorkstationPane>

        {/* Center Pane - Evidence / Decision / Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          {/* Tabs */}
          <div className="tabs" role="tablist" aria-label="Case detail sections">
            <button
              role="tab"
              aria-selected={activeTab === 'evidence'}
              onClick={() => setActiveTab('evidence')}
              className={`tabs-item ${activeTab === 'evidence' ? 'tabs-item-active' : ''}`}
            >
              Evidence
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'decision'}
              onClick={() => setActiveTab('decision')}
              className={`tabs-item ${activeTab === 'decision' ? 'tabs-item-active' : ''}`}
            >
              Decision
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'timeline'}
              onClick={() => setActiveTab('timeline')}
              className={`tabs-item ${activeTab === 'timeline' ? 'tabs-item-active' : ''}`}
            >
              Timeline
            </button>
          </div>

          {/* Tab Panels */}
          <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
            {/* Evidence Tab */}
            {activeTab === 'evidence' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-normal)' }}>
                <EvidenceCard category="behavioral" items={evidenceGroups.behavioral} />
                <EvidenceCard category="graph" items={evidenceGroups.graph} />
                <EvidenceCard category="temporal" items={evidenceGroups.temporal} />
              </div>
            )}

            {/* Decision Tab */}
            {activeTab === 'decision' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-normal)' }}>
                <div style={{
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-normal)'
                }}>
                  <h3 style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--font-semibold)', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-tight)' }}>Risk Assessment Summary</h3>
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)', lineHeight: 'var(--leading-relaxed)', marginBottom: 'var(--space-tight)' }}>
                    This refund event was scored <strong>{caseData.risk_score.toFixed(3)}</strong>
                    by the Sentinel production model (39 features: 18 behavioral + 15 graph + 6 temporal).
                    The frozen decision threshold is <strong>0.41</strong>.
                  </p>
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)', lineHeight: 'var(--leading-relaxed)' }}>
                    Based on the ActionPolicy, this places the event in the
                    <StatusBadge variant="risk" value={caseData.risk_band} />
                    band, recommending
                    <StatusBadge variant="action" value={caseData.recommended_action} />.
                  </p>
                </div>

                {caseData.status === 'decided' && (
                  <Callout variant="production" title="Decision Recorded">
                    <p style={{ color: 'var(--color-risk-low-text)' }}>
                      Action: <strong>{caseData.decision?.toUpperCase()}</strong>
                      {caseData.decided_at && ` · ${formatTimestamp(caseData.decided_at)}`}
                    </p>
                  </Callout>
                )}

                <div style={{
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  overflow: 'hidden'
                }}>
                  <div style={{ padding: 'var(--space-tight) var(--space-normal)', borderBottom: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-tertiary)' }}>
                    <h3 style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--font-semibold)', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)' }}>Feature Values (Production Model)</h3>
                  </div>
                  <details style={{ padding: 'var(--space-normal)' }}>
                    <summary style={{ cursor: 'pointer', color: 'var(--color-primary)', marginBottom: 'var(--space-tight)', fontSize: 'var(--text-sm)', fontWeight: 'var(--font-medium)' }}>
                      Show all 39 features
                    </summary>
                    <pre style={{
                      fontSize: '10px',
                      lineHeight: '1.5',
                      maxHeight: '400px',
                      overflow: 'auto',
                      backgroundColor: 'var(--color-bg-tertiary)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      padding: 'var(--space-tight)',
                      fontFamily: 'var(--font-mono)'
                    }}>
                      {JSON.stringify(caseData, null, 2)}
                    </pre>
                  </details>
                </div>
              </div>
            )}

            {/* Timeline Tab */}
            {activeTab === 'timeline' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-normal)' }}>
                {timelineData ? (
                  <>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-normal)' }}>
                      <MetricRowWithDescription label="Target Customer" value={timelineData.target_customer} />
                      <MetricRowWithDescription label="Target Refund" value={timelineData.target_refund_id} />
                      <MetricRowWithDescription label="Refund Time" value={formatTimestamp(timelineData.target_timestamp)} />
                      <MetricRowWithDescription label="Component Size" value={`${timelineData.component_size} accounts`} description="Connected component members" />
                    </div>
                    {timelineData.events.length === 0 ? (
                      <div style={{ textAlign: 'center', padding: '48px', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
                        <p style={{ color: 'var(--color-text-muted)' }}>
                          No events in the connected component within the {timelineData.window_hours}-hour window before the refund.
                        </p>
                      </div>
                    ) : (
                      <CompactTable
                        columns={[
                          {
                            key: 'relative',
                            header: 'TIME (RELATIVE)',
                            render: (_: TimelineEvent, idx: number) => {
                              const event = timelineData!.events[idx];
                              const eventTime = new Date(event.timestamp);
                              const targetTime = new Date(timelineData!.target_timestamp);
                              const diffMinutes = Math.round((eventTime.getTime() - targetTime.getTime()) / 60000);
                              const relativeTime = diffMinutes < 0
                                ? `${Math.abs(diffMinutes)} min before`
                                : diffMinutes > 0
                                ? `${diffMinutes} min after`
                                : 'at refund time';
                              return <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>{relativeTime}</span>;
                            },
                          },
                          {
                            key: 'absolute',
                            header: 'ABSOLUTE TIME',
                            render: (_: TimelineEvent, idx: number) => (
                              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
                                {formatTimestamp(timelineData!.events[idx].timestamp)}
                              </span>
                            ),
                          },
                          {
                            key: 'customer',
                            header: 'CUSTOMER',
                            render: (_: TimelineEvent, idx: number) => {
                              const event = timelineData!.events[idx];
                              return (
                                <span style={{
                                  fontFamily: 'var(--font-mono)',
                                  fontSize: 'var(--text-xs)',
                                  color: event.is_target ? 'var(--color-primary)' : 'var(--color-text-primary)',
                                  fontWeight: event.is_target ? 'var(--font-medium)' : 'normal'
                                }}>
                                  {event.customer_id}
                                  {event.is_target && ' (target)'}
                                </span>
                              );
                            },
                          },
                          {
                            key: 'event_type',
                            header: 'EVENT TYPE',
                            render: (_: TimelineEvent, idx: number) => {
                              const event = timelineData!.events[idx];
                              return (
                                <StatusBadge
                                  variant={event.event_type === 'refund' ? 'risk' : 'action'}
                                  value={event.event_type === 'refund' ? 'HIGH' : 'approve'}
                                />
                              );
                            },
                          },
                        ]}
                        data={timelineData.events}
                        keyExtractor={(_, idx) => idx}
                        emptyMessage="No events in this window"
                      />
                    )}
                  </>
                ) : (
                  <div style={{ textAlign: 'center', padding: '48px', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
                    <p style={{ color: 'var(--color-text-muted)' }}>Loading timeline...</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Graph Pane - Right */}
        <WorkstationPane title="Network Graph" sticky className="workstation-pane-sticky">
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
              <GraphViz data={graphData} width={360} height={500} />
            </div>
            {graphData && (
              <div style={{
                marginTop: 'var(--space-loose)',
                paddingTop: 'var(--space-loose)',
                borderTop: '1px solid var(--color-border)',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: 'var(--space-loose)'
              }}>
                <MetricRowWithDescription
                  label="Connected Customers"
                  value={graphData.stats.connected_customers}
                  description="Customers in the connected component"
                />
                <MetricRowWithDescription
                  label="Shared Devices"
                  value={graphData.stats.shared_devices}
                  description="Device entities shared with target"
                />
                <MetricRowWithDescription
                  label="Shared Addresses"
                  value={graphData.stats.shared_addresses}
                  description="Address entities shared with target"
                />
                <MetricRowWithDescription
                  label="Shared Payments"
                  value={graphData.stats.shared_payments}
                  description="Payment tokens shared with target"
                />
              </div>
            )}
          </div>
        </WorkstationPane>
      </div>
    </div>
  );
}