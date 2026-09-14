import { useEffect, useState } from 'react'
import Logo from './Logo.jsx'
import { getWatchlist, removeWatch } from '../lib/watchlist.js'
import { research } from '../api.js'

function changeChip(pct) {
  if (pct == null) return <span className="chip flat">—</span>
  const cls = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  const a = pct > 0 ? '▲' : pct < 0 ? '▼' : '■'
  return <span className={'chip ' + cls}>{a} {pct > 0 ? '+' : ''}{pct}%</span>
}
const sym = (c) => (c === 'INR' ? '₹' : c === 'USD' ? '$' : '')

export default function Watchlist({ onNavigate, onOpen }) {
  const [items, setItems] = useState(getWatchlist())
  const [quotes, setQuotes] = useState({}) // ticker -> quote

  // Pull a fresh quote for each tracked name (deterministic; no Claude spend).
  useEffect(() => {
    let alive = true
    items.forEach((it) => {
      research(it.ticker).then((r) => {
        if (alive) setQuotes((q) => ({ ...q, [it.ticker]: r.quote }))
      }).catch(() => {})
    })
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const drop = (t) => setItems(removeWatch(t))

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo"><Logo /> Trade Craft</div>
          <div className="tabs">
            <a onClick={() => onNavigate('home')}>Research</a>
            <a onClick={() => onNavigate('compare')}>Comparison</a>
            <a className="on">Watchlist</a>
            <a onClick={() => onNavigate('history')}>History</a>
          </div>
        </div>
        <button className="backbtn" onClick={() => onNavigate('home')}>＋ New research</button>
      </div>

      <div className="headline">
        <h1 style={{ fontSize: 30 }}>Watchlist</h1>
        <span className="faint" style={{ fontSize: 13, alignSelf: 'center' }}>companies you're tracking · information, not trade prompts</span>
      </div>

      {items.length === 0 ? (
        <div className="card"><div className="placeholder">Nothing tracked yet. Open a company and tap ☆ Watch to add it here. This is a study list to revisit — no positions, no profit/loss, no signals.</div></div>
      ) : (
        <div className="watch-list">
          {items.map((it) => {
            const q = quotes[it.ticker]
            return (
              <div className="watch-item" key={it.ticker}>
                <button className="watch-open" onClick={() => onOpen(it.ticker)}>
                  <span className="watch-tk mono">{it.ticker}</span>
                  <span className="watch-name">{q?.name || it.name || ''}</span>
                  <span className="watch-px mono">{q ? `${sym(q.currency)}${q.price}` : '…'}</span>
                  {q ? changeChip(q.changePercent) : <span className="chip flat">—</span>}
                </button>
                <button className="watch-x" title="Remove" onClick={() => drop(it.ticker)}>✕</button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
