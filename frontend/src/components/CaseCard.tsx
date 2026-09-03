// CaseCard component - case list item

import { CaseResponse } from '../types';

interface CaseCardProps {
  case: CaseResponse;
  onClick: () => void;
}

const bandStyles: Record<string, string> = {
  LOW: 'bg-success-light text-success-foreground border-success-light',
  MEDIUM: 'bg-warning-light text-warning-foreground border-warning-light',
  HIGH: 'bg-danger-light text-danger-foreground border-danger-light',
  CRITICAL: 'bg-critical-light text-critical-foreground border-critical-light',
};

const actionStyles: Record<string, string> = {
  approve: 'bg-success-light text-success-foreground',
  verify: 'bg-primary-light text-primary',
  review: 'bg-warning-light text-warning-foreground',
  hold: 'bg-danger-light text-danger-foreground',
};

const statusStyles: Record<string, string> = {
  pending: 'bg-primary-light text-primary',
  decided: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
};

export function CaseCard({ case: caseData, onClick }: CaseCardProps) {
  const bandStyle = bandStyles[caseData.risk_band] || 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700';
  const actionStyle = actionStyles[caseData.recommended_action] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
  const statusStyle = statusStyles[caseData.status] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';

  return (
    <div
      className="card p-4 hover:border-primary hover:shadow-md transition cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-mono text-sm text-text-secondary">{caseData.refund_id}</span>
            <span className="text-sm text-text-secondary">{caseData.customer_id}</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${bandStyle}`}>
              {caseData.risk_band}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${actionStyle}`}>
              {caseData.recommended_action.toUpperCase()}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${statusStyle}`}>
              {caseData.status.toUpperCase()}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-4 text-sm text-text-secondary">
            <span>Score: <span className="font-mono font-medium">{caseData.risk_score.toFixed(3)}</span></span>
            <span>Created: <span className="font-mono">{new Date(caseData.created_at).toLocaleString()}</span></span>
            {caseData.decided_at && (
              <span>Decided: <span className="font-mono">{new Date(caseData.decided_at).toLocaleString()}</span></span>
            )}
            {caseData.decision && (
              <span className="font-medium">Decision: <span className="text-text-primary">{caseData.decision.toUpperCase()}</span></span>
            )}
          </div>
        </div>
        <div className="text-right text-sm text-text-secondary">
          <span className="font-mono">#{caseData.id}</span>
        </div>
      </div>
    </div>
  );
}