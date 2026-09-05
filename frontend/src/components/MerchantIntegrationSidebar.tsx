// Merchant Integration Sidebar Component

import { useIntegrationStatus } from '../contexts/IntegrationStatusContext';

interface MerchantIntegrationSidebarProps {
  onInjectClick: () => void;
}

export function MerchantIntegrationSidebar({ onInjectClick }: MerchantIntegrationSidebarProps) {
  const { status, control, isLoading } = useIntegrationStatus();

  if (isLoading) {
    return (
      <div className="sidebar-integration">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
          <div className="spinner" />
        </div>
      </div>
    );
  }

  const isConnected = status?.connected ?? false;
  const isMonitoring = status?.monitoring ?? false;
  const queuePending = status?.queue_pending ?? 0;
  const eventsProcessed = status?.events_processed ?? 0;
  const eventsFailed = status?.events_failed ?? 0;

  return (
    <div className="sidebar-integration">
      <div className="sidebar-integration-status">
        <span className="dot" style={{ backgroundColor: isConnected ? 'var(--color-status-connected)' : 'var(--color-status-disconnected)' }} />
        <span>INTEGRATION</span>
        <span style={{ marginLeft: 'auto', textTransform: 'uppercase', fontSize: '10px', color: isMonitoring ? 'var(--color-status-monitoring)' : 'var(--color-text-muted)' }}>
          {isMonitoring ? 'ACTIVE' : 'STOPPED'}
        </span>
      </div>

      <div className="sidebar-integration-metrics">
        <div className="sidebar-integration-metric">
          <span className="label">Queue</span>
          <span className="value">{queuePending}</span>
        </div>
        <div className="sidebar-integration-metric">
          <span className="label">Processed</span>
          <span className="value">{eventsProcessed}</span>
        </div>
        <div className="sidebar-integration-metric">
          <span className="label">Failed</span>
          <span className="value" style={{ color: 'var(--color-risk-high)' }}>{eventsFailed}</span>
        </div>
        <div className="sidebar-integration-metric">
          <span className="label">Status</span>
          <span className="value">{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {!isMonitoring ? (
          <button
            onClick={() => control('start')}
            className="btn btn-primary btn-sm"
            style={{ width: '100%', justifyContent: 'center' }}
          >
            Start Monitoring
          </button>
        ) : (
          <button
            onClick={() => control('stop')}
            className="btn btn-danger btn-sm"
            style={{ width: '100%', justifyContent: 'center' }}
          >
            Stop Monitoring
          </button>
        )}

        <button
          onClick={onInjectClick}
          className="btn btn-secondary btn-sm"
          style={{ width: '100%', justifyContent: 'center' }}
          data-testid="inject-refund-btn"
        >
          Inject Refund
        </button>
      </div>
    </div>
  );
}