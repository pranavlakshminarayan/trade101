import { useState } from 'react'
import { journalAdd } from '../api.js'

// Guided Study: observe → predict → reveal → challenge → revisit.
//
// The ordering is the entire point. Once you have read an AI's confident
// paragraph, you cannot un-read it, and whatever you "would have thought" is
// reconstructed rather than recalled. So the AI read stays hidden behind this
// component until the learner has committed their own, in writing, and what
// they wrote is saved before the reveal — not after.
//
// Nothing here asks for a trade. The saved artefact is a hypothesis and the
// evidence behind it, because that is what can be graded on revisit.

const STEPS = ['observe', 'predict', 'reveal', 'challenge', 'revisit']

const LEANS = [
  ['bullish', '▲ Bullish', 'Buyers look to be in control here'],
  ['bearish', '▼ Bearish', 'Sellers look to be in control here'],
  ['neutral', '■ Neutral', 'No clear direction — it is ranging'],
  ['mixed', '◈ Mixed', 'The signals genuinely disagree'],
]

const CONFIDENCE = ['low', 'moderate', 'high']

// Observation prompts drawn from the exact numbers already on the page, so the
// learner is pointed at evidence rather than asked to guess in the abstract.
function observations(indicators, quote) {
  const out = []
  const { rsi14, sma50, sma200, macd } = indicators || {}
  const macdLine = macd?.macd
  const macdSignal = macd?.signal
  const px = quote?.price

  if (px != null && sma50 != null) {
    out.push(`Price is ${px >= sma50 ? 'above' : 'below'} its 50-day average (${sma50}). What does that say about the medium-term trend?`)
  }
  if (sma50 != null && sma200 != null) {
    out.push(`The 50-day average is ${sma50 >= sma200 ? 'above' : 'below'} the 200-day (${sma200}). Which way is the longer trend leaning?`)
  }
  if (rsi14 != null) {
    out.push(`RSI(14) is ${rsi14}. Is momentum stretched, or is there room left in this move?`)
  }
  if (macdLine != null && macdSignal != null) {
    out.push(`MACD (${macdLine}) is ${macdLine >= macdSignal ? 'above' : 'below'} its signal line (${macdSignal}). Is momentum building or fading?`)
  }
  out.push('Do these signals agree with each other, or is one contradicting the rest?')
  return out
}

