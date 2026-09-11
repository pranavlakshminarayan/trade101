import { useEffect, useState } from 'react'
import Logo from './Logo.jsx'
import { search as searchSymbols, watchAdd, watchlist as fetchWatchlist, watchRemove } from '../api.js'

// Watchlist — what you are following, and what changed since you looked.
//
// The wording here is the feature. A level you marked being crossed is a fact
// you asked to be told; it is not a cue, and the UI must not dress it as one.
// So: no red/green urgency on events, no bell icons, no "alert" language, and
// the field is called "tell me when price passes" rather than "target".

function Event({ ev }) {
  return (
    <div className="wl-event">
      <div>{ev.text}</div>
      <div className="faint">{ev.context}</div>
    </div>
  )
}

function AddForm({ onAdded }) {
  const [q, setQ] = useState('')
  const [level, setLevel] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit() {
    const term = q.trim()
    if (!term) return
    setBusy(true); setError(null)
    try {
      const { candidates = [] } = await searchSymbols(term)
      const c = candidates[0]
      await watchAdd({
        ticker: c?.symbol || term.toUpperCase(),
        name: c?.name,
        note: note.trim() || null,
        level: level.trim() === '' ? null : Number(level),
      })
      setQ(''); setLevel(''); setNote('')
      onAdded()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card wl-add">
      <div className="lbl">Follow a company</div>
      <div className="wl-fields">
        <label>
          <span className="faint">Company or ticker</span>
          <input value={q} onChange={(e) => setQ(e.target.value)}
                 placeholder="e.g. Nvidia"
                 onKeyDown={(e) => { if (e.key === 'Enter') submit() }} />
        </label>
        <label>
          <span className="faint">Tell me when price passes (optional)</span>
          <input value={level} onChange={(e) => setLevel(e.target.value)}
                 inputMode="decimal" placeholder="e.g. 150" />
        </label>
        <label className="wl-note">
          <span className="faint">Why you are watching it</span>
          <input value={note} onChange={(e) => setNote(e.target.value)}
                 placeholder="e.g. waiting to see whether margins recover after the guidance cut" />
        </label>
        <button className="go" onClick={submit} disabled={busy || !q.trim()}>
          {busy ? 'Adding…' : 'Follow'}
        </button>
      </div>
      <p className="faint" style={{ fontSize: 11.5, lineHeight: 1.6, margin: '8px 0 0' }}>
        A level here is a number you want to be <b>told</b> about — not a target and not a
        trigger. Trade101 will say that price passed it, and nothing more.
      </p>
      {error && <div className="err" style={{ marginTop: 10 }}>⚠️ {error}</div>}
    </div>
  )
}

export default function Watchlist({ onNavigate, onOpen }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    return fetchWatchlist(true).then((r) => { setData(r); setLoading(false) })
  }
  useEffect(() => { load() }, [])

  const items = data?.items || []
  const withEvents = items.filter((i) => i.events?.length)

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo"><Logo /> Trade101</div>
          <div className="tabs">
            <a onClick={() => onNavigate('home')} style={{ cursor: 'pointer' }}>Research</a>
            <a onClick={() => onNavigate('compare')} style={{ cursor: 'pointer' }}>Comparison</a>
            <a className="on">Watchlist</a>
            <a onClick={() => onNavigate('journal')} style={{ cursor: 'pointer' }}>Journal</a>
          </div>
        </div>
        <button className="backbtn" onClick={() => onNavigate('home')}>← New search</button>
      </div>

      <div className="headline"><h1>Watchlist</h1></div>
      <p className="study-lead" style={{ maxWidth: 760 }}>{data?.note}</p>

      <AddForm onAdded={load} />

      {loading && <div className="scraping"><div className="spinner" />
        <div className="faint">Checking each company…</div></div>}

      {!loading && items.length === 0 && (
        <div className="placeholder">Nothing followed yet. Add a company above.</div>
      )}

      {withEvents.length > 0 && (
        <div className="card">
          <div className="lbl">Since you last looked</div>
          {withEvents.map((i) => (
            <div key={i.ticker} className="wl-eventgroup">
              <button className="jticker" onClick={() => onOpen(i.ticker)}>{i.ticker}</button>
              {i.events.map((ev, n) => <Event key={n} ev={ev} />)}
            </div>
          ))}
        </div>
      )}

      {items.length > 0 && (
        <div className="card">
          <div className="lbl">Following</div>
          <div className="wl-list">
            {items.map((i) => (
              <div className="wl-item" key={i.ticker}>
                <div className="wl-main">
                  <button className="jticker" onClick={() => onOpen(i.ticker)}>{i.ticker}</button>
                  <span className="faint">{i.name}</span>
                  {i.price != null && (
                    <>
                      <span className="mono">{i.price}</span>
                      {i.changePercent != null && (
                        <span className={'chip ' + (i.changePercent > 0 ? 'up' : i.changePercent < 0 ? 'down' : 'flat')}>
                          {i.changePercent > 0 ? '+' : ''}{i.changePercent}%
                        </span>
                      )}
                    </>
                  )}
                  {i.stale && <span className="asof-flag">stale</span>}
                  <button className="jdel" aria-label={`Stop following ${i.ticker}`}
                          onClick={async () => { await watchRemove(i.ticker); load() }}>✕</button>
                </div>
                {i.level != null && (
                  <div className="faint wl-level">
                    Telling you when price passes <b>{i.level}</b>
                  </div>
                )}
                {i.note && <div className="wl-yournote">“{i.note}”</div>}
                {i.error && <div className="err" style={{ marginTop: 6 }}>⚠️ {i.error}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
