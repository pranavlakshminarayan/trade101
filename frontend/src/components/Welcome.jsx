import { useState } from 'react'
import Logo from './Logo.jsx'
import { SearchIcon, ScaleIcon, StarIcon, ClockIcon, PlusIcon, FlaskIcon, BookIcon } from './Icons.jsx'
import { getUserName } from '../lib/apiKey.js'

const SUGGEST = ['NVDA', 'Apple', 'Samsung', 'Toyota', 'Tencent', 'Reliance']

export default function Welcome({ onSearch, recent, onNavigate }) {
  const [value, setValue] = useState('')
  const submit = (t) => { const q = (t ?? value).trim(); if (q) onSearch(q) }
  // Per-visitor personalization (2026-09-17) — each visitor's own name, set
  // once in the ApiKeyGate, never a hardcoded one (docs/AUDIT.md H7 fixed the
  // opposite problem: a single hardcoded "Pranav" that broke for every other
  // visitor). Falls back to the plain greeting when no name was given.
  const name = getUserName()

  return (
    <div className="welcome">
      <aside className="rail">
        <div className="logo"><Logo /> Trade Craft</div>
        <button className="railitem on" style={{ marginTop: 12 }}><PlusIcon className="icon" /> New research</button>
        <button className="railitem" onClick={() => onNavigate('compare')}><ScaleIcon className="icon" /> Comparison</button>
        <button className="railitem" onClick={() => onNavigate('watchlist')}><StarIcon className="icon" /> Watchlist</button>
        <button className="railitem" onClick={() => onNavigate('history')}><ClockIcon className="icon" /> History</button>
        <button className="railitem" onClick={() => onNavigate('practice')}><FlaskIcon className="icon" /> Practice Lab</button>
        <button className="railitem" onClick={() => onNavigate('glossary')}><BookIcon className="icon" /> Glossary</button>
        {recent?.length > 0 && <div className="railsec">Recent research</div>}
        {recent?.map((r) => (
          <button key={r} className="railitem" onClick={() => submit(r)}>{r}</button>
        ))}
      </aside>

      <main className="welc-main">
        <div className="logo" style={{ fontSize: 22 }}><Logo size={34} /> Trade Craft</div>
        <div className="big">Which stock shall we <span>study</span> today{name ? `, ${name}` : ''}?</div>
        <div className="sub">
          Just type a <b>company name</b> (or ticker) — any market: US, China, Japan, Korea, Hong Kong, Singapore, India, Europe.
          If several match, you pick. I'll pull the live data and teach the metrics as we go.
        </div>

        <div className="askbox">
          <SearchIcon className="icon faint" />
          <input
            autoFocus
            placeholder="Search a company or ticker…"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') submit() }}
          />
          <button className="go" onClick={() => submit()}>Research →</button>
        </div>

        <div className="chips">
          {SUGGEST.map((s) => (
            <button key={s} className="chipx" onClick={() => submit(s)}>{s}</button>
          ))}
        </div>
      </main>
    </div>
  )
}
