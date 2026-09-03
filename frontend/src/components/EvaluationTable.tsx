// EvaluationTable component - displays model evaluation metrics

import { EvaluationMetrics } from '../types';

interface EvaluationTableProps {
  title: string;
  models: EvaluationMetrics[];
  highlightModel?: string;
}

const formatCurrency = (n: number) => `₹${n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

const formatLossVsBaseline = (lossAvoided: number) => {
  if (lossAvoided >= 0) {
    return { label: 'Loss Avoided', value: formatCurrency(lossAvoided), color: 'text-success' };
  } else {
    return { label: 'Additional Loss', value: formatCurrency(Math.abs(lossAvoided)), color: 'text-danger' };
  }
};

export function EvaluationTable({ title, models, highlightModel }: EvaluationTableProps) {
  const formatNumber = (n: number) => n.toLocaleString();
  const formatPercent = (n: number) => `${(n * 100).toFixed(1)}%`;

  return (
    <div className="card overflow-hidden">
      <div className="bg-bg-tertiary px-4 py-3 border-b border-border">
        <h3 className="font-semibold text-text-primary">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-bg-tertiary">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-text-secondary">Model</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">PR-AUC</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">ROC-AUC</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">Precision</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">Recall</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">F1</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">Total Loss</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">Loss vs Baseline</th>
              <th className="px-4 py-3 text-right font-semibold text-text-secondary">Threshold</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {models.map((m, idx) => {
              const isHighlight = highlightModel && m.model_name.includes(highlightModel);
              const isProduction = m.model_name.includes('Sentinel') && !m.model_name.includes('Interaction');
              const lossInfo = (() => {
                if (m.loss_avoided_vs_baseline >= 0) {
                  return { label: 'Loss Avoided', value: formatCurrency(m.loss_avoided_vs_baseline), color: 'text-success' };
                } else {
                  return { label: 'Additional Loss', value: formatCurrency(Math.abs(m.loss_avoided_vs_baseline)), color: 'text-danger' };
                }
              })();
              return (
                <tr
                  key={idx}
                  className={isHighlight ? 'bg-primary-light' : isProduction ? 'bg-success-light' : ''}
                >
                  <td className="px-4 py-3 font-medium text-text-primary">
                    {m.model_name}
                    {isProduction && (
                      <span className="ml-2 px-1.5 py-0.5 text-xs bg-success-light text-success rounded">
                        PRODUCTION
                      </span>
                    )}
                    {isHighlight && !isProduction && (
                      <span className="ml-2 px-1.5 py-0.5 text-xs bg-danger-light text-danger rounded">
                        REJECTED
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-mono font-medium text-text-primary">{m.pr_auc.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right font-mono text-text-secondary">{m.roc_auc.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right font-mono text-text-secondary">{m.precision.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right font-mono text-text-secondary">{m.recall.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right font-mono text-text-secondary">{m.f1.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right font-mono text-text-secondary">{formatCurrency(m.total_expected_loss)}</td>
                  <td className="px-4 py-3 text-right font-mono">
                    <span className={lossInfo.color}>
                      {lossInfo.label}: {lossInfo.value}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-text-secondary">{m.frozen_threshold.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}