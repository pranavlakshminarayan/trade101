import { useEffect, useRef, useState } from 'react'
import { ask } from '../api.js'

// Floating chatbot widget: a bubble pinned bottom-right that opens an overlay
// panel over the page content (like a website "Chat with us" bot). Per-ticker
// threads live in module memory so switching stocks/tabs and coming back keeps
// the conversation.
const threads = {}

const STARTERS = [
  'What is the RSI telling us here?',
  'Why might the stock have moved recently?',
  'Explain what the moving averages show.',
]

export default function AskClaude({ ticker }) {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState(() => threads[ticker] || [])
  const [q, setQ] = useState('')
  const [busy, setBusy] = useState(false)
  const listRef = useRef(null)

  useEffect(() => { setMsgs(threads[ticker] || []) }, [ticker])
  useEffect(() => { threads[ticker] = msgs }, [ticker, msgs])
  useEffect(() => { if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight }, [msgs, busy, open])

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
    <>
      {!open && (
        <button className="askbubble-btn" onClick={() => setOpen(true)} aria-label="Ask Claude about this stock" title="Ask Claude">
          <span className="askbubble-icon">✦</span>
          <span className="askbubble-label">Ask Claude</span>
        </button>
      )}

      {open && (
        <div className="askpanel" role="dialog" aria-label="Ask Claude">
          <div className="askpanel-head">
            <div>
              <div className="askpanel-title">Ask Claude</div>
              <div className="askpanel-sub">about {ticker} · grounded in this data, never advice</div>
            </div>
            <button className="askpanel-close" onClick={() => setOpen(false)} aria-label="Close">–</button>
          </div>

          <div className="askmsgs" ref={listRef}>
            {msgs.length === 0 && !busy && (
              <div className="placeholder" style={{ fontSize: 13 }}>
                Hi — ask about {ticker}'s indicators, news, or what the signals mean together. Answers use the exact numbers and sourced evidence on this page, and never give buy/sell advice.
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
              autoFocus
            />
            <button className="go" disabled={busy || !q.trim()} onClick={() => send()}>Ask</button>
          </div>
          <div className="faint" style={{ fontSize: 11, marginTop: 6 }}>Each question makes one Claude call — educational only, not financial advice.</div>
        </div>
      )}
    </>
  )
}
