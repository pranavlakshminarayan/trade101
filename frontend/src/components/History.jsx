import { useState } from 'react'
import Logo from './Logo.jsx'
import { getHistory, clearHistory, timeAgo } from '../lib/history.js'

function leanChip(lean) {
  if (!lean) return null
  const cls = lean === 'bullish' ? 'up' : lean === 'bearish' ? 'down' : 'flat'
  const a = lean === 'bullish' ? '▲' : lean === 'bearish' ? '▼' : '■'
  return <span className={'chip ' + cls}>{a} {lean}</span>
}

export default function History({ onNavigate, onOpen }) {
  const [items, setItems] = useState(getHistory())

  const wipe = () => { clearHistory(); setItems([]) }

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo"><Logo /> Trade101</div>
          <div className="tabs">
            <a onClick={() => onNavigate('home')}>Research</a>
            <a onClick={() => onNavigate('home')}>Comparison</a>
            <a className="on">History</a>
          </div>
        </div>
        <button className="backbtn" onClick={() => onNavigate('home')}>＋ New research</button>
      </div>

      <div className="headline" style={{ justifyContent: 'space-between' }}>
        <h1 style={{ fontSize: 30 }}>History</h1>
        {items.length > 0 && <button className="backbtn" onClick={wipe}>Clear all</button>}
      </div>

      {items.length === 0 ? (
        <div className="card"><div className="placeholder">No research yet. Search a company from the home screen — each one you study is saved here with a two-line takeaway.</div></div>
      ) : (
        <div className="hist-list">
          {items.map((it) => (
            <button className="hist-item" key={it.ticker} onClick={() => onOpen(it.ticker)}>
              <div className="hist-head">
                <span className="hist-tk mono">{it.ticker}</span>
                <span className="hist-name">{it.name}</span>
                {leanChip(it.lean)}
                <span className="faint" style={{ marginLeft: 'auto', fontSize: 12 }}>{timeAgo(it.when)}</span>
              </div>
              <div className="hist-sum">{it.summary || 'No AI summary was captured for this one.'}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
