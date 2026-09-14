import { useEffect, useRef, useState } from 'react'
import { ask } from '../api.js'

// Per-ticker chat threads kept in module memory so switching tabs / stocks and
// coming back restores the conversation (same principle as the api result cache).
const threads = {}

const STARTERS = [
  'What is the RSI telling us here?',
  'Why might the stock have moved recently?',
  'Explain what the moving averages show.',
]

export default function AskClaude({ ticker }) {
  const [msgs, setMsgs] = useState(() => threads[ticker] || [])
  const [q, setQ] = useState('')
  const [busy, setBusy] = useState(false)
  const listRef = useRef(null)

  useEffect(() => { setMsgs(threads[ticker] || []) }, [ticker])
  useEffect(() => { threads[ticker] = msgs }, [ticker, msgs])
  useEffect(() => { if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight }, [msgs, busy])

  async function send(text) {
    const question = (text ?? q).trim()
    if (!question || busy) return
    setQ('')
    const history = msgs.map((m) => ({ role: m.role, content: m.content }))
    const next = [...msgs, { role: 'user', content: question }]
    setMsgs(next)
    setBusy(true)
    const res = await ask(ticker, question, history)
    const answer = res?.available ? res.answer : (res?.reason || 'Ask-Claude is unavailable right now.')
    setMsgs([...next, { role: 'assistant', content: answer, ok: !!res?.available }])
    setBusy(false)
  }

  return (
    <div className="card askcard">
      <div className="lbl">Ask Claude <span className="faint" style={{ textTransform: 'none', letterSpacing: 0 }}>· about {ticker} · grounded in this data, never advice</span></div>

      <div className="askmsgs" ref={listRef}>
        {msgs.length === 0 && !busy && (
          <div className="placeholder" style={{ fontSize: 13 }}>
            Ask about this stock's indicators, news, or what the signals mean together. Answers use the exact numbers and sourced evidence on this page — and never give buy/sell advice.
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={'askmsg ' + m.role}>
            <span className="askwho">{m.role === 'user' ? 'You' : 'Claude'}</span>
            <div className="askbubble">{m.content}</div>
          </div>
        ))}
        {busy && (
          <div className="askmsg assistant">
            <span className="askwho">Claude</span>
            <div className="askbubble faint"><span className="spinner-inline" /> thinking…</div>
          </div>
        )}
      </div>

      {msgs.length === 0 && !busy && (
        <div className="askstarters">
          {STARTERS.map((s) => (
            <button key={s} className="chipx" onClick={() => send(s)}>{s}</button>
          ))}
        </div>
      )}

      <div className="askinput">
        <input
          placeholder={`Ask about ${ticker}…`}
          value={q}
          disabled={busy}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') send() }}
        />
        <button className="go" disabled={busy || !q.trim()} onClick={() => send()}>Ask</button>
      </div>
      <div className="faint" style={{ fontSize: 11, marginTop: 6 }}>Each question makes one Claude call — educational only, not financial advice.</div>
    </div>
  )
}
