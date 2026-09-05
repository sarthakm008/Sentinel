// RiskBadge component - displays risk score and band

import { RiskScoreResponse } from '../types';
import { ScoreBar } from './ScoreBar';
import { StatusBadge } from './StatusBadge';

interface RiskBadgeProps {
  score: number;
  band: RiskScoreResponse['risk_band'];
  action: RiskScoreResponse['recommended_action'];
  className?: string;
  compact?: boolean;
}

export function RiskBadge({ score, band, action, className = '', compact = false }: RiskBadgeProps) {
  if (compact) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <ScoreBar score={score} band={band} showValue={false} />
        <StatusBadge variant="action" value={action} />
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      <ScoreBar score={score} band={band} />
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium uppercase tracking-wider text-text-secondary">Recommended Action</span>
        <StatusBadge variant="action" value={action} />
      </div>
    </div>
  );
}