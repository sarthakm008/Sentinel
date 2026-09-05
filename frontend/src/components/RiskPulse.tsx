interface RiskPulseProps {
  stats: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
    total: number;
  };
}

export function RiskPulse({ stats }: RiskPulseProps) {
  const bands = [
    { key: 'CRITICAL', label: 'CRITICAL', count: stats.CRITICAL, color: 'risk-critical' },
    { key: 'HIGH', label: 'HIGH', count: stats.HIGH, color: 'risk-high' },
    { key: 'MEDIUM', label: 'MEDIUM', count: stats.MEDIUM, color: 'risk-medium' },
    { key: 'LOW', label: 'LOW', count: stats.LOW, color: 'risk-low' },
  ];

  const total = stats.total || 1;

  return (
    <div className="space-y-2">
      {bands.map((band) => {
        const width = total > 0 ? (band.count / total) * 100 : 0;
        return (
          <div key={band.key} className="flex items-center gap-3">
            <span className="text-xs font-medium text-text-secondary w-16">{band.label}</span>
            <div className="flex-1 h-3 bg-bg-tertiary rounded-full overflow-hidden border border-border">
              <div
                className={`h-full rounded-full transition-all duration-300 bg-${band.color}`}
                style={{ width: `${width}%` }}
              />
            </div>
            <span className="font-mono font-semibold text-text-primary w-12 text-right text-sm">
              {band.count}
            </span>
          </div>
        );
      })}
      <div className="flex items-center justify-between pt-2 border-t border-border">
        <span className="text-xs font-medium text-text-secondary">Total</span>
        <span className="font-mono font-semibold text-text-primary text-sm">{stats.total}</span>
      </div>
    </div>
  );
}