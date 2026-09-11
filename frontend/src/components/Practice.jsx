import { useEffect, useState } from 'react'
import Logo from './Logo.jsx'
import { practiceClose, practiceDelete, practiceList, practiceOpen, search as searchSymbols } from '../api.js'

// Practice lab — hypothetical positions, kept deliberately apart from research.
//
// This is the one screen in Trade101 that comes closest to looking like a
// trading app, so it is the one that needs the strongest framing. Every number
// is labelled hypothetical, the disclaimer sits at the top rather than in a
// footnote, and closing a position asks what you learned before it shows you
// the result. The lab is reachable only from its own tab — never the primary
// action on a research page.

function Hypo({ h }) {
  if (!h) return <span className="faint">—</span>
  const cls = h.hypotheticalChangePercent > 0 ? 'up' : h.hypotheticalChangePercent < 0 ? 'down' : 'flat'
  return (
    <span className={'chip ' + cls} title="Hypothetical — no order was placed">
      {h.hypotheticalChangePercent > 0 ? '+' : ''}{h.hypotheticalChangePercent}% hypothetical
    </span>
  )
}

function CloseForm({ entry, onDone }) {
  const [price, setPrice] = useState(entry.mark ?? '')
  const [reflection, setReflection] = useState('')
  const [busy, setBusy] = useState(false)

  return (
    <div className="pl-close">
      <label>
        <span className="faint">Closing price</span>
        <input value={price} inputMode="decimal" onChange={(e) => setPrice(e.target.value)} />
      </label>
      <textarea className="hypo" rows={2} value={reflection}
                onChange={(e) => setReflection(e.target.value)}
                placeholder="Before you see the result: what did this teach you? Was the reasoning you opened on the reasoning that mattered?" />
      <div className="study-foot">
        <button className="cand-cancel" onClick={() => onDone()}>Cancel</button>
        <button className="go" disabled={busy || price === ''}
                onClick={async () => {
                  setBusy(true)
                  await practiceClose(entry.id, Number(price), reflection.trim() || null)
                  setBusy(false); onDone(true)
                }}>Close position</button>
      </div>
    </div>
  )
}

function OpenForm({ onOpened }) {
  const [q, setQ] = useState('')
  const [price, setPrice] = useState('')
  const [quantity, setQuantity] = useState('1')
  const [direction, setDirection] = useState('long')
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const ready = q.trim() && price !== '' && reason.trim().length >= 15

  async function submit() {
    setBusy(true); setError(null)
    try {
      const { candidates = [] } = await searchSymbols(q.trim())
      await practiceOpen({
        ticker: candidates[0]?.symbol || q.trim().toUpperCase(),
        price: Number(price), quantity: Number(quantity) || 1,
        direction, reason: reason.trim(),
      })
      setQ(''); setPrice(''); setQuantity('1'); setReason('')
      onOpened()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card">
      <div className="lbl">Record a hypothetical position</div>
      <div className="wl-fields">
        <label><span className="faint">Company or ticker</span>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. Nvidia" /></label>
        <label><span className="faint">Entry price</span>
          <input value={price} inputMode="decimal" onChange={(e) => setPrice(e.target.value)} /></label>
        <label><span className="faint">Quantity</span>
          <input value={quantity} inputMode="decimal" onChange={(e) => setQuantity(e.target.value)} /></label>
        <label><span className="faint">Direction</span>
          <select value={direction} onChange={(e) => setDirection(e.target.value)}>
            <option value="long">long</option>
            <option value="short">short</option>
          </select>
        </label>
      </div>
      <textarea className="hypo" rows={2} value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Why? Which evidence are you testing here? (required — a position with no reasoning teaches nothing when you close it)" />
      <div className="study-foot">
        <span className="faint" style={{ fontSize: 11.5 }}>
          {reason.trim().length < 15 ? 'Write your reasoning to continue.' : ''}
        </span>
        <button className="go" disabled={!ready || busy} onClick={submit}>
          {busy ? 'Saving…' : 'Record'}
        </button>
      </div>
      {error && <div className="err" style={{ marginTop: 10 }}>⚠️ {error}</div>}
    </div>
  )
}

export default function Practice({ onNavigate, onOpen }) {
  const [data, setData] = useState(null)
  const [closing, setClosing] = useState(null)

  const load = () => practiceList().then(setData)
  useEffect(() => { load() }, [])

  const entries = data?.entries || []
  const open = entries.filter((e) => !e.closed_at)
  const closed = entries.filter((e) => e.closed_at)

  const render = (e) => (
    <div className={'pl-entry' + (e.closed_at ? ' closed' : '')} key={e.id}>
      <div className="pl-head">
        <button className="jticker" onClick={() => onOpen(e.ticker)}>{e.ticker}</button>
        <span className="faint">{e.direction} · {e.quantity} @ {e.open_price}</span>
        <Hypo h={e.hypothetical} />
        {e.closed_at
          ? <span className="faint">closed {new Date(e.closed_at).toLocaleDateString()}</span>
          : <span className="faint">marked at {e.mark ?? '—'}</span>}
        <button className="jdel" aria-label="Delete entry"
                onClick={async () => { await practiceDelete(e.id); load() }}>✕</button>
      </div>
      <p className="jhypo">{e.reason}</p>
      {e.note && <div className="err" style={{ fontSize: 12 }}>⚠️ {e.note}</div>}
      {e.reflection && <p className="jrefl-text">↩ {e.reflection}</p>}
      {!e.closed_at && closing !== e.id && (
        <button className="collapse" onClick={() => setClosing(e.id)}>Close this position</button>
      )}
      {closing === e.id && (
        <CloseForm entry={e} onDone={(saved) => { setClosing(null); if (saved) load() }} />
      )}
    </div>
  )

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo"><Logo /> Trade101</div>
          <div className="tabs">
            <a onClick={() => onNavigate('home')} style={{ cursor: 'pointer' }}>Research</a>
            <a onClick={() => onNavigate('compare')} style={{ cursor: 'pointer' }}>Comparison</a>
            <a onClick={() => onNavigate('watchlist')} style={{ cursor: 'pointer' }}>Watchlist</a>
            <a onClick={() => onNavigate('journal')} style={{ cursor: 'pointer' }}>Journal</a>
            <a className="on">Practice</a>
          </div>
        </div>
        <button className="backbtn" onClick={() => onNavigate('home')}>← New search</button>
      </div>

      <div className="headline"><h1>Practice lab</h1></div>

      {/* The disclaimer leads. It is not a footnote on this screen. */}
      <div className="notadvice" style={{ maxWidth: 820 }}>
        <b>Nothing here is real.</b> {data?.disclaimer}
      </div>
      <p className="study-lead" style={{ maxWidth: 820 }}>{data?.purpose}</p>

      <OpenForm onOpened={load} />

      {entries.length === 0 && (
        <div className="placeholder">
          No hypothetical positions recorded. This lab is optional — the learning journal
          is where the more useful work happens.
        </div>
      )}

      {open.length > 0 && (
        <div className="card">
          <div className="lbl">Open — hypothetical, marked to delayed prices</div>
          <div className="jlist">{open.map(render)}</div>
        </div>
      )}

      {closed.length > 0 && (
        <div className="card">
          <div className="lbl">Closed — read the reflections, not the numbers</div>
          <div className="jlist">{closed.map(render)}</div>
        </div>
      )}
    </div>
  )
}
