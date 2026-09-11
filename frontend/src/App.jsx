import { useEffect, useState } from 'react'
import Welcome from './components/Welcome.jsx'
import Research from './components/Research.jsx'
import History from './components/History.jsx'
import Journal from './components/Journal.jsx'
import { research as fetchResearch, search as searchSymbols } from './api.js'

export default function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [recent, setRecent] = useState([])
  const [candidates, setCandidates] = useState(null) // disambiguation list
  const [view, setView] = useState('home') // 'home' | 'history'

  async function doResearch(symbol, push = true) {
    setLoading(true); setError(null); setCandidates(null)
    try {
      const bundle = await fetchResearch(symbol)
      setData(bundle)
      setRecent((r) => [bundle.ticker, ...r.filter((x) => x !== bundle.ticker)].slice(0, 6))
      if (push) window.history.pushState({ ticker: bundle.ticker }, '', '#' + bundle.ticker)
    } catch (e) {
      // Keep the failure kind, so the UI can offer a retry only when retrying
      // could actually help.
      setError({ message: e.message || 'Something went wrong', retryable: !!e.retryable, symbol })
    } finally {
      setLoading(false)
    }
  }

  // Browser back/forward + shareable #TICKER links.
  useEffect(() => {
    const hashTicker = () => decodeURIComponent(window.location.hash.replace('#', '')).trim()
    const initial = hashTicker()
    if (initial) doResearch(initial, false)
    const onPop = (e) => {
      const t = e.state?.ticker || hashTicker()
      if (t) doResearch(t, false)
      else { setData(null); setError(null); setCandidates(null) }
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Resolve a name/ticker → research, or show a picker when ambiguous.
  async function submitQuery(query) {
    const qn = query.trim()
    if (!qn) return
    setLoading(true); setError(null); setCandidates(null)
    const { candidates: cands = [] } = await searchSymbols(qn)
    if (cands.length === 0) {
      // maybe it's an exact ticker Yahoo search didn't surface — try it directly
      return doResearch(qn)
    }
    if (cands.length === 1 || cands[0].symbol.toUpperCase() === qn.toUpperCase()) {
      return doResearch(cands[0].symbol)
    }
    setCandidates(cands); setLoading(false)
  }

  const goHome = () => { setData(null); setError(null); setCandidates(null); window.history.pushState({}, '', '#') }

  const picker = candidates && (
    <div className="modal-bg" onClick={() => setCandidates(null)}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="lbl">Did you mean… — pick the one you want</div>
        {candidates.map((c) => (
          <button key={c.symbol} className="cand" onClick={() => doResearch(c.symbol)}>
            <span className="cand-sym mono">{c.symbol}</span>
            <span className="cand-name">{c.name}</span>
            <span className="cand-exch faint">{c.exchange}{c.type === 'ETF' ? ' · ETF' : ''}</span>
          </button>
        ))}
        <button className="cand-cancel" onClick={() => setCandidates(null)}>Cancel</button>
      </div>
    </div>
  )

  const openTicker = (t) => { setView('home'); doResearch(t) }

  if (view === 'history') {
    return <History onNavigate={setView} onOpen={openTicker} />
  }

  if (view === 'journal') {
    return <Journal onNavigate={setView} onOpen={openTicker} />
  }

  if (loading) {
    return <div className="loading"><div className="spinner" />Working…</div>
  }

  if (data) {
    return (<>
      <Research data={data} onBack={goHome} onSearch={submitQuery} onNavigate={setView} />
      {picker}
    </>)
  }

  return (<>
    <Welcome onSearch={submitQuery} recent={recent} onNavigate={setView} />
    {picker}
    {error && (
      <div style={{ position: 'fixed', left: 0, right: 0, bottom: 20, display: 'flex', justifyContent: 'center' }}>
        <div className="err" style={{ maxWidth: 620 }}>
          <div>⚠️ {error.message}</div>
          {error.retryable && (
            <button className="retry" onClick={() => doResearch(error.symbol, false)}>
              Try again
            </button>
          )}
        </div>
      </div>
    )}
  </>)
}
