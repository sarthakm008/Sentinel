// EvidenceCard component - displays structured evidence by category

import { EvidenceItem } from '../types';

interface EvidenceCardProps {
  title: string;
  category: 'behavioral' | 'graph' | 'temporal';
  items: EvidenceItem[];
  icon?: React.ReactNode;
}

const categoryStyles: Record<string, { bg: string; border: string; icon: string }> = {
  behavioral: { bg: 'bg-blue-50', border: 'border-blue-200', icon: '👤' },
  graph: { bg: 'bg-purple-50', border: 'border-purple-200', icon: '🕸️' },
  temporal: { bg: 'bg-orange-50', border: 'border-orange-200', icon: '⏱️' },
};

export function EvidenceCard({ title, category, items, icon }: EvidenceCardProps) {
  const styles = categoryStyles[category] || categoryStyles.behavioral;

  if (items.length === 0) {
    return (
      <div className="bg-bg-tertiary border border-border rounded-lg p-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-text-secondary mb-3">
          <span>{styles.icon}</span> {title}
        </h3>
        <p className="text-sm text-text-muted">No significant evidence in this category</p>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-text-secondary mb-3">
        <span>{styles.icon}</span> {title}
      </h3>
      <div className="space-y-2">
        {items.map((item, idx) => (
          <div key={idx} className="bg-surface border border-border rounded p-3">
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