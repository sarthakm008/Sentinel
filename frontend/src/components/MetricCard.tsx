// MetricCard Component

interface MetricCardProps {
  label: string;
  value: string | number;
  valueClassName?: string;
  accent?: boolean;
}

export function MetricCard({ label, value, valueClassName = '', accent = false }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-card-label">{label}</div>
      <div className={`metric-card-value ${valueClassName} ${accent ? 'accent' : ''}`}>
        {value}
      </div>
    </div>
  );
}