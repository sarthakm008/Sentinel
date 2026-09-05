// Overview Page - Operations Command Center

import { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { casesApi, demoApi, evaluationApi } from '../api';
import { CaseResponse, EvaluationResponse } from '../types';
import { DataRow } from '../components/DataRow';
import { PageHeader } from '../components/PageHeader';
import { MetricCard } from '../components/MetricCard';
import { Callout } from '../components/Callout';
import { Divider } from '../components/Divider';
import { RiskPulse } from '../components/RiskPulse';
import { formatCurrency, formatLossVsBaseline } from '../utils/format';
import { useIntegrationStatus } from '../contexts/IntegrationStatusContext';

export function Overview() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total: 0,
    highRisk: 0,
    reviewQueue: 0,
    approved: 0,
    estimatedExposure: 0,
    byBand: { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 },
  });
  const [recentCases, setRecentCases] = useState<CaseResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [evalData, setEvalData] = useState<EvaluationResponse | null>(null);
  const { status: integrationStatus } = useIntegrationStatus();

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const [casesRes, evalRes] = await Promise.all([
        casesApi.list({ size: 50 }),
        evaluationApi.get(),
      ]);
      setRecentCases(casesRes.cases);

      const byBand = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
      casesRes.cases.forEach((c) => {
        byBand[c.risk_band] = (byBand[c.risk_band] || 0) + 1;
      });

      const highRisk = byBand.HIGH + byBand.CRITICAL;
      const reviewQueue = casesRes.cases.filter(
        (c) => c.status === 'pending' && (c.recommended_action === 'review' || c.recommended_action === 'hold')
      ).length;
      const approved = casesRes.cases.filter((c) => c.recommended_action === 'approve').length;
      const exposure = casesRes.cases
        .filter((c) => c.risk_band === 'HIGH' || c.risk_band === 'CRITICAL')
        .reduce((sum, c) => sum + c.risk_score * 10000, 0);

      setStats({
        total: casesRes.total,
        highRisk,
        reviewQueue,
        approved,
        estimatedExposure: exposure,
        byBand,
      });
      setEvalData(evalRes);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const handleRunDemo = async () => {
    try {
      await demoApi.run();
      await loadDashboard();
    } catch (err) {
      console.error('Demo failed:', err);
    }
  };

  const handleResetDemo = async () => {
    try {
      await demoApi.reset();
      await loadDashboard();
    } catch (err) {
      console.error('Reset failed:', err);
    }
  };

  const sentinel = evalData?.production_candidate;
  const lossInfo = sentinel ? formatLossVsBaseline(sentinel.loss_avoided_vs_baseline) : null;

  const latestCases = recentCases.slice(0, 15);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
        <div className="spinner-lg" />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Operations"
        subtitle="Live risk operations console"
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={handleRunDemo} className="btn btn-primary btn-sm">Run Demo</button>
            <button onClick={handleResetDemo} className="btn btn-secondary btn-sm">Reset Demo</button>
          </div>
        }
      />

      {/* System Status Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '24px',
        padding: '12px 16px',
        backgroundColor: 'var(--color-bg-tertiary)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        marginBottom: 'var(--space-loose)'
      }}>
        <div className="sidebar-integration-status" style={{ padding: '0', backgroundColor: 'transparent' }}>
          <span className="dot" style={{ backgroundColor: integrationStatus?.monitoring ? 'var(--color-status-monitoring)' : 'var(--color-text-muted)' }} />
          <span style={{ fontWeight: 'var(--font-semibold)', fontSize: 'var(--text-sm)' }}>
            {integrationStatus?.monitoring ? 'MONITORING ACTIVE' : 'MONITORING STOPPED'}
          </span>
        </div>
        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border)' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>Refunds</span>
          <span className="metric-card-value" style={{ fontSize: 'var(--text-sm)' }}>{integrationStatus?.events_received ?? 0}</span>
        </div>
        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border)' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>Queue</span>
          <span className="metric-card-value risk-medium" style={{ fontSize: 'var(--text-sm)' }}>{integrationStatus?.queue_pending ?? 0}</span>
        </div>
        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border)' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>Processed</span>
          <span className="metric-card-value risk-low" style={{ fontSize: 'var(--text-sm)' }}>{integrationStatus?.events_processed ?? 0}</span>
        </div>
        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border)' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>Failed</span>
          <span className="metric-card-value risk-high" style={{ fontSize: 'var(--text-sm)' }}>{integrationStatus?.events_failed ?? 0}</span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="metric-row">
        <MetricCard label="Total Cases" value={stats.total} />
        <MetricCard label="Review Queue" value={stats.reviewQueue} valueClassName="risk-medium" />
        <MetricCard label="High + Critical" value={stats.highRisk} valueClassName="risk-high" />
        <MetricCard label="Est. Exposure" value={formatCurrency(stats.estimatedExposure)} valueClassName="accent" />
      </div>

      {/* Live Refund Activity */}
      <div style={{ marginBottom: 'var(--space-loose)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <h2 style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--font-semibold)', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)' }}>Live Refund Activity</h2>
          <Link to="/cases" className="btn btn-ghost btn-sm">View All Cases</Link>
        </div>
        <div style={{
          backgroundColor: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          overflow: 'hidden'
        }}>
          {latestCases.length === 0 ? (
            <div className="empty-state" style={{ padding: '32px' }}>
              <p style={{ color: 'var(--color-text-muted)' }}>No recent refund activity</p>
            </div>
          ) : (
            latestCases.map((c) => (
              <DataRow
                key={c.id}
                case={c}
                onClick={() => navigate(`/cases/${c.id}`)}
              />
            ))
          )}
        </div>
      </div>

      <Divider label="Risk Distribution" />

      {/* Risk Distribution */}
      <RiskPulse stats={stats.byBand} />

      <Divider label="Production Model" />

      {/* Production Model Summary */}
      {sentinel && (
        <Callout
          variant="production"
          title="Production Candidate: Full Sentinel (39 features)"
          metrics={[
            { label: 'PR-AUC', value: sentinel.pr_auc.toFixed(4) },
            { label: 'Recall', value: sentinel.recall.toFixed(4) },
            { label: 'Precision', value: sentinel.precision.toFixed(4) },
            { label: 'Threshold', value: sentinel.frozen_threshold.toFixed(2) },
            { label: 'Samples', value: sentinel.sample_count.toLocaleString() },
            { label: lossInfo?.label || 'Loss vs Baseline', value: lossInfo?.value || '—', valueClassName: lossInfo?.color === 'success' ? 'risk-low' : 'risk-high' },
          ]}
        >
          <Link to="/evaluation" className="btn btn-secondary btn-sm" style={{ width: 'fit-content', marginTop: '8px' }}>
            View Full Evaluation
          </Link>
        </Callout>
      )}
    </div>
  );
}