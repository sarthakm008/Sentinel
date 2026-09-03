// CaseCard component - case list item

import { CaseResponse } from '../types';

interface CaseCardProps {
  case: CaseResponse;
  onClick: () => void;
}

const bandColors: Record<string, string> = {
  LOW: 'bg-green-100 text-green-800',
  MEDIUM: 'bg-yellow-100 text-yellow-800',
  HIGH: 'bg-orange-100 text-orange-800',
  CRITICAL: 'bg-red-100 text-red-800',
};

const actionColors: Record<string, string> = {
  approve: 'bg-green-100 text-green-800',
  verify: 'bg-blue-100 text-blue-800',
  review: 'bg-orange-100 text-orange-800',
  hold: 'bg-red-100 text-red-800',
};

export function CaseCard({ case: caseData, onClick }: CaseCardProps) {
  const bandColor = bandColors[caseData.risk_band] || 'bg-gray-100 text-gray-800';
  const actionColor = actionColors[caseData.recommended_action] || 'bg-gray-100 text-gray-800';

  return (
    <div
      className="bg-white border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-mono text-sm text-gray-600">{caseData.refund_id}</span>
            <span className="text-sm text-gray-500">{caseData.customer_id}</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${bandColor}`}>
              {caseData.risk_band}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${actionColor}`}>
              {caseData.recommended_action.toUpperCase()}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
              caseData.status === 'decided' ? 'bg-gray-100 text-gray-800' : 'bg-blue-100 text-blue-800'
            }`}>
              {caseData.status.toUpperCase()}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
            <span>Score: <span className="font-mono font-medium">{caseData.risk_score.toFixed(3)}</span></span>
            <span>Created: <span className="font-mono">{new Date(caseData.created_at).toLocaleString()}</span></span>
            {caseData.decided_at && (
              <span>Decided: <span className="font-mono">{new Date(caseData.decided_at).toLocaleString()}</span></span>
            )}
            {caseData.decision && (
              <span className="font-medium">Decision: <span className="text-gray-900">{caseData.decision.toUpperCase()}</span></span>
            )}
          </div>
        </div>
        <div className="text-right text-sm text-gray-500">
          <span className="font-mono">#{caseData.id}</span>
        </div>
      </div>
    </div>
  );
}