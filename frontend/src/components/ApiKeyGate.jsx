import { useState } from 'react'
import Logo from './Logo.jsx'
import { getApiKey, setApiKey, getUserName, setUserName } from '../lib/apiKey.js'

// BYOK first-run gate (2026-09-17). The app itself (chart, indicators, news,
// patterns, ecosystem) is fully free and open — no key needed for any of
// that. This gate only asks for a key up front so the AI features (momentum
// read, Ask TC-Buddy) work from the very first click without a second prompt
// mid-research. The key is the only credential; there's no separate
// password. Stored in THIS browser only (localStorage, permanent) — never
// sent anywhere except as a header on /analyze and /ask, and the app owner's
// own key is never used for a visitor's requests.
export default function ApiKeyGate({ children }) {
  const [key, setKeyState] = useState(getApiKey())
  const [name, setNameState] = useState(getUserName())
  const [unlocked, setUnlocked] = useState(!!getApiKey())
  const [error, setError] = useState('')

  const submit = () => {
    const k = key.trim()
    if (!k) { setError('Paste an Anthropic API key to continue.') ; return }
    if (!k.startsWith('sk-ant-')) {
      setError('That doesn\'t look like an Anthropic API key (they start with "sk-ant-"). Double-check and try again.')
      return
    }
    setApiKey(k)
    setUserName(name)
    setUnlocked(true)
  }

  if (unlocked) return children

  return (
    <div className="welcome">
      <main className="welc-main" style={{ gridColumn: '1 / -1' }}>
        <div className="logo" style={{ fontSize: 22 }}><Logo size={34} /> Trade Craft</div>
        <div className="big">Bring your own <span>API key</span></div>
        <div className="sub" style={{ maxWidth: 520 }}>
          Trade Craft's charts, indicators, news, and patterns are free for anyone — no key needed.
          The AI features (momentum read, Ask TC-Buddy) run on YOUR own Anthropic API key so your
          usage is billed to you, not the app owner. It's saved only in this browser — you won't be
          asked again on this device.
        </div>

        <div className="askbox" style={{ flexDirection: 'column', alignItems: 'stretch', gap: 10, padding: 18 }}>
          <div>
            <label className="faint" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Anthropic API key</label>
            <input
              autoFocus
              type="password"
              placeholder="sk-ant-..."
              value={key}
              onChange={(e) => { setKeyState(e.target.value); setError('') }}
              onKeyDown={(e) => { if (e.key === 'Enter') submit() }}
              style={{ width: '100%', background: 'var(--bg)', border: '1px solid var(--hair)', borderRadius: 10, padding: '10px 12px', color: 'var(--ink)', fontSize: 14 }}
            />
          </div>
          <div>
            <label className="faint" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>Your name (optional)</label>
            <input
              placeholder="What should we call you?"
              value={name}
              onChange={(e) => setNameState(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') submit() }}
              style={{ width: '100%', background: 'var(--bg)', border: '1px solid var(--hair)', borderRadius: 10, padding: '10px 12px', color: 'var(--ink)', fontSize: 14 }}
            />
          </div>
          {error && <div style={{ color: 'var(--down)', fontSize: 12.5 }}>{error}</div>}
          <button className="go" onClick={submit} style={{ alignSelf: 'flex-start' }}>Continue →</button>
        </div>

        <div className="faint" style={{ fontSize: 11.5, marginTop: 14, maxWidth: 480 }}>
          Don't have a key? Get one at <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noreferrer" style={{ color: 'var(--teal)' }}>console.anthropic.com</a>.
          Your key never leaves your browser except to authenticate your own AI requests — it's
          never logged or stored on the server.
        </div>
      </main>
    </div>
  )
}
