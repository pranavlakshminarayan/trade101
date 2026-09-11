import { useState } from 'react'
import AsOf from './AsOf.jsx'
import Coverage from './Coverage.jsx'

// AI momentum read — synthesis, confidence, and every claim traceable to the
// evidence it was actually built from.
//
// Each claim carries resolved citations: an indicator shows its exact value, a
// news or filing citation opens the source. A claim that could not be traced is
// never shown as a finding — it is listed separately as a sourcing failure,
// because hiding it would make the panel look more reliable than it was.

function leanClass(lean) {
  if (lean === 'bullish') return 'up'
  if (lean === 'bearish') return 'down'
  return 'flat'
}

function Cite({ c }) {
  const title = c.detail ? `${c.label} — ${c.detail}` : c.label
  if (c.url) {
    return (
      <a className="cite" href={c.url} target="_blank" rel="noreferrer" title={title}>
        {c.kind === 'filing' ? 'filing' : 'source'} ↗
      </a>
    )
  }
  // Indicators have no URL — the citation IS the exact number it rests on.
  return <span className="cite cite-num" title={title}>{c.detail || c.label}</span>
}

function Claims({ items }) {
  if (!items?.length) return null
  return (
    <ul className="why">
      {items.slice(0, 6).map((e, i) => (
        <li key={i}>
          <b>{e.point}</b>{' '}
          {e.citations?.map((c, j) => <Cite key={j} c={c} />)}
        </li>
      ))}
    </ul>
  )
}

export default function AiRead({ ai, loading, meta }) {
  const [open, setOpen] = useState(false)

  if (loading) {
    return (
      <div className="card">
        <div className="lbl">AI momentum read</div>
        <div className="scraping">
          <div className="spinner" />
          <div>
            <div style={{ fontWeight: 500, color: 'var(--ink)' }}>Screening sources &amp; analysing…</div>
            <div className="faint" style={{ fontSize: 12 }}>
              Filtering news to this company, then reading the signals against it.
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!ai || !ai.available) {
    return (
      <div className="card">
        <div className="lbl">AI momentum read</div>
        <div className="placeholder">
          {ai?.reason || 'AI narration unavailable.'}
          <div style={{ marginTop: 8 }}>
            The chart, metrics and patterns above are unaffected — they are computed
            locally from the price data and remain exact.
          </div>
        </div>
      </div>
    )
  }

  const m = ai.momentum || {}
  const unsupported = ai.meta?.unsupportedClaims || []

  return (
    <div className="card">
      <div className="lbl">AI momentum read</div>

      {/* The not-advice boundary sits WITH the narrative, not in a footer. */}
      <div className="notadvice">
        <b>This describes what the data shows — it is not advice.</b> Trade101 never
        says buy, sell or hold, and never predicts a price. Read the evidence, then
        form your own view.
      </div>

      <AsOf meta={{ ...(meta || {}), asOf: ai.asOf || meta?.asOf }} timeframe={ai.timeframe} />
      <Coverage coverage={ai.coverage} filter={ai.evidenceFilter} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '10px 0 8px' }}>
        <span className={'chip ' + leanClass(m.lean)} style={{ fontSize: 15 }}>{m.lean || '—'}</span>
        <span className="conf">confidence: {m.confidence || '—'}</span>
      </div>

      <p style={{ margin: '0 0 4px', fontSize: 14 }}>{m.summary}</p>
      <Claims items={m.evidence} />

      {unsupported.length > 0 && (
        <details className="unsupported">
          <summary>{unsupported.length} claim{unsupported.length === 1 ? '' : 's'} withheld — source could not be verified</summary>
          <p className="faint">
            These were generated but cite something outside the evidence supplied, so they
            are not shown as findings:
          </p>
          <ul>
            {unsupported.map((u, i) => <li key={i}>{u.point} <span className="faint">— {u.reason}</span></li>)}
          </ul>
        </details>
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
