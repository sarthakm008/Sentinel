// ScoreDisplay Component

import { StatusBadge } from './StatusBadge';

interface ScoreDisplayProps {
  score: number;
  band: string;
  threshold: number;
  recommendedAction: string;
  meta?: Array<{ label: string; value: string | number }>;
  onAction?: (action: string) => void;
  disabled?: boolean;
  loadingAction?: string | null;
}

const riskFillColors: Record<string, string> = {
  LOW: 'var(--color-risk-low)',
  MEDIUM: 'var(--color-risk-medium)',
  HIGH: 'var(--color-risk-high)',
  CRITICAL: 'var(--color-risk-critical)',
};

const actionStyles: Record<string, { base: string; hover: string }> = {
  approve: { base: 'bg-action-approve text-white border-action-approve', hover: 'hover:bg-emerald-700 hover:border-emerald-700' },
  verify: { base: 'bg-action-verify text-white border-action-verify', hover: 'hover:bg-blue-700 hover:border-blue-700' },
  review: { base: 'bg-action-review text-white border-action-review', hover: 'hover:bg-amber-700 hover:border-amber-700' },
  hold: { base: 'bg-action-hold text-white border-action-hold', hover: 'hover:bg-red-700 hover:border-red-700' },
};

const actionLabels: Record<string, string> = {
  approve: 'APPROVE',
  verify: 'VERIFY',
  review: 'REVIEW',
  hold: 'HOLD',
};

export function ScoreDisplay({
  score,
  band,
  threshold,
  recommendedAction,
  meta,
  onAction,
  disabled,
  loadingAction,
}: ScoreDisplayProps) {
  const fillColor = riskFillColors[band] || riskFillColors.LOW;
  const exceeded = score > threshold;

  return (
    <div className="score-display">
      <div className="score-display-header">
        <span className="score-display-label">Risk Score</span>
        <span className="score-display-value">{score.toFixed(3)}</span>
      </div>
      <div className="score-display-bar">
        <div
          className="score-display-fill"
          style={{ width: `${Math.min(score * 100, 100)}%`, backgroundColor: fillColor }}
        />
      </div>
      <div className="score-display-badges">
        <StatusBadge variant="risk" value={band} className="text-sm" />
        <StatusBadge variant="action" value={recommendedAction} className="text-sm" />
        {exceeded && (
          <span className="badge badge-risk-critical text-xs">THRESHOLD EXCEEDED</span>
        )}
      </div>

      {meta && meta.length > 0 && (
        <div className="score-display-meta">
          {meta.map((item, idx) => (
            <div key={idx} className="score-display-meta-item">
              <div className="score-display-meta-label">{item.label}</div>
              <div className="score-display-meta-value">{item.value}</div>
            </div>
          ))}
        </div>
      )}

      {onAction && (
        <div className="score-display-actions">
          {(['approve', 'verify', 'review', 'hold'] as const).map((action) => (
            <button
              key={action}
              type="button"
              onClick={() => onAction(action)}
              disabled={disabled || !!loadingAction}
              className={`btn btn-sm border ${actionStyles[action].base} ${actionStyles[action].hover} disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-surface focus-visible:ring-primary`}
            >
              {loadingAction === action ? 'PROCESSING...' : actionLabels[action]}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}