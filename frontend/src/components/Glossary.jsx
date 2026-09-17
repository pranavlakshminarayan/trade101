import { useMemo, useState } from 'react'
import Logo from './Logo.jsx'
import { GLOSSARY } from '../lib/glossary.js'
import { PlusIcon, SearchIcon } from './Icons.jsx'

export default function Glossary({ onNavigate, onHome }) {
  const [q, setQ] = useState('')

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase()
    if (!needle) return GLOSSARY
    return GLOSSARY
      .map((g) => ({ ...g, terms: g.terms.filter((t) => t.term.toLowerCase().includes(needle) || t.def.toLowerCase().includes(needle)) }))
      .filter((g) => g.terms.length > 0)
  }, [q])

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <button className="logo logo-btn" onClick={onHome}><Logo /> Trade Craft</button>
          <div className="tabs">
            <button onClick={() => onNavigate('home')}>Research</button>
            <button onClick={() => onNavigate('compare')}>Comparison</button>
            <button onClick={() => onNavigate('watchlist')}>Watchlist</button>
            <button onClick={() => onNavigate('history')}>History</button>
            <button onClick={() => onNavigate('practice')}>Practice Lab</button>
            <button className="on" aria-current="page">Glossary</button>
          </div>
        </div>
        <button className="backbtn" onClick={() => onNavigate('home')}><PlusIcon className="icon" /> New search</button>
      </div>

      <div className="headline">
        <h1 style={{ fontSize: 30 }}>Glossary</h1>
        <span className="faint" style={{ fontSize: 13, alignSelf: 'center' }}>terms used throughout the app — indicators, chart patterns, fundamentals</span>
      </div>

      <div className="strip">
        <div className="strip-search">
          <SearchIcon className="icon faint" />
          <input placeholder="Search a term…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="card"><div className="placeholder">No terms match "{q}".</div></div>
      ) : (
        filtered.map((g) => (
          <div className="card" key={g.group} style={{ marginBottom: 16 }}>
            <div className="lbl">{g.group}</div>
            <div className="gloss-list">
              {g.terms.map((t) => (
                <div className="gloss-item" key={t.term}>
                  <div className="gloss-term">{t.term}</div>
                  <div className="gloss-def">{t.def}</div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
