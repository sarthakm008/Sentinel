interface MetricRowProps {
  label: string;
  value: string | number;
  valueClassName?: string;
  align?: 'left' | 'right';
}

export function MetricRow({ label, value, valueClassName = '', align = 'right' }: MetricRowProps) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-2">
      <span className="text-xs font-medium uppercase tracking-wider text-text-secondary">
        {label}
      </span>
      <div className={`text-text-primary font-mono font-medium text-sm ${valueClassName}`} style={{ textAlign: align }}>
        {value}
      </div>
    </div>
  );
}

interface MetricRowDescriptionProps {
  label: string;
  value: string | number;
  description: string;
  valueClassName?: string;
}

export function MetricRowWithDescription({ label, value, description, valueClassName = '' }: MetricRowDescriptionProps) {
  return (
    <div className="py-2">
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-xs font-medium uppercase tracking-wider text-text-secondary">
          {label}
        </span>
        <span className={`font-mono font-medium text-sm text-text-primary ${valueClassName}`}>
          {value}
        </span>
      </div>
      <p className="text-xs text-text-muted mt-1">{description}</p>
    </div>
  );
}