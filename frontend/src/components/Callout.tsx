// Callout Component (left-border accent block)

import { ReactNode } from 'react';

interface CalloutProps {
  variant?: 'production' | 'rejected' | 'methodology' | 'default';
  title?: string;
  badge?: ReactNode;
  metrics?: Array<{ label: string; value: string | number; valueClassName?: string }>;
  children?: ReactNode;
  className?: string;
}

export function Callout({
  variant = 'default',
  title,
  badge,
  metrics,
  children,
  className = '',
}: CalloutProps) {
  const variantClass = variant !== 'default' ? `callout-${variant}` : '';

  return (
    <div className={`callout ${variantClass} ${className}`}>
      {(title || badge) && (
        <div className="callout-header">
          {title && <div className="callout-title">{title}</div>}
          {badge && <div>{badge}</div>}
        </div>
      )}
      {metrics && metrics.length > 0 && (
        <div className="callout-metrics">
          {metrics.map((metric, idx) => (
            <div key={idx} className="callout-metric">
              <div className="callout-metric-label">{metric.label}</div>
              <div className={`callout-metric-value ${metric.valueClassName || ''}`}>
                {metric.value}
              </div>
            </div>
          ))}
        </div>
      )}
      {children && <div className="callout-body">{children}</div>}
    </div>
  );
}