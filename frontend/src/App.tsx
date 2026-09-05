// Main App component with routing and new shell

import { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, Outlet, useLocation } from 'react-router-dom';
import { Overview } from './pages/Overview';
import { Cases } from './pages/Cases';
import { CaseDetail } from './pages/CaseDetail';
import { Evaluation } from './pages/Evaluation';
import { ThemeToggle } from './components/ThemeToggle';
import { IntegrationStatusProvider, useIntegrationStatus } from './contexts/IntegrationStatusContext';
import { MerchantIntegrationSidebar } from './components/MerchantIntegrationSidebar';
import { InjectRefundModal } from './components/InjectRefundModal';

const navigation = [
  { path: '/', label: 'Operations', icon: OperationsIcon },
  { path: '/cases', label: 'Cases', icon: CasesIcon },
  { path: '/evaluation', label: 'Evaluation', icon: EvaluationIcon },
] as const;

function OperationsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="2" y="3" width="20" height="14" rx="2" />
      <path d="M8 21h8" />
      <path d="M12 17v4" />
    </svg>
  );
}

function CasesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

function EvaluationIcon({ className }: { className?: string }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}

function Layout() {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const { status } = useIntegrationStatus();
  const isMonitoring = status?.monitoring ?? false;

  return (
    <div className="app-shell">
      <header className="app-header" role="banner">
        <div className="header-inner">
          <div className="header-brand">
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label={sidebarOpen ? 'Close navigation' : 'Open navigation'}
              aria-expanded={sidebarOpen}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <Link to="/" className="header-title" aria-label="Sentinel Home">
              Sentinel
            </Link>
          </div>

          <nav className="header-nav" aria-label="Main navigation">
            {navigation.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-nav-item ${location.pathname === item.path ? 'active' : ''}`}
                style={{ padding: '6px 12px', gap: '8px' }}
                aria-current={location.pathname === item.path ? 'page' : undefined}
              >
                <item.icon />
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>

          <div className="header-actions">
            <SystemStatus isMonitoring={isMonitoring} />
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="app-body">
        <aside
          className={`app-sidebar ${sidebarOpen ? 'open' : ''}`}
          aria-label="Sidebar navigation"
        >
          <nav className="sidebar-nav" aria-label="Navigation">
            <div className="sidebar-section">
              <div className="sidebar-section-title">Navigation</div>
              {navigation.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`sidebar-nav-item ${location.pathname === item.path ? 'active' : ''}`}
                  onClick={() => setSidebarOpen(false)}
                  aria-current={location.pathname === item.path ? 'page' : undefined}
                >
                  <item.icon />
                  <span>{item.label}</span>
                </Link>
              ))}
            </div>

            <div className="sidebar-divider" />

            <MerchantIntegrationSidebar onInjectClick={() => setModalOpen(true)} />
          </nav>
        </aside>

        <main className="app-main" role="main">
          <Outlet />
        </main>
      </div>

      <footer className="app-footer">
        <div style={{ maxWidth: 'none', padding: '8px 24px', textAlign: 'center' }}>
          <p style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>
            Sentinel — Razorpay AI Buildathon 2026 • Track 02: AI Risk Manager
            <span style={{ margin: '0 8px' }}>•</span>
            All data synthetic. Results do not represent production performance.
          </p>
        </div>
      </footer>

      {sidebarOpen && (
        <div
          className="modal-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <InjectRefundModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function SystemStatus({ isMonitoring }: { isMonitoring: boolean }) {
  return (
    <span className="sidebar-integration-status" style={{ padding: '4px 8px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-bg-tertiary)' }}>
      <span className="dot" style={{ backgroundColor: isMonitoring ? 'var(--color-status-monitoring)' : 'var(--color-text-muted)' }} />
      <span>{isMonitoring ? 'MONITORING ACTIVE' : 'MONITORING STOPPED'}</span>
    </span>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <IntegrationStatusProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Overview />} />
            <Route path="/cases" element={<Cases />} />
            <Route path="/cases/:id" element={<CaseDetail />} />
            <Route path="/evaluation" element={<Evaluation />} />
          </Route>
        </Routes>
      </IntegrationStatusProvider>
    </BrowserRouter>
  );
}