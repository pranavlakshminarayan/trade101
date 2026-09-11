import { useEffect, useState } from 'react'
import { lenses as fetchLenses } from '../api.js'

// Style lenses — the same data read five ways.
//
// The design rule here: "ignores" and "failure modes" are NOT hidden behind a
// disclosure that nobody opens. A lens that shows only its own conclusion is
// precisely the thing this panel exists to inoculate against, so the blind spot
// sits next to the reading, at the same weight.

const LEAN_CLASS = { bullish: 'up', bearish: 'down', mixed: 'flat', neutral: 'flat', unknown: 'flat' }
const LEAN_ICON = { bullish: '▲', bearish: '▼', mixed: '◈', neutral: '■', unknown: '?' }

function Lens({ l, open, onToggle }) {
  return (
    <div className={'lens' + (open ? ' open' : '')}>
      <button className="lens-head" onClick={onToggle} aria-expanded={open}>
        <span className="lens-name">{l.name}</span>
        <span className={'chip ' + (LEAN_CLASS[l.lean] || 'flat')}>
          {LEAN_ICON[l.lean] || '■'} {l.lean}
        </span>
        <span className="lens-q faint">{l.question}</span>
        <span className="lens-caret">{open ? '▾' : '▸'}</span>
      </button>

      {open && (
        <div className="lens-body">
          <p className="lens-reading">{l.reading}</p>

          {l.caveat && <div className="verdict differ">{l.caveat}</div>}

          {l.evidence?.length > 0 && (
            <ul className="why">
              {l.evidence.map((e, i) => (
                <li key={i}>{e.point} <span className="src">[{e.source}]</span></li>
              ))}
            </ul>
          )}

          <div className="lens-grid">
            <div>
              <div className="lbl">Considers</div>
              <ul>{l.considers.map((x, i) => <li key={i}>{x}</li>)}</ul>
            </div>
            <div className="lens-ignores">
              <div className="lbl">Does not look at</div>
              <ul>{l.ignores.map((x, i) => <li key={i}>{x}</li>)}</ul>
            </div>
          </div>

          {l.conflicts?.length > 0 && (
            <div className="lens-conflict">
              <div className="lbl">Evidence against this reading, in this data</div>
              <ul>{l.conflicts.map((x, i) => <li key={i}>{x}</li>)}</ul>
            </div>
          )}

          <div className="lens-fail">
            <div className="lbl">How this lens goes wrong</div>
            <ul>{l.failureModes.map((x, i) => <li key={i}>{x}</li>)}</ul>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Lenses({ ticker }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState('trend')

  useEffect(() => {
    let alive = true
    setLoading(true); setData(null); setOpen('trend')
    fetchLenses(ticker).then((r) => { if (alive) { setData(r); setLoading(false) } })
    return () => { alive = false }
  }, [ticker])

  if (loading) {
    return (
      <div className="card">
        <div className="lbl">Style lenses — the same data, read five ways</div>
        <div className="scraping"><div className="spinner" />
          <div className="faint" style={{ fontSize: 13 }}>Computing each lens…</div></div>
      </div>
    )
  }

  if (!data?.lenses) {
    return (
      <div className="card">
        <div className="lbl">Style lenses</div>
        <div className="placeholder">
          Lenses unavailable for {ticker} right now. Everything else on this page is
          unaffected; retrying later may work.
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="lbl">Style lenses — the same data, read five ways</div>
      <p className="study-lead" style={{ margin: '4px 0 10px' }}>
        These are not styles to copy. They show that "what the chart says" depends on what
        you were asking — and every one of them is blind to something.
      </p>

      <div className={'disagree ' + data.disagreement.level}>
        <b>
          {data.disagreement.level === 'high' ? 'These lenses disagree' : 'These lenses agree'}
        </b>
        <p>{data.disagreement.note}</p>
      </div>

      <div className="lenslist">
        {data.lenses.map((l) => (
          <Lens key={l.id} l={l} open={open === l.id}
                onToggle={() => setOpen(open === l.id ? null : l.id)} />
        ))}
      </div>

      <div className="lens-excluded">
        <b>No day-trading lens.</b> {data.excluded['day-trading']}
      </div>
      <div className="note faint">{data.meta?.note}</div>
    </div>
  )
}
