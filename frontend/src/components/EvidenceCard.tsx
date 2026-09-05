// EvidenceCard component - displays structured evidence by category

import { EvidenceItem } from '../types';

interface EvidenceCardProps {
  category: 'behavioral' | 'graph' | 'temporal';
  items: EvidenceItem[];
}

const categoryConfig: Record<string, { label: string; color: string; bg: string; border: string }> = {
  behavioral: { label: 'BEHAVIORAL', color: 'var(--color-primary)', bg: 'var(--color-primary-light)', border: 'var(--color-primary)' },
  graph: { label: 'GRAPH', color: 'var(--color-risk-medium)', bg: 'var(--color-action-review-bg)', border: 'var(--color-action-review)' },
  temporal: { label: 'TEMPORAL', color: 'var(--color-risk-high)', bg: 'var(--color-action-hold-bg)', border: 'var(--color-action-hold)' },
};

export function EvidenceCard({ category, items }: EvidenceCardProps) {
  const config = categoryConfig[category] || categoryConfig.behavioral;

  if (items.length === 0) {
    return (
      <div className="panel">
        <div className="panel-header" style={{ color: config.color, borderColor: config.border }}>
          {config.label}
        </div>
        <div className="panel-body">
          <p className="text-sm text-text-muted">No significant evidence in this category</p>
        </div>
      </div>
    );
  }

  return (
    <div className="panel" style={{ borderColor: config.border }}>
      <div className="panel-header" style={{ color: config.color, borderColor: config.border }}>
        {config.label}
      </div>
      <div className="panel-body space-y-2">
        {items.map((item, idx) => (
          <div key={idx} className="panel-body p-3" style={{ backgroundColor: config.bg, borderColor: config.border }}>
            <p className="text-sm font-medium text-text-primary">{item.description}</p>
            <p className="text-xs text-text-muted mt-1 font-mono">
              Metric: {item.metric} = {typeof item.value === 'number' ? item.value.toFixed(3) : item.value}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}