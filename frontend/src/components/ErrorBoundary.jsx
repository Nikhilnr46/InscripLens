import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Unhandled UI Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          backgroundColor: '#121214',
          color: '#EDEDEC',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
          <div style={{
            maxWidth: '520px',
            backgroundColor: '#1B1B1F',
            border: '1px solid #3A2A2A',
            borderRadius: '12px',
            padding: '32px',
            textAlign: 'center'
          }}>
            <h2 style={{ fontSize: '1.25rem', color: '#E06C75', marginBottom: '12px' }}>
              Something went wrong loading the interface
            </h2>
            <p style={{ fontSize: '0.88rem', color: '#A8A29A', lineHeight: 1.5, marginBottom: '20px' }}>
              The workspace encountered an unexpected rendering error. You can reload the page or return to the landing overview.
            </p>
            {this.state.error?.message && (
              <pre style={{
                textAlign: 'left',
                backgroundColor: '#121214',
                color: '#E5C07B',
                padding: '12px',
                borderRadius: '6px',
                fontSize: '0.78rem',
                overflowX: 'auto',
                marginBottom: '20px'
              }}>
                {this.state.error.message}
              </pre>
            )}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
              <button
                onClick={() => { window.location.href = '/'; }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#C9A66B',
                  color: '#121214',
                  fontWeight: '600',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Go to Overview
              </button>
              <button
                onClick={() => window.location.reload()}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#2A2A30',
                  color: '#EDEDEC',
                  border: '1px solid #3A3A42',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Reload
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;