export default function StudyMode({ ticker, indicators, quote, meta, ai, onClose }) {
  const [step, setStep] = useState('observe')
  const [lean, setLean] = useState(null)
  const [confidence, setConfidence] = useState('moderate')
  const [hypothesis, setHypothesis] = useState('')
  const [picked, setPicked] = useState([])
  const [saved, setSaved] = useState(null)
  const [saveError, setSaveError] = useState(null)
  const [busy, setBusy] = useState(false)

  const prompts = observations(indicators, quote)
  const ready = lean && hypothesis.trim().length >= 20

  const toggle = (p) =>
    setPicked((c) => (c.includes(p) ? c.filter((x) => x !== p) : [...c, p]))

  // Commit: save the learner's read BEFORE the AI's is shown.
  async function commit() {
    setBusy(true); setSaveError(null)
    try {
      const entry = await journalAdd({
        ticker, kind: 'study', lean, confidence,
        hypothesis: hypothesis.trim(),
        evidence: picked,
        asOf: meta?.asOf,
        timeframe: meta?.period,
        aiLean: ai?.available ? ai.momentum?.lean : null,
      })
      setSaved(entry)
      setStep('reveal')
    } catch (e) {
      setSaveError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const aiLean = ai?.available ? ai.momentum?.lean : null
  const agrees = aiLean && lean && aiLean === lean

  return (
    <div className="modal-bg" onClick={onClose}>
      <div className="modal study" onClick={(e) => e.stopPropagation()}>
        <div className="study-head">
          <div>
            <div className="lbl">Guided study — {ticker}</div>
            <div className="faint" style={{ fontSize: 11.5 }}>
              {meta?.asOf ? `reading the data as of ${new Date(meta.asOf).toLocaleDateString()}` : ''}
            </div>
          </div>
          <button className="cand-cancel" onClick={onClose}>Close ✕</button>
        </div>

        <ol className="study-steps">
          {STEPS.map((s) => (
            <li key={s} className={s === step ? 'on' : STEPS.indexOf(s) < STEPS.indexOf(step) ? 'done' : ''}>
              {s}
            </li>
          ))}
        </ol>

        {step === 'observe' && (
          <div className="study-body">
            <p className="study-lead">
              Before any opinion — yours or the app's — just look. Tick the observations
              you think actually matter here.
            </p>
            <ul className="obs">
              {prompts.map((p, i) => (
                <li key={i}>
                  <label>
                    <input type="checkbox" checked={picked.includes(p)} onChange={() => toggle(p)} />
                    <span>{p}</span>
                  </label>
                </li>
              ))}
            </ul>
            <div className="study-foot">
              <span className="faint">{picked.length} selected</span>
              <button className="go" onClick={() => setStep('predict')}>Next: write your read →</button>
            </div>
          </div>
        )}

        {step === 'predict' && (
          <div className="study-body">
            <p className="study-lead">
              Now commit. What do you think is happening in this chart, and which evidence
              tells you so? This is saved before you see the AI's read — so it is genuinely
              yours.
            </p>
            <div className="leanpick">
              {LEANS.map(([v, label, hint]) => (
                <button key={v} className={'leanbtn' + (lean === v ? ' on' : '')}
                        onClick={() => setLean(v)} title={hint}>
                  <b>{label}</b><span className="faint">{hint}</span>
                </button>
              ))}
            </div>
            <div className="conflevel">
              <span className="faint">How sure are you?</span>
              {CONFIDENCE.map((c) => (
                <button key={c} className={'chipx' + (confidence === c ? ' on' : '')}
                        onClick={() => setConfidence(c)}>{c}</button>
              ))}
            </div>
            <textarea
              className="hypo" rows={4} value={hypothesis}
              onChange={(e) => setHypothesis(e.target.value)}
              placeholder="e.g. Price has held above the 200-day for three months and RSI is mid-range, so the uptrend looks intact rather than stretched — but volume has been falling, which makes me less sure."
            />
            <div className="faint" style={{ fontSize: 11.5 }}>
              {hypothesis.trim().length < 20
                ? `Write a little more — ${20 - hypothesis.trim().length} more characters. A saved lean with no reasoning teaches nothing when you revisit it.`
                : 'Good — that is something you can grade yourself against later.'}
            </div>
            {saveError && <div className="err" style={{ marginTop: 10 }}>⚠️ {saveError}</div>}
            <div className="study-foot">
              <button className="cand-cancel" onClick={() => setStep('observe')}>← Back</button>
              <button className="go" disabled={!ready || busy} onClick={commit}>
                {busy ? 'Saving…' : 'Commit my read & reveal the AI →'}
              </button>
            </div>
          </div>
        )}

        {step === 'reveal' && (
          <div className="study-body">
            <div className="compare">
              <div className="compare-col">
                <div className="lbl">Your read</div>
                <span className={'chip ' + (lean === 'bullish' ? 'up' : lean === 'bearish' ? 'down' : 'flat')}>{lean}</span>
                <span className="conf">confidence: {confidence}</span>
                <p>{hypothesis}</p>
              </div>
              <div className="compare-col">
                <div className="lbl">Trade101's read</div>
                {aiLean ? (
                  <>
                    <span className={'chip ' + (aiLean === 'bullish' ? 'up' : aiLean === 'bearish' ? 'down' : 'flat')}>{aiLean}</span>
                    <span className="conf">confidence: {ai.momentum?.confidence}</span>
                    <p>{ai.momentum?.summary}</p>
                  </>
                ) : (
                  <p className="placeholder">
                    The AI read is unavailable, so there is nothing to compare against.
                    Your own read is still saved — that was the valuable half.
                  </p>
                )}
              </div>
            </div>
            {aiLean && (
              <div className={'verdict ' + (agrees ? 'agree' : 'differ')}>
                {agrees
                  ? 'You and the model landed in the same place. That is reassuring, not proof — check whether you got there by the same evidence, or whether you agreed for different reasons.'
                  : 'You disagree. That is the most useful outcome in this exercise: one of you is weighting evidence the other discounted. Work out which, rather than deferring.'}
              </div>
            )}
            <div className="study-foot">
              <button className="go" onClick={() => setStep('challenge')}>Next: challenge it →</button>
            </div>
          </div>
        )}

        {step === 'challenge' && (
          <div className="study-body">
            <p className="study-lead">
              Now argue the other side. A read you cannot argue against is one you have
              not really tested.
            </p>
            <ul className="challenge">
              <li>What would have to happen on this chart for your read to be <b>wrong</b>?</li>
              <li>Which single piece of evidence are you leaning on hardest? What if it is noise?</li>
              <li>Is any signal here contradicting the others — and did you quietly discount it?</li>
              {ai?.coverage?.level !== 'ok' && (
                <li><b>Source coverage is {ai?.coverage?.level || 'thin'}.</b> How much of your
                    confidence came from the news, and should it have?</li>
              )}
              <li>If you saw this exact chart on a company you had never heard of, would you
                  read it the same way?</li>
            </ul>
            <div className="study-foot">
              <button className="cand-cancel" onClick={() => setStep('reveal')}>← Back</button>
              <button className="go" onClick={() => setStep('revisit')}>Finish →</button>
            </div>
          </div>
        )}

        {step === 'revisit' && (
          <div className="study-body">
            <p className="study-lead">Saved to your journal.</p>
            <p>
              Come back to this entry in a few weeks. The question when you do is
              <b> not</b> "was I right?" — a sound read loses often and a sloppy one wins
              often. The question is whether the <b>reasoning</b> held up: did the evidence
              you leaned on turn out to be the evidence that mattered?
            </p>
            {saved && (
              <div className="savedbox">
                <span className="faint">Entry #{saved.id} · {ticker} · {saved.created_at}</span>
                <p style={{ margin: '6px 0 0' }}>{saved.hypothesis}</p>
              </div>
            )}
            <div className="study-foot">
              <button className="go" onClick={onClose}>Done</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
