import { useState } from 'react'

// AI momentum read — synthesis + confidence + sourced evidence + a collapsible
// "learn the read" note (kept collapsed so the block doesn't tower over the page).

function leanClass(lean) {
  if (lean === 'bullish') return 'up'
  if (lean === 'bearish') return 'down'
  return 'flat'
}

export default function AiRead({ ai, loading }) {
  const [open, setOpen] = useState(false)

  if (loading) {
    return (
      <div className="card">
        <div className="lbl">AI momentum read</div>
        <div className="scraping">
          <div className="spinner" />
          <div>
            <div style={{ fontWeight: 500, color: 'var(--ink)' }}>Scraping &amp; analysing…</div>
            <div className="faint" style={{ fontSize: 12 }}>Gathering news + filings and reading the signals. This takes a few seconds.</div>
          </div>
        </div>
      </div>
    )
  }

  if (!ai || !ai.available) {
    return (
      <div className="card">
        <div className="lbl">AI momentum read</div>
        <div className="placeholder">{ai?.reason || 'AI narration unavailable.'}</div>
      </div>
    )
  }

  const m = ai.momentum || {}
  return (
    <div className="card">
      <div className="lbl">AI momentum read <span className="faint" style={{ textTransform: 'none', letterSpacing: 0 }}>· describes, never advises</span></div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '2px 0 8px' }}>
        <span className={'chip ' + leanClass(m.lean)} style={{ fontSize: 15 }}>{m.lean || '—'}</span>
        <span className="conf">confidence: {m.confidence || '—'}</span>
      </div>
      <p style={{ margin: '0 0 4px', fontSize: 14 }}>{m.summary}</p>
      {m.evidence?.length > 0 && (
        <ul className="why">
          {m.evidence.slice(0, 6).map((e, i) => (
            <li key={i}><b>{e.point}</b> <span className="src">[{e.source}]</span></li>
          ))}
        </ul>
      )}
      {ai.learning_note && (
        <div className="lesson" style={{ marginTop: 10 }}>
          <button className="collapse" onClick={() => setOpen(!open)}>
            {open ? '▾' : '▸'} Learn the read
          </button>
          {open && <p style={{ margin: '8px 0 0' }}>{ai.learning_note}</p>}
        </div>
      )}
    </div>
  )
}
