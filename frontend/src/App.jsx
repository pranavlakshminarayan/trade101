import { useEffect, useState } from 'react'
import Welcome from './components/Welcome.jsx'
import Research from './components/Research.jsx'
import History from './components/History.jsx'
import Compare from './components/Compare.jsx'
import Watchlist from './components/Watchlist.jsx'
import PracticeLab from './components/PracticeLab.jsx'
import { research as fetchResearch, search as searchSymbols } from './api.js'
import { captureTokenFromUrl } from './lib/access.js'

captureTokenFromUrl()

// One route = one browser-history entry, so the address bar's own Back/Forward
// walks through every search *and* every tab switch, like a normal site —
// not just ticker searches. Tickers keep the existing #TICKER shareable-link
// shape; tab views get their own #/name so the two never collide.
function routeHash({ view, ticker }) {
  if (ticker) return '#' + encodeURIComponent(ticker)
  if (view && view !== 'home') return '#/' + view
  return '#'
}
function parseRoute() {
  const h = decodeURIComponent(window.location.hash.replace('#', '')).trim()
  if (h.startsWith('/')) return { view: h.slice(1) || 'home', ticker: null }
  if (h) return { view: 'home', ticker: h }
  return { view: 'home', ticker: null }
}

export default function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [recent, setRecent] = useState([])
  const [candidates, setCandidates] = useState(null) // disambiguation list
  const [view, setView] = useState('home') // 'home' | 'history' | 'compare' | 'watchlist' | 'practice'

  async function doResearch(symbol, push = true) {
    setLoading(true); setError(null); setCandidates(null)
    try {
      const bundle = await fetchResearch(symbol)
      setData(bundle)
      setView('home')
      setRecent((r) => [bundle.ticker, ...r.filter((x) => x !== bundle.ticker)].slice(0, 6))
      if (push) window.history.pushState({ view: 'home', ticker: bundle.ticker }, '', routeHash({ view: 'home', ticker: bundle.ticker }))
    } catch (e) {
      setError(e.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  // Switch tabs (Compare/Watchlist/History/Research) without losing whatever
  // was last researched — mirrors clicking a tab on any normal site.
  function goToView(v) {
    setView(v)
    window.history.pushState({ view: v, ticker: null }, '', routeHash({ view: v, ticker: null }))
  }

  // Browser back/forward + shareable #TICKER / #/compare /#/watchlist /#/history links.
  useEffect(() => {
    const applyRoute = (route) => {
      if (route.ticker) { doResearch(route.ticker, false); return }
      if (route.view && route.view !== 'home') { setView(route.view); return }
      setData(null); setError(null); setCandidates(null); setView('home')
    }
    applyRoute(parseRoute())
    const onPop = (e) => applyRoute(e.state || parseRoute())
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

  const goHome = () => {
    setData(null); setError(null); setCandidates(null); setView('home')
    window.history.pushState({ view: 'home', ticker: null }, '', '#')
  }

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

  if (view === 'history') {
    return <History onNavigate={goToView} onOpen={(t) => doResearch(t)} />
  }

  if (view === 'compare') {
    return <Compare onNavigate={goToView} onOpen={(t) => doResearch(t)} initial={data?.ticker} />
  }

  if (view === 'watchlist') {
    return <Watchlist onNavigate={goToView} onOpen={(t) => doResearch(t)} />
  }

  if (view === 'practice') {
    return <PracticeLab onNavigate={goToView} onOpen={(t) => doResearch(t)} />
  }

  if (loading) {
    return <div className="loading"><div className="spinner" />Working…</div>
  }

  if (data) {
    return (<>
      <Research data={data} onBack={goHome} onSearch={submitQuery} onNavigate={goToView} />
      {picker}
    </>)
  }

  return (<>
    <Welcome onSearch={submitQuery} recent={recent} onNavigate={goToView} />
    {picker}
    {error && (
      <div style={{ position: 'fixed', left: 0, right: 0, bottom: 20, display: 'flex', justifyContent: 'center' }}>
        <div className="err" style={{ maxWidth: 560 }}>⚠️ {error}</div>
      </div>
    )}
  </>)
}
