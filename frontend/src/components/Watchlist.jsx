import { useEffect, useState } from 'react'
import Logo from './Logo.jsx'
import { getWatchlist, removeWatch, setNote } from '../lib/watchlist.js'
import { research } from '../api.js'
import { currencySymbol } from '../lib/currency.js'
import { PlusIcon, ArrowIcon, CloseIcon } from './Icons.jsx'

function changeChip(pct) {
  if (pct == null) return <span className="chip flat">—</span>
  const cls = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  const dir = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  return <span className={'chip ' + cls}><ArrowIcon direction={dir} className="icon" /> {pct > 0 ? '+' : ''}{pct}%</span>
}
const sym = currencySymbol

export default function Watchlist({ onNavigate, onOpen, onHome }) {
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
  const editNote = (t, note) => setItems(setNote(t, note))

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <button className="logo logo-btn" onClick={onHome}><Logo /> Trade Craft</button>
          <div className="tabs">
            <button onClick={() => onNavigate('home')}>Research</button>
            <button onClick={() => onNavigate('compare')}>Comparison</button>
            <button className="on" aria-current="page">Watchlist</button>
            <button onClick={() => onNavigate('history')}>History</button>
            <button onClick={() => onNavigate('practice')}>Practice Lab</button>
            <button onClick={() => onNavigate('glossary')}>Glossary</button>
          </div>
        </div>
        <button className="backbtn" onClick={() => onNavigate('home')}><PlusIcon className="icon" /> New research</button>
      </div>

      <div className="headline">
        <h1 style={{ fontSize: 30 }}>Watchlist</h1>
        <span className="faint" style={{ fontSize: 13, alignSelf: 'center' }}>companies you're tracking · information, not trade prompts</span>
      </div>

      {items.length === 0 ? (
        <div className="card"><div className="placeholder">Nothing tracked yet. Open a company and tap "Watch" to add it here. This is a study list to revisit — no positions, no profit/loss, no signals.</div></div>
      ) : (
        <div className="watch-list">
          {items.map((it) => {
            const q = quotes[it.ticker]
            return (
              <div className="watch-entry" key={it.ticker}>
                <div className="watch-item">
                  <button className="watch-open" onClick={() => onOpen(it.ticker)}>
                    <span className="watch-tk mono">{it.ticker}</span>
                    <span className="watch-name">{q?.name || it.name || ''}</span>
                    <span className="watch-px mono">{q ? `${sym(q.currency)}${q.price}` : '…'}</span>
                    {q ? changeChip(q.changePercent) : <span className="chip flat">—</span>}
                  </button>
                  <button className="watch-x" title="Remove" onClick={() => drop(it.ticker)}><CloseIcon className="icon" /></button>
                </div>
                <input
                  className="watch-note"
                  placeholder="Why are you watching this? (optional study note)"
                  defaultValue={it.note || ''}
                  onBlur={(e) => editNote(it.ticker, e.target.value)}
                />
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
