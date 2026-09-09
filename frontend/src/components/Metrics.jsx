import { useEffect, useState } from 'react'
import { METRICS, metricLabel, metricValue, lessonFor } from '../lessons.js'

// Merged metric analyzer + learning: click a metric → its lesson opens; Esc closes.
export default function Metrics({ indicators, ticker }) {
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setSelected(null) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const lesson = selected ? lessonFor(selected, indicators, ticker) : null

  return (
    <div className="card">
      <div className="lbl">Metrics &amp; learning — tap a metric to learn it on {ticker}</div>
      <div className="metrics">
        {METRICS.map((m) => (
          <button
            key={m}
            className={'metric' + (selected === m ? ' sel' : '')}
            onClick={() => setSelected(selected === m ? null : m)}
          >
            <div className="k">{metricLabel(m)}</div>
            <div className="v mono">{metricValue(m, indicators)}</div>
          </button>
        ))}
      </div>
      {lesson && (
        <div className="lesson">
          <button className="esc" onClick={() => setSelected(null)}>Esc ✕</button>
          <h4>{lesson.title}</h4>
          <p style={{ margin: 0 }}>{lesson.body}</p>
        </div>
      )}
    </div>
  )
}
