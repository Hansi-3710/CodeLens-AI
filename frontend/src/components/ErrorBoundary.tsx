/**
 * Top-level error boundary — without one, an unhandled render error in any
 * page unmounts the entire React tree to a blank white screen with only a
 * console error, which is exactly the "amateurish" failure mode a portfolio
 * demo can't afford to hit live. Catches it, shows a recoverable message
 * instead.
 *
 * Belongs to: frontend/src/components/
 * Phase: hardening pass (post-audit) — audit flagged missing error handling.
 */
import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In production this is where an error-tracking call (Sentry, etc.)
    // would go — logged here so it's not silently swallowed.
    console.error("Unhandled UI error:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-md mx-auto mt-24 text-center">
          <p className="font-mono text-sm text-channel-1 mb-2">Something went wrong.</p>
          <p className="text-sm text-mist mb-6">{this.state.message ?? "An unexpected error occurred."}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-signal text-white text-sm font-medium rounded px-4 py-2 hover:opacity-90 transition-opacity"
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
