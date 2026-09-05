interface StatusBadgeProps {
  variant: 'risk' | 'action' | 'status';
  value: string;
  className?: string;
}

const riskVariantMap: Record<string, string> = {
  LOW: 'badge-risk-low',
  MEDIUM: 'badge-risk-medium',
  HIGH: 'badge-risk-high',
  CRITICAL: 'badge-risk-critical',
};

const actionVariantMap: Record<string, string> = {
  approve: 'badge-action-approve',
  verify: 'badge-action-verify',
  review: 'badge-action-review',
  hold: 'badge-action-hold',
};

const statusVariantMap: Record<string, string> = {
  pending: 'badge-status-pending',
  decided: 'badge-status-decided',
  processing: 'badge-status-pending',
  completed: 'badge-action-approve',
  failed: 'badge-action-hold',
};

export function StatusBadge({ variant, value, className = '' }: StatusBadgeProps) {
  let badgeClass = '';
  const displayValue = value.toUpperCase();

  switch (variant) {
    case 'risk':
      badgeClass = riskVariantMap[value] || 'badge-risk-low';
      break;
    case 'action':
      badgeClass = actionVariantMap[value.toLowerCase()] || 'badge-action-verify';
      break;
    case 'status':
      badgeClass = statusVariantMap[value.toLowerCase()] || 'badge-status-pending';
      break;
  }

  return (
    <span className={`badge badge-dot ${badgeClass} ${className}`}>
      {displayValue}
    </span>
  );
}