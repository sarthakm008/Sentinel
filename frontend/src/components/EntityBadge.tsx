// EntityBadge Component

interface EntityBadgeProps {
  id: string;
  type?: 'refund' | 'customer' | 'order' | 'device' | 'address' | 'payment';
  primary?: boolean;
}

const typeColors: Record<string, { bg: string; text: string }> = {
  refund: { bg: 'var(--color-primary-light)', text: 'var(--color-primary)' },
  customer: { bg: 'var(--color-risk-medium-bg)', text: 'var(--color-risk-medium)' },
  order: { bg: 'var(--color-bg-tertiary)', text: 'var(--color-text-primary)' },
  device: { bg: 'var(--color-action-review-bg)', text: 'var(--color-action-review)' },
  address: { bg: 'var(--color-action-approve-bg)', text: 'var(--color-action-approve)' },
  payment: { bg: 'var(--color-action-hold-bg)', text: 'var(--color-action-hold)' },
};

export function EntityBadge({ id, type, primary = false }: EntityBadgeProps) {
  const typeConfig = type ? typeColors[type] : null;

  return (
    <span className={`entity-badge ${primary ? 'primary' : ''}`}>
      {type && typeConfig && (
        <span className="entity-badge-type" style={{ backgroundColor: typeConfig.bg, color: typeConfig.text }}>
          {type.toUpperCase()}
        </span>
      )}
      {id}
    </span>
  );
}