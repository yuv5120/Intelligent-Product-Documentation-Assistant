import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Catches any uncaught render errors in the subtree.
 * Without this, one bad component crash kills the entire app.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In production this would go to Sentry / Datadog
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 16,
            padding: 40,
            color: 'var(--text-secondary)',
            textAlign: 'center',
          }}
        >
          <AlertTriangle size={32} color="var(--error)" />
          <div>
            <p style={{ fontWeight: 600, marginBottom: 6, color: 'var(--text-primary)' }}>
              Something went wrong
            </p>
            <p style={{ fontSize: 13, maxWidth: 360 }}>
              {this.state.error?.message ?? 'An unexpected error occurred in this component.'}
            </p>
          </div>
          <button
            className="btn btn-ghost"
            onClick={this.handleReset}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <RefreshCw size={13} />
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
