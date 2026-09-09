// AI momentum read — synthesis + confidence + sourced evidence + learning note.
// Falls back gracefully: while loading, and when the AI is unavailable (no key),
// the deterministic Technical Snapshot beside it still carries the facts.

function leanClass(lean) {
  if (lean === 'bullish') return 'up'
  if (lean === 'bearish') return 'down'
  return 'flat'
}

export default function AiRead({ ai, loading }) {
  if (loading) {
    return (
      <div className="card">
        <div className="lbl">AI momentum read</div>
        <div className="placeholder">Reading the signals…</div>
      </div>
    )
  }

  if (!ai || !ai.available) {
    return (
      <div className="card">
        <div className="lbl">AI momentum read</div>
        <div className="placeholder">
          {ai?.reason || 'AI narration unavailable.'} The Technical Snapshot (facts) still applies.
        </div>
      </div>
    )
  }

  const m = ai.momentum || {}
  return (
    <div className="card">
      <div className="lbl">AI momentum read <span className="faint" style={{ textTransform: 'none', letterSpacing: 0 }}>· describes, never advises</span></div>
      <div className="headline" style={{ margin: '0 0 6px', gap: 10 }}>
        <span className={'chip ' + leanClass(m.lean)} style={{ fontSize: 15 }}>{m.lean || '—'}</span>
        <span className="conf">confidence: {m.confidence || '—'}</span>
      </div>
      <p style={{ margin: '6px 0 0', fontSize: 14 }}>{m.summary}</p>
      {m.evidence?.length > 0 && (
        <ul className="why">
          {m.evidence.map((e, i) => (
            <li key={i}><b>{e.point}</b> <span className="src">[{e.source}]</span></li>
          ))}
        </ul>
      )}
      {ai.learning_note && (
        <div className="lesson" style={{ marginTop: 12 }}>
          <h4>Learn the read</h4>
          <p style={{ margin: 0 }}>{ai.learning_note}</p>
        </div>
      )}
    </div>
  )
}
