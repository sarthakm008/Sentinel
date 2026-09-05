// Evaluation Page - Model Intelligence Console

import { useEffect, useState } from 'react';
import { evaluationApi } from '../api';
import { EvaluationResponse, EvaluationMetrics } from '../types';
import { CompactTable } from '../components/CompactTable';
import { PageHeader } from '../components/PageHeader';
import { Callout } from '../components/Callout';
import { Divider } from '../components/Divider';
import { formatCurrency, formatLossVsBaseline } from '../utils/format';

const evaluationColumns = [
  {
    key: 'model_name',
    header: 'MODEL',
    render: (m: EvaluationMetrics) => (
      <span style={{ fontWeight: 'var(--font-medium)', color: 'var(--color-text-primary)' }}>
        {m.model_name}
      </span>
    ),
    className: 'font-medium text-text-primary',
  },
  {
    key: 'pr_auc',
    header: 'PR-AUC',
    render: (m: EvaluationMetrics) => (
      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 'var(--font-medium)', color: 'var(--color-text-primary)' }}>
        {m.pr_auc.toFixed(4)}
      </span>
    ),
    className: 'text-right',
  },
  {
    key: 'roc_auc',
    header: 'ROC-AUC',
    render: (m: EvaluationMetrics) => (
      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)' }}>
        {m.roc_auc.toFixed(4)}
      </span>
    ),
    className: 'text-right',
  },
  {
    key: 'precision',
    header: 'PRECISION',
    render: (m: EvaluationMetrics) => (
      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)' }}>
        {m.precision.toFixed(4)}
      </span>
    ),
    className: 'text-right',
  },
  {
    key: 'recall',
    header: 'RECALL',
    render: (m: EvaluationMetrics) => (
      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)' }}>
        {m.recall.toFixed(4)}
      </span>
    ),
    className: 'text-right',
  },
  {
    key: 'f1',
    header: 'F1',
    render: (m: EvaluationMetrics) => (
      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)' }}>
        {m.f1.toFixed(4)}
      </span>
    ),
    className: 'text-right',
  },
  {
    key: 'total_expected_loss',
    header: 'TOTAL LOSS',
    render: (m: EvaluationMetrics) => (
      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)' }}>
        {formatCurrency(m.total_expected_loss)}
      </span>
    ),
    className: 'text-right',
  },
  {
    key: 'loss_avoided_vs_baseline',
    header: 'Δ LOSS VS BASELINE',
    render: (m: EvaluationMetrics) => {
      const lossInfo = formatLossVsBaseline(m.loss_avoided_vs_baseline);
      return (
        <span style={{
          fontFamily: 'var(--font-mono)',
          color: lossInfo.color === 'success' ? 'var(--color-risk-low)' : 'var(--color-risk-high)'
        }}>
          {lossInfo.label}: {lossInfo.value}
        </span>
      );
    },
    className: 'text-right',
  },
  {
    key: 'frozen_threshold',
    header: 'THRESHOLD',
    render: (m: EvaluationMetrics) => (
      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)' }}>
        {m.frozen_threshold.toFixed(2)}
      </span>
    ),
    className: 'text-right',
  },
];

const isProductionModel = (name: string) => name === 'sentinel' || name === 'Full Sentinel (Production)';
const isRejectedModel = (name: string) => name.includes('Interaction') || name === 'Sentinel + Interaction';

const rowClass = (name: string) => {
  if (isProductionModel(name)) return 'bg-risk-low-bg/30';
  if (isRejectedModel(name)) return 'bg-risk-high-bg/20';
  return '';
};

const modelBadge = (name: string) => {
  if (isProductionModel(name)) return (
    <span style={{
      marginLeft: '8px',
      padding: '2px 6px',
      fontSize: '10px',
      fontWeight: 'var(--font-medium)',
      backgroundColor: 'var(--color-risk-low-bg)',
      color: 'var(--color-risk-low)',
      border: '1px solid var(--color-risk-low-border)',
      borderRadius: 'var(--radius-sm)'
    }}>
      PRODUCTION
    </span>
  );
  if (isRejectedModel(name)) return (
    <span style={{
      marginLeft: '8px',
      padding: '2px 6px',
      fontSize: '10px',
      fontWeight: 'var(--font-medium)',
      backgroundColor: 'var(--color-risk-high-bg)',
      color: 'var(--color-risk-high)',
      border: '1px solid var(--color-risk-high-border)',
      borderRadius: 'var(--radius-sm)'
    }}>
      REJECTED
    </span>
  );
  return null;
};

