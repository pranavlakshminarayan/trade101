import { useEffect, useState } from 'react'
import { METRICS, metricLabel, metricValue, factFor, lessonFor } from '../lessons.js'
import { CloseIcon } from './Icons.jsx'

// Metric analyzer + learning in ONE block: click a metric → the fact for this
// stock first, then the deeper lesson. Esc closes.
export default function Metrics({ indicators, ticker }) {
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setSelected(null) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

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
      {selected && (
        <div className="lesson">
          <button className="esc" onClick={() => setSelected(null)}>Esc <CloseIcon className="icon" /></button>
          <h4>{metricLabel(selected)} on {ticker}</h4>
          <p className="fact">{factFor(selected, indicators, ticker)}</p>
          <p style={{ margin: '8px 0 0' }}>{lessonFor(selected, indicators, ticker)}</p>
        </div>
      )}
    </div>
  )
}
