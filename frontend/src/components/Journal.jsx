import { useEffect, useState } from 'react'
import Logo from './Logo.jsx'
import { journalDelete, journalList, journalReflect } from '../api.js'

// The learning journal — what you thought, and why.
//
// Entries are reads, not trades. On revisit the question is never "did this
// make money"; it is whether the reasoning held up. The UI is built around that
// distinction, which is why the reflection box asks about evidence rather than
// outcome, and why no entry has a P&L anywhere.

const KIND = {
  study: { label: 'Guided study', icon: '◎' },
  replay: { label: 'Replay', icon: '⟲' },
  note: { label: 'Note', icon: '✎' },
}

function leanChip(lean) {
  if (!lean) return null
  const cls = lean === 'bullish' ? 'up' : lean === 'bearish' ? 'down' : 'flat'
  const a = lean === 'bullish' ? '▲' : lean === 'bearish' ? '▼' : '■'
  return <span className={'chip ' + cls}>{a} {lean}</span>
}

function Entry({ e, onChanged, onOpen }) {
  const [draft, setDraft] = useState(e.reflection || '')
  const [editing, setEditing] = useState(false)
  const [saved, setSaved] = useState(false)
  const k = KIND[e.kind] || KIND.note
  const disagreed = e.ai_lean && e.lean && e.ai_lean !== e.lean

  async function save() {
    if (await journalReflect(e.id, draft)) {
      setSaved(true); setEditing(false); onChanged()
      setTimeout(() => setSaved(false), 2000)
    }
  }

  return (
    <div className="jentry">
      <div className="jentry-head">
        <span className="jkind" title={k.label}>{k.icon} {k.label}</span>
        <button className="jticker" onClick={() => onOpen(e.ticker)}>{e.ticker}</button>
        {leanChip(e.lean)}
        {e.confidence && <span className="conf">confidence: {e.confidence}</span>}
        <span className="faint jwhen">
          {new Date(e.created_at).toLocaleString()}
          {e.as_of ? ` · data as of ${new Date(e.as_of).toLocaleDateString()}` : ''}
        </span>
        <button className="jdel" title="Delete this entry"
                onClick={async () => { if (await journalDelete(e.id)) onChanged() }}>✕</button>
      </div>

      <p className="jhypo">{e.hypothesis}</p>

      {e.evidence?.length > 0 && (
        <div className="jevidence">
          <span className="faint">Evidence you leaned on:</span>
          <ul>{e.evidence.map((x, i) => <li key={i}>{x}</li>)}</ul>
        </div>
      )}

      {e.ai_lean && (
        <div className={'jcompare ' + (disagreed ? 'differ' : 'agree')}>
          Trade101 read it as <b>{e.ai_lean}</b> — {disagreed
            ? 'you disagreed at the time. Worth revisiting which of you was weighting the right evidence.'
            : 'you agreed at the time. Check whether you agreed for the same reasons.'}
        </div>
      )}

      {e.outcome && (
        <div className="joutcome">
          What followed over {e.outcome.barsRevealed} bars: <b>{e.outcome.changePercent > 0 ? '+' : ''}{e.outcome.changePercent}%</b>
          <span className="faint"> — one sample; it grades the market, not your reasoning.</span>
        </div>
      )}

      <div className="jreflect">
        {!editing && e.reflection && <p className="jrefl-text">↩ {e.reflection}</p>}
        {!editing && (
          <button className="collapse" onClick={() => setEditing(true)}>
            {e.reflection ? 'Edit reflection' : '+ Revisit: did the reasoning hold up?'}
          </button>
        )}
        {editing && (
          <>
            <textarea rows={3} className="hypo" value={draft}
                      onChange={(ev) => setDraft(ev.target.value)}
                      placeholder="Not 'was I right' — was the evidence you leaned on the evidence that mattered? What would you look at differently now?" />
            <div className="study-foot">
              <button className="cand-cancel" onClick={() => { setEditing(false); setDraft(e.reflection || '') }}>Cancel</button>
              <button className="go" onClick={save}>Save reflection</button>
            </div>
          </>
        )}
        {saved && <span className="faint"> saved</span>}
      </div>
    </div>
  )
}

export default function Journal({ onNavigate, onOpen }) {
  const [entries, setEntries] = useState(null)
  const [filter, setFilter] = useState('')

  const load = () => journalList().then((r) => setEntries(r.entries || []))
  useEffect(() => { load() }, [])

  const shown = (entries || []).filter(
    (e) => !filter || e.ticker.toLowerCase().includes(filter.toLowerCase()))

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo"><Logo /> Trade101</div>
          <div className="tabs">
            <a onClick={() => onNavigate('home')} style={{ cursor: 'pointer' }}>Research</a>
            <a onClick={() => onNavigate('compare')} style={{ cursor: 'pointer' }}>Comparison</a>
            <a onClick={() => onNavigate('history')} style={{ cursor: 'pointer' }}>History</a>
            <a className="on">Journal</a>
          </div>
        </div>
        <button className="backbtn" onClick={() => onNavigate('home')}>← New search</button>
      </div>

      <div className="headline"><h1>Learning journal</h1></div>
      <p className="study-lead" style={{ maxWidth: 720 }}>
        Your own reads, saved before you saw the app's. Revisiting them is the point:
        a read that lost for sound reasons is worth more than one that won by luck, and
        only the written version can tell you which you had.
      </p>

      {entries === null && <div className="scraping"><div className="spinner" /><div className="faint">Loading…</div></div>}

      {entries?.length === 0 && (
        <div className="placeholder">
          No entries yet. Open any stock and use <b>Study this chart</b> or <b>Replay</b> —
          both save your read before revealing anything.
        </div>
      )}

      {entries?.length > 0 && (
        <>
          <div className="strip-search" style={{ maxWidth: 320, marginBottom: 16 }}>
            <span className="faint">🔍</span>
            <input placeholder="Filter by ticker…" value={filter}
                   onChange={(e) => setFilter(e.target.value)} />
          </div>
          <div className="jlist">
            {shown.map((e) => <Entry key={e.id} e={e} onChanged={load} onOpen={onOpen} />)}
          </div>
        </>
      )}
    </div>
  )
}
