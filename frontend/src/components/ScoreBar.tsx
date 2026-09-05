import { StatusBadge } from './StatusBadge';

interface ScoreBarProps {
  score: number;
  band: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  showValue?: boolean;
  className?: string;
}

const bandClassMap: Record<string, string> = {
  LOW: 'score-bar__fill--low',
  MEDIUM: 'score-bar__fill--medium',
  HIGH: 'score-bar__fill--high',
  CRITICAL: 'score-bar__fill--critical',
};

export function ScoreBar({ score, band, showValue = true, className = '' }: ScoreBarProps) {
  const percentage = Math.round(score * 100);
  const fillClass = bandClassMap[band] || 'score-bar__fill--low';

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="flex-1 min-w-0">
        <div className="score-bar" role="progressbar" aria-valuenow={percentage} aria-valuemin={0} aria-valuemax={100} aria-label={`Risk score: ${percentage}%`}>
          <div className={`score-bar__fill ${fillClass}`} style={{ width: `${percentage}%` }} />
        </div>
      </div>
      {showValue && (
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="font-mono font-semibold text-text-primary w-10 text-right">
            {percentage}%
          </span>
          <StatusBadge variant="risk" value={band} />
        </div>
      )}
    </div>
  );
}