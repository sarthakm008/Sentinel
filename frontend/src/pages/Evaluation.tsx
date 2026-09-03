// Evaluation page

import { useEffect, useState } from 'react';
import { evaluationApi } from '../api';
import { EvaluationResponse } from '../types';
import { EvaluationTable } from '../components/EvaluationTable';

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

  const formatCurrency = (n: number) => `₹${n.toLocaleString(undefined, { minimumFractionDigits: 0 })}`;

  const formatLossVsBaseline = (lossAvoided: number) => {
    if (lossAvoided >= 0) {
      return `Loss Avoided: ${formatCurrency(lossAvoided)}`;
    } else {
      return `Additional Loss vs Baseline: ${formatCurrency(Math.abs(lossAvoided))}`;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12 text-text-muted">
        Failed to load evaluation data.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Model Evaluation</h1>
        <p className="text-text-secondary mt-1">
          Performance metrics from the locked benchmark. Production candidate clearly separated from experimental models.
        </p>
      </div>

      {/* Production Candidate */}
      <div className="card p-6 border-success border">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-success flex items-center gap-2">
              <span className="px-2 py-0.5 bg-success text-success-foreground text-xs rounded">PRODUCTION CANDIDATE</span>
              Full Sentinel (39 features)
            </h2>
            <p className="text-success mt-1">
              Behavioral (18) + Graph (15) + Temporal (6) = 39 features. Frozen threshold: {data.production_candidate.frozen_threshold.toFixed(2)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-success">PR-AUC: {data.production_candidate.pr_auc.toFixed(4)}</p>
            <p className="text-sm text-success">{formatLossVsBaseline(data.production_candidate.loss_avoided_vs_baseline)}</p>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="bg-surface p-3 rounded"><p className="text-success">ROC-AUC</p><p className="font-bold">{data.production_candidate.roc_auc.toFixed(4)}</p></div>
          <div className="bg-surface p-3 rounded"><p className="text-success">Precision</p><p className="font-bold">{data.production_candidate.precision.toFixed(4)}</p></div>
          <div className="bg-surface p-3 rounded"><p className="text-success">Recall</p><p className="font-bold">{data.production_candidate.recall.toFixed(4)}</p></div>
          <div className="bg-surface p-3 rounded"><p className="text-success">F1</p><p className="font-bold">{data.production_candidate.f1.toFixed(4)}</p></div>
        </div>
      </div>

      {/* Ablation Study */}
      <EvaluationTable
        title="Ablation Study: Held-Out Standard A-E Test Set"
        models={data.ablation}
        highlightModel="Sentinel"
      />

      {/* Out-of-Distribution: Type F */}
      <EvaluationTable
        title="Out-of-Distribution: Ring Type F (Structural Shift)"
        models={data.type_f}
        highlightModel="Sentinel"
      />

      {/* Future Period Holdout */}
      <EvaluationTable
        title="Temporal Holdout: Future Period (Days 120-180)"
        models={data.future_period}
        highlightModel="Sentinel"
      />

      {/* Phase 5 Experiment */}
      <div className="card p-6 border-danger border">
        <h2 className="text-lg font-semibold text-danger flex items-center gap-2 mb-4">
          <span className="px-2 py-0.5 bg-danger text-danger-foreground text-xs rounded">EXPERIMENTAL / REJECTED</span>
          Phase 5: Graph-Temporal Interaction Experiment
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="bg-surface p-4 rounded">
            <p className="text-danger font-medium">Feature Tested</p>
            <p className="font-mono text-text-primary">{data.phase5_experiment.feature}</p>
          </div>
          <div className="bg-surface p-4 rounded">
            <p className="text-danger font-medium">Model</p>
            <p className="font-mono text-text-primary">{data.phase5_experiment.model}</p>
          </div>
          <div className="bg-surface p-4 rounded">
            <p className="text-danger font-medium">ΔPR-AUC (vs Full Sentinel)</p>
            <p className="font-bold text-text-primary">{data.phase5_experiment.delta_pr_auc.toFixed(4)}</p>
          </div>
          <div className="bg-surface p-4 rounded">
            <p className="text-danger font-medium">95% Bootstrap CI</p>
            <p className="font-mono text-text-primary">[{data.phase5_experiment.ci_lower.toFixed(4)}, {data.phase5_experiment.ci_upper.toFixed(4)}]</p>
          </div>
          <div className="bg-surface p-4 rounded md:col-span-2">
            <p className="text-danger font-medium">Decision</p>
            <p className="font-bold text-danger">{data.phase5_experiment.decision}</p>
            <p className="text-danger mt-1">{data.phase5_experiment.reason}</p>
          </div>
        </div>
        <div className="mt-4 p-4 bg-surface rounded border border-danger">
          <p className="text-sm text-text-secondary">
            <strong>Key Principle:</strong> The interaction feature <code className="font-mono bg-bg-tertiary px-1 rounded">{data.phase5_experiment.feature}</code>
            was tested as a 40th feature added to the 39-feature production model. The paired bootstrap 95% confidence interval
            for ΔPR-AUC includes zero, meaning the improvement is not statistically significant. Per the pre-registered decision gate,
            the feature is NOT deployed. The production candidate remains the 39-feature Full Sentinel model.
          </p>
        </div>
      </div>

      {/* Frozen Thresholds */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-4">Frozen Validation Thresholds</h2>
        <p className="text-sm text-text-secondary mb-4">
          Thresholds selected by minimizing validation expected financial loss (review cost: ₹50, friction cost: ₹150).
          These are frozen and used for all test set evaluations.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-2 text-left font-semibold text-text-secondary">Model</th>
                <th className="px-4 py-2 text-right font-semibold text-text-secondary">Threshold</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {Object.entries(data.thresholds).map(([model, thresh]) => (
                <tr key={model}>
                  <td className="px-4 py-2 font-medium text-text-primary">{model}</td>
                  <td className="px-4 py-2 text-right font-mono text-text-secondary">{Number(thresh).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Methodology Note */}
      <div className="card p-6 border-primary border">
        <h3 className="font-semibold text-primary mb-2">Evaluation Methodology</h3>
        <ul className="text-sm text-primary space-y-1 list-disc list-inside">
          <li>Group-aware splits: no customer/device/address/payment leakage between train/val/test</li>
          <li>Ring Type F (structural shift) held out exclusively in test set</li>
          <li>Future period holdout: days 120-180 of 180-day timeline</li>
          <li>Thresholds frozen on validation set only; test set touched once</li>
          <li>Financial cost model: FN = refund amount, FP = review + friction cost</li>
          <li>All results reproducible from fixed seed (42)</li>
        </ul>
      </div>
    </div>
  );
}

function formatCurrency(n: number): string {
  return `₹${n.toLocaleString(undefined, { minimumFractionDigits: 0 })}`;
}

function formatLossVsBaseline(lossAvoided: number): string {
  if (lossAvoided >= 0) {
    return `Loss Avoided: ${formatCurrency(lossAvoided)}`;
  } else {
    return `Additional Loss vs Baseline: ${formatCurrency(Math.abs(lossAvoided))}`;
  }
}