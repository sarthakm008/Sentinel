import { StrictMode, Component, ReactNode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/globals.css'
import './styles/components.css'
import { ThemeProvider } from './contexts/ThemeContext'
import App from './App.tsx'

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  componentStack: string | null
}

class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null, componentStack: null }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: { componentStack: string }) {
    console.error('SENTINEL RUNTIME ERROR:', error)
    console.error('COMPONENT STACK:', errorInfo.componentStack)
    this.setState({ componentStack: errorInfo.componentStack })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '24px', fontFamily: 'monospace', color: '#dc2626', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px' }}>
          <h2 style={{ margin: '0 0 12px', fontSize: '18px' }}>SENTINEL RUNTIME ERROR</h2>
          <p style={{ margin: '0 0 8px', fontSize: '14px' }}><strong>Message:</strong> {this.state.error?.message}</p>
          <pre style={{ margin: '0 0 8px', fontSize: '12px', overflow: 'auto', maxHeight: '300px', background: '#fff', padding: '12px', border: '1px solid #e5e7eb', borderRadius: '4px' }}>
            {this.state.componentStack}
          </pre>
          <p style={{ margin: '0', fontSize: '12px', color: '#6b7280' }}>Inspect the component stack above to identify the failing component.</p>
        </div>
      )
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </ThemeProvider>
  </StrictMode>,
)