import { Component } from 'react'

// Top-level render-error catch. Without this, a single throw anywhere in the
// component tree (a malformed API response, an unexpected null, etc.) white-
// screens the ENTIRE app with no way back except a manual reload — for a
// research tool a beginner is relying on mid-session, that's a bad failure
// mode. This gives them a plain explanation and a way to recover without
// losing everything (going home clears state; reloading is still available).
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null, resetKey: 0 }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('Trade Craft crashed:', error, info?.componentStack)
  }

  // Bump resetKey to force React to fully unmount + remount the app tree below,
  // not just clear this boundary's own flag — the crash may have come from
  // App's own internal state (e.g. a bad research payload it's still holding),
  // which a plain re-render would hit again immediately.
  reset = () => {
    try { window.history.pushState({}, '', '#') } catch { /* ignore */ }
    this.setState((s) => ({ error: null, resetKey: s.resetKey + 1 }))
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ maxWidth: 560, margin: '80px auto', padding: '0 24px', textAlign: 'center' }}>
          <div className="card">
            <div className="lbl">Something went wrong</div>
            <p className="placeholder" style={{ marginBottom: 16 }}>
              This screen hit an unexpected error and couldn't render. Your data wasn't lost —
              going home should recover it; if the same thing happens again, a full reload will.
            </p>
            <button className="backbtn" onClick={this.reset}>← Go home</button>
          </div>
        </div>
      )
    }
    return <div key={this.state.resetKey}>{this.props.children}</div>
  }
}
