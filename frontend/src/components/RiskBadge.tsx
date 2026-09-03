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

  const bandStyle = bandStyles[band] || 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700';
  const actionStyle = actionStyles[action] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-text-secondary">Risk Score</span>
          <div className="relative w-32 h-4 bg-bg-tertiary rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                band === 'LOW' ? 'bg-success' :
                band === 'MEDIUM' ? 'bg-warning' :
                band === 'HIGH' ? 'bg-danger' : 'bg-danger'
              }`}
              style={{ width: `${score * 100}%` }}
            />
          </div>
          <span className="text-lg font-bold text-text-primary w-10 text-right">
            {(score * 100).toFixed(1)}%
          </span>
        </div>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${bandStyle}`}>
          {band}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-text-secondary">Recommended Action:</span>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${actionStyle}`}>
          {action.toUpperCase()}
        </span>
      </div>
    </div>
  );
}