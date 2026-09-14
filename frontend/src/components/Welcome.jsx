import { useState } from 'react'
import Logo from './Logo.jsx'

const SUGGEST = ['NVDA', 'Apple', 'Samsung', 'Toyota', 'Tencent', 'Reliance']

export default function Welcome({ onSearch, recent, onNavigate }) {
  const [value, setValue] = useState('')
  const submit = (t) => { const q = (t ?? value).trim(); if (q) onSearch(q) }

  return (
    <div className="welcome">
      <aside className="rail">
        <div className="logo"><Logo /> Trade101</div>
        <button className="railitem on" style={{ marginTop: 12 }}>✚ New research</button>
        <button className="railitem" onClick={() => onNavigate('compare')}>⚖️ Comparison</button>
        <button className="railitem" onClick={() => onNavigate('history')}>🕘 History</button>
        {recent?.length > 0 && <div className="railsec">Recent research</div>}
        {recent?.map((r) => (
          <button key={r} className="railitem" onClick={() => submit(r)}>{r}</button>
        ))}
      </aside>

      <main className="welc-main">
        <div className="logo" style={{ fontSize: 22 }}><Logo size={34} /> Trade101</div>
        <div className="big">Which stock shall we study, <span>Pranav?</span></div>
        <div className="sub">
          Just type a <b>company name</b> (or ticker) — any market: US, China, Japan, Korea, Hong Kong, Singapore, India, Europe.
          If several match, you pick. I'll pull the live data and teach the metrics as we go.
        </div>

        <div className="askbox">
          <span className="faint">🔍</span>
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
