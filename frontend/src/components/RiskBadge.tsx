// RiskBadge component - displays risk score and band

import { RiskScoreResponse } from '../types';

interface RiskBadgeProps {
  score: number;
  band: RiskScoreResponse['risk_band'];
  action: RiskScoreResponse['recommended_action'];
  className?: string;
}

export function RiskBadge({ score, band, action, className = '' }: RiskBadgeProps) {
  const bandStyles: Record<string, string> = {
    LOW: 'bg-green-100 text-green-800 border-green-200',
    MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    HIGH: 'bg-orange-100 text-orange-800 border-orange-200',
    CRITICAL: 'bg-red-100 text-red-800 border-red-200',
  };

  const actionStyles: Record<string, string> = {
    approve: 'bg-green-100 text-green-800',
    verify: 'bg-blue-100 text-blue-800',
    review: 'bg-orange-100 text-orange-800',
    hold: 'bg-red-100 text-red-800',
  };

  const bandStyle = bandStyles[band] || 'bg-gray-100 text-gray-800';
  const actionStyle = actionStyles[action] || 'bg-gray-100 text-gray-800';

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-600">Risk Score</span>
          <div className="relative w-32 h-4 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                band === 'LOW' ? 'bg-green-500' :
                band === 'MEDIUM' ? 'bg-yellow-500' :
                band === 'HIGH' ? 'bg-orange-500' : 'bg-red-500'
              }`}
              style={{ width: `${score * 100}%` }}
            />
          </div>
          <span className="text-lg font-bold text-gray-900 w-10 text-right">
            {(score * 100).toFixed(1)}%
          </span>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${bandStyle}`}>
          {band}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-gray-600">Recommended Action:</span>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${actionStyle}`}>
          {action.toUpperCase()}
        </span>
      </div>
    </div>
  );
}