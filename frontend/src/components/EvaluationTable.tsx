// EvaluationTable component - displays model evaluation metrics

import { EvaluationMetrics } from '../types';

interface EvaluationTableProps {
  title: string;
  models: EvaluationMetrics[];
  highlightModel?: string;
}

export function EvaluationTable({ title, models, highlightModel }: EvaluationTableProps) {
  const formatNumber = (n: number) => n.toLocaleString();
  const formatCurrency = (n: number) => `₹${n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
  const formatPercent = (n: number) => `${(n * 100).toFixed(1)}%`;

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Model</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">PR-AUC</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">ROC-AUC</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Precision</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Recall</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">F1</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Total Loss</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Loss Avoided</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Threshold</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {models.map((m, idx) => {
              const isHighlight = highlightModel && m.model_name.includes(highlightModel);
              const isProduction = m.model_name.includes('Sentinel') && !m.model_name.includes('Interaction');
              return (
                <tr
                  key={idx}
                  className={isHighlight ? 'bg-blue-50' : isProduction ? 'bg-green-50' : ''}
                >
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {m.model_name}
                    {isProduction && (
                      <span className="ml-2 px-1.5 py-0.5 text-xs bg-green-100 text-green-800 rounded">
                        PRODUCTION
                      </span>
                    )}
                    {isHighlight && !isProduction && (
                      <span className="ml-2 px-1.5 py-0.5 text-xs bg-red-100 text-red-800 rounded">
                        REJECTED
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-mono font-medium text-gray-900">{m.pr_auc.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right font-mono text-gray-700">{m.roc_auc.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right font-mono text-gray-700">{m.precision.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right font-mono text-gray-700">{m.recall.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right font-mono text-gray-700">{m.f1.toFixed(4)}</td>
                  <td className="px-4 py-3 text-right font-mono text-gray-700">{formatCurrency(m.total_expected_loss)}</td>
                  <td className="px-4 py-3 text-right font-mono">
                    <span className={m.loss_avoided_vs_baseline >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {m.loss_avoided_vs_baseline >= 0 ? '−' : '+'}{formatCurrency(Math.abs(m.loss_avoided_vs_baseline))}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-gray-700">{m.frozen_threshold.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}