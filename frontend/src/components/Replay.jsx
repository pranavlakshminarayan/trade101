import { useEffect, useState } from 'react'
import PriceChart from './PriceChart.jsx'
import { journalAdd, replayReveal, replaySetup } from '../api.js'

// Retrospective replay — read a chart without knowing the answer.
//
// The outcome is fetched from a SEPARATE endpoint, and only after the learner
// has written and saved a read. That is not merely a UI convention: if the
// future bars were in the browser at all, any bug, any devtools glance, any
// accidental render would spoil the exercise permanently.
//
// The reveal always carries the one-sample caveat. Watching a pattern "work"
// once is the fastest way to learn a false lesson, and this screen is exactly
// where that misreading would form.

export default function Replay({ ticker, onClose }) {
  const [variant, setVariant] = useState(0)
  const [setup, setSetup] = useState(null)
  const [loading, setLoading] = useState(true)
  const [hypothesis, setHypothesis] = useState('')
  const [lean, setLean] = useState(null)
  const [revealed, setRevealed] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let alive = true
    setLoading(true); setSetup(null); setRevealed(null)
    setHypothesis(''); setLean(null); setError(null)
    replaySetup(ticker, { variant }).then((r) => { if (alive) { setSetup(r); setLoading(false) } })
    return () => { alive = false }
  }, [ticker, variant])

  const ready = lean && hypothesis.trim().length >= 20

  async function commitAndReveal() {
    setBusy(true); setError(null)
    try {
      // Save first — so the record cannot be edited once the answer is known.
      await journalAdd({
        ticker, kind: 'replay', lean, hypothesis: hypothesis.trim(),
        asOf: setup.asOf, timeframe: `replay+${setup.horizon}`,
      })
      const r = await replayReveal(ticker, { variant })
      setRevealed(r)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const outcome = revealed?.outcome
  // Only once revealed do the two series get concatenated for display.
  const chartData = revealed?.available
    ? [...setup.ohlcv, ...revealed.ohlcv]
    : setup?.ohlcv

  return (
    <div className="modal-bg" onClick={onClose}>
      <div className="modal study wide" onClick={(e) => e.stopPropagation()}>
        <div className="study-head">
          <div>
            <div className="lbl">Retrospective replay — {ticker}</div>
            <div className="faint" style={{ fontSize: 11.5 }}>
              A real window from this stock's own history, with the ending hidden.
            </div>
          </div>
          <button className="cand-cancel" onClick={onClose}>Close ✕</button>
        </div>

        {loading && <div className="scraping"><div className="spinner" />
          <div className="faint">Loading a historical window…</div></div>}

        {!loading && !setup && (
          <div className="placeholder">Could not load a replay for {ticker}.</div>
        )}

        {!loading && setup && setup.available === false && (
          <div className="placeholder">{setup.reason}</div>
        )}

        {!loading && setup?.available && (
          <div className="study-body">
            <p className="study-lead">{setup.prompt}</p>

            <div className="chartwrap-outer">
              <PriceChart ohlcv={chartData} type="candles" />
              {revealed?.available && (
                <div className="revealmark">
                  ← your read was made here · {setup.horizon} bars revealed →
                </div>
              )}
            </div>

            {!revealed && (
              <>
                <div className="leanpick">
                  {[['bullish', '▲ Bullish'], ['bearish', '▼ Bearish'],
                    ['neutral', '■ Neutral'], ['mixed', '◈ Mixed']].map(([v, label]) => (
                    <button key={v} className={'leanbtn' + (lean === v ? ' on' : '')}
                            onClick={() => setLean(v)}><b>{label}</b></button>
                  ))}
                </div>
                <textarea
                  className="hypo" rows={3} value={hypothesis}
                  onChange={(e) => setHypothesis(e.target.value)}
                  placeholder="What do you think was happening at this point, and which evidence on the chart tells you that?"
                />
                <div className="faint" style={{ fontSize: 11.5 }}>{setup.caveat}</div>
                {error && <div className="err" style={{ marginTop: 10 }}>⚠️ {error}</div>}
                <div className="study-foot">
                  <button className="cand-cancel" onClick={() => setVariant((v) => v + 1)}>
                    Different window
                  </button>
                  <button className="go" disabled={!ready || busy} onClick={commitAndReveal}>
                    {busy ? 'Saving…' : 'Commit my read & reveal what followed →'}
                  </button>
                </div>
              </>
            )}

            {revealed?.available && (
              <>
                <div className="compare">
                  <div className="compare-col">
                    <div className="lbl">Your read</div>
                    <span className={'chip ' + (lean === 'bullish' ? 'up' : lean === 'bearish' ? 'down' : 'flat')}>{lean}</span>
                    <p>{hypothesis}</p>
                  </div>
                  <div className="compare-col">
                    <div className="lbl">What followed ({outcome.barsRevealed} bars)</div>
                    <span className={'chip ' + (outcome.changePercent >= 0 ? 'up' : 'down')}>
                      {outcome.changePercent > 0 ? '+' : ''}{outcome.changePercent}%
                    </span>
                    <ul className="why">
                      <li>Peak <b>{outcome.peak.percent > 0 ? '+' : ''}{outcome.peak.percent}%</b> after {outcome.peak.bars} bars ({outcome.peak.date})</li>
                      <li>Trough <b>{outcome.trough.percent}%</b> after {outcome.trough.bars} bars ({outcome.trough.date})</li>
                      <li>Deepest drawdown from the cut: <b>{outcome.maxDrawdownPercent}%</b></li>
                    </ul>
                  </div>
                </div>

                <div className="verdict differ">{revealed.caveat}</div>

                <div className="study-foot">
                  <button className="cand-cancel" onClick={() => setVariant((v) => v + 1)}>
                    Try another window
                  </button>
                  <button className="go" onClick={onClose}>Done</button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
