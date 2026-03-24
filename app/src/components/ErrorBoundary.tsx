import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 m-8 bg-red-50 border border-red-200 rounded-lg shadow-sm">
          <h1 className="text-2xl font-bold text-red-600 mb-4">React Application Crashed!</h1>
          <h2 className="text-lg font-semibold text-gray-800 mb-2">{this.state.error?.toString()}</h2>
          <pre className="p-4 bg-gray-900 text-red-400 rounded overflow-x-auto text-sm">
            {this.state.error?.stack}
          </pre>
          <div className="mt-4">
            <h3 className="font-semibold text-gray-700 mb-2">Component Stack Trace:</h3>
            <pre className="p-4 bg-gray-100 text-gray-800 rounded overflow-x-auto text-xs">
              {this.state.errorInfo?.componentStack}
            </pre>
          </div>
          <button 
            className="mt-6 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            onClick={() => window.location.reload()}
          >
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
