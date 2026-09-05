// DataRow Component

import { CaseResponse } from '../types';

interface DataRowProps {
  case: CaseResponse;
  onClick?: () => void;
}

const riskBorderColors: Record<string, string> = {
  LOW: 'var(--color-risk-low)',
  MEDIUM: 'var(--color-risk-medium)',
  HIGH: 'var(--color-risk-high)',
  CRITICAL: 'var(--color-risk-critical)',
};

const actionColors: Record<string, { bg: string; text: string }> = {
  approve: { bg: 'var(--color-action-approve-bg)', text: 'var(--color-action-approve)' },
  verify: { bg: 'var(--color-action-verify-bg)', text: 'var(--color-action-verify)' },
  review: { bg: 'var(--color-action-review-bg)', text: 'var(--color-action-review)' },
  hold: { bg: 'var(--color-action-hold-bg)', text: 'var(--color-action-hold)' },
};

const statusColors: Record<string, { bg: string; text: string }> = {
  pending: { bg: 'var(--color-primary-light)', text: 'var(--color-primary)' },
  decided: { bg: 'var(--color-bg-tertiary)', text: 'var(--color-text-muted)' },
};

export function DataRow({ case: caseData, onClick }: DataRowProps) {
  const riskColor = riskBorderColors[caseData.risk_band] || riskBorderColors.LOW;
  const actionStyle = actionColors[caseData.recommended_action] || actionColors.verify;
  const statusStyle = statusColors[caseData.status] || statusColors.pending;

  return (
    <div
      className="data-row"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick?.(); } }}
      style={{ borderLeftColor: riskColor }}
    >
      <div className="data-row-risk" style={{ backgroundColor: riskColor }} />
      <div className="data-row-refund">{caseData.refund_id}</div>
      <div className="data-row-customer">{caseData.customer_id}</div>
      <div className="data-row-score">{caseData.risk_score.toFixed(3)}</div>
      <div className="data-row-badges">
        <div
          className="data-row-band"
          style={{ backgroundColor: actionStyle.bg, color: actionStyle.text }}
        >
          {caseData.risk_band}
        </div>
        <div
          className="data-row-action"
          style={{ backgroundColor: actionStyle.bg, color: actionStyle.text }}
        >
          {caseData.recommended_action.toUpperCase()}
        </div>
      </div>
      <div className="data-row-meta">
        <div
          className="data-row-status"
          style={{ backgroundColor: statusStyle.bg, color: statusStyle.text }}
        >
          {caseData.status.toUpperCase()}
        </div>
        <div className="data-row-timestamp">
          {new Date(caseData.created_at).toLocaleString()}
        </div>
      </div>
    </div>
  );
}