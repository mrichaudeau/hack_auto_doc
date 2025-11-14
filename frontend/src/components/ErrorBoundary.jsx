/**
 * Error Boundary Component
 *
 * Catches React errors and displays them instead of white screen
 */
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
    this.state = { hasError: true, error, errorInfo };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '2rem',
          maxWidth: '800px',
          margin: '2rem auto',
          backgroundColor: '#fee',
          border: '2px solid #c00',
          borderRadius: '8px',
          fontFamily: 'monospace'
        }}>
          <h1 style={{ color: '#c00' }}>Application Error</h1>
          <h2>Something went wrong</h2>
          <details style={{ whiteSpace: 'pre-wrap', marginTop: '1rem' }}>
            <summary>Error Details</summary>
            <p><strong>Error:</strong> {this.state.error && this.state.error.toString()}</p>
            <p><strong>Stack:</strong></p>
            <pre style={{ overflow: 'auto', backgroundColor: '#f5f5f5', padding: '1rem' }}>
              {this.state.error && this.state.error.stack}
            </pre>
            {this.state.errorInfo && (
              <>
                <p><strong>Component Stack:</strong></p>
                <pre style={{ overflow: 'auto', backgroundColor: '#f5f5f5', padding: '1rem' }}>
                  {this.state.errorInfo.componentStack}
                </pre>
              </>
            )}
          </details>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