export function Evaluation() {
  const [data, setData] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEvaluation();
  }, []);

  const loadEvaluation = async () => {
    try {
      setLoading(true);
      const res = await evaluationApi.get();
      setData(res);
    } catch (err) {
      console.error('Failed to load evaluation:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
        <div className="spinner-lg" />
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '48px', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
        <p style={{ color: 'var(--color-text-muted)' }}>Failed to load evaluation data.</p>
      </div>
    );
  }

  const prod = data.production_candidate;
  const lossInfo = formatLossVsBaseline(prod.loss_avoided_vs_baseline);

  return (
    <div>
      <PageHeader
        title="Model Evaluation"
        subtitle="Locked benchmark metrics · Production candidate separated from experimental models"
      />

      {/* Production Candidate - Hero */}
      <Callout
        variant="production"
        title="Production Candidate: Full Sentinel (39 features)"
        metrics={[
          { label: 'PR-AUC', value: prod.pr_auc.toFixed(4), valueClassName: 'accent' },
          { label: 'ROC-AUC', value: prod.roc_auc.toFixed(4) },
          { label: 'Precision', value: prod.precision.toFixed(4) },
          { label: 'Recall', value: prod.recall.toFixed(4) },
          { label: 'F1', value: prod.f1.toFixed(4) },
          { label: 'Threshold', value: prod.frozen_threshold.toFixed(2) },
          { label: 'Samples', value: prod.sample_count.toLocaleString() },
          { label: lossInfo.label, value: lossInfo.value, valueClassName: lossInfo.color === 'success' ? 'risk-low' : 'risk-high' },
        ]}
      >
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)', marginTop: 'var(--space-tight)' }}>
          PR-AUC: <strong>{prod.pr_auc.toFixed(4)}</strong> · Recall: <strong>{prod.recall.toFixed(4)}</strong> · Precision: <strong>{prod.precision.toFixed(4)}</strong> · {lossInfo.label}: <strong>{lossInfo.value}</strong>
        </p>
      </Callout>

      <Divider label="Ablation Study: Held-Out Test Set" />

      {/* Ablation Study */}
      <CompactTable
        columns={evaluationColumns}
        data={data.ablation.map((m) => ({
          ...m,
          _rowClass: rowClass(m.model_name),
          model_name: (
            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {m.model_name}
              {modelBadge(m.model_name)}
            </span>
          ),
        }))}
        keyExtractor={(m, idx) => idx}
        emptyMessage="No ablation data"
      />

      <Divider label="Stress Tests" />

      {/* Stress Tests - Responsive Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(720px, 1fr))', gap: 'var(--space-loose)' }}>
        {/* Type F */}
        <div style={{ minWidth: 0 }}>
          <h3 style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--font-semibold)', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-tight)' }}>
            Type F — Structural Shift
          </h3>
          <CompactTable
            columns={evaluationColumns}
            data={data.type_f.map((m) => ({
              ...m,
              _rowClass: rowClass(m.model_name),
              model_name: (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {m.model_name}
                  {modelBadge(m.model_name)}
                </span>
              ),
            }))}
            keyExtractor={(m, idx) => idx}
            emptyMessage="No Type F data"
            scrollable={true}
          />
        </div>

        {/* Future Period */}
        <div style={{ minWidth: 0 }}>
          <h3 style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--font-semibold)', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-tight)' }}>
            Future Period — Days 120–180
          </h3>
          <CompactTable
            columns={evaluationColumns}
            data={data.future_period.map((m) => ({
              ...m,
              _rowClass: rowClass(m.model_name),
              model_name: (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {m.model_name}
                  {modelBadge(m.model_name)}
                </span>
              ),
            }))}
            keyExtractor={(m, idx) => idx}
            emptyMessage="No future period data"
            scrollable={true}
          />
        </div>
      </div>

      <Divider label="Phase 5 Experiment" />

      {/* Phase 5 Experiment */}
      <Callout
        variant="rejected"
        title="Phase 5: Graph-Temporal Interaction Experiment"
        metrics={[
          { label: 'Feature Tested', value: data.phase5_experiment.feature },
          { label: 'Model', value: data.phase5_experiment.model },
          { label: 'ΔPR-AUC (vs Full Sentinel)', value: data.phase5_experiment.delta_pr_auc.toFixed(4) },
          { label: '95% Bootstrap CI', value: `[${data.phase5_experiment.ci_lower.toFixed(4)}, ${data.phase5_experiment.ci_upper.toFixed(4)}]` },
        ]}
      >
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)', lineHeight: 'var(--leading-relaxed)' }}>
          <strong>Decision:</strong> {data.phase5_experiment.decision} — {data.phase5_experiment.reason}
        </p>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--text-sm)', lineHeight: 'var(--leading-relaxed)', marginTop: 'var(--space-tight)' }}>
          <strong>Key Principle:</strong> The interaction feature <code style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', backgroundColor: 'var(--color-bg-tertiary)', padding: '1px 4px', borderRadius: 'var(--radius-sm)', color: 'var(--color-text-primary)' }}>{data.phase5_experiment.feature}</code>
          was tested as a 40th feature added to the 39-feature production model. The paired bootstrap 95% confidence interval
          for ΔPR-AUC includes zero, meaning the improvement is not statistically significant. Per the pre-registered decision gate,
          the feature is NOT deployed. The production candidate remains the 39-feature Full Sentinel model.
        </p>
      </Callout>

      <Divider label="Frozen Validation Thresholds" />

      {/* Frozen Thresholds */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 'var(--space-tight)' }}>
        {Object.entries(data.thresholds).map(([model, thresh]) => (
          <div key={model} style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
            padding: 'var(--space-tight)',
            backgroundColor: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)'
          }}>
            <div style={{ fontSize: 'var(--text-xs)', fontWeight: 'var(--font-semibold)', textTransform: 'uppercase', letterSpacing: '0.03em', color: 'var(--color-text-secondary)' }}>
              {model.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-sm)', fontWeight: 'var(--font-medium)', color: 'var(--color-text-primary)' }}>
              {Number(thresh).toFixed(2)}
            </div>
          </div>
        ))}
      </div>

      <Divider label="Methodology" />

      {/* Methodology */}
      <div style={{ borderLeft: '4px solid var(--color-primary)', padding: 'var(--space-normal)', backgroundColor: 'var(--color-surface)', borderRadius: 'var(--radius-md)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: 'var(--space-tight)' }}>
          <span style={{
            padding: '2px 6px',
            fontSize: 'var(--text-xs)',
            fontWeight: 'var(--font-medium)',
            backgroundColor: 'var(--color-primary-light)',
            color: 'var(--color-primary)',
            border: '1px solid var(--color-primary)',
            borderRadius: 'var(--radius-sm)'
          }}>
            METHODOLOGY
          </span>
          <h3 style={{ fontWeight: 'var(--font-semibold)', color: 'var(--color-primary)' }}>Evaluation Methodology</h3>
        </div>
        <ul style={{ fontSize: 'var(--text-sm)', color: 'var(--color-primary)', lineHeight: 'var(--leading-relaxed)', paddingLeft: '20px' }}>
          <li>Group-aware splits: no customer/device/address/payment leakage between train/val/test</li>
          <li>Ring Type F (structural shift) held out exclusively in test set</li>
          <li>Future period holdout: days 120–180 of 180-day timeline</li>
          <li>Thresholds frozen on validation set only; test set touched once</li>
          <li>Financial cost model: FN = refund amount, FP = review + friction cost</li>
          <li>All results reproducible from fixed seed (42)</li>
        </ul>
      </div>
    </div>
  );
}