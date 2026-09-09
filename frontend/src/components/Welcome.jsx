import { useState } from 'react'
import Logo from './Logo.jsx'

const SUGGEST = ['NVDA', 'AAPL', 'MSFT', 'TSM', 'RELIANCE.NS', '005930.KS']

export default function Welcome({ onSearch, recent }) {
  const [value, setValue] = useState('')
  const submit = (t) => { const q = (t ?? value).trim(); if (q) onSearch(q) }

  return (
    <div className="welcome">
      <aside className="rail">
        <div className="logo"><Logo /> Trade101</div>
        <button className="railitem on" style={{ marginTop: 12 }}>✚ New research</button>
        <button className="railitem">⚖️ Comparison <span className="faint" style={{ marginLeft: 'auto', fontSize: 11 }}>soon</span></button>
        <button className="railitem">🕘 History <span className="faint" style={{ marginLeft: 'auto', fontSize: 11 }}>soon</span></button>
        {recent?.length > 0 && <div className="railsec">Recent research</div>}
        {recent?.map((r) => (
          <button key={r} className="railitem" onClick={() => submit(r)}>{r}</button>
        ))}
      </aside>

      <main className="welc-main">
        <div className="logo" style={{ fontSize: 22 }}><Logo size={34} /> Trade101</div>
        <div className="big">Which stock shall we study, <span>Pranav?</span></div>
        <div className="sub">
          Type any ticker — US, China, Japan, Korea, Hong Kong, Singapore or India.
          I'll pull the live data and teach the metrics as we go. (Non-US needs a suffix, e.g. <span className="mono">RELIANCE.NS</span>, <span className="mono">005930.KS</span>.)
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
