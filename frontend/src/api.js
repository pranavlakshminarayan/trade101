// Dev: the API runs on its own port (separate Vite server). Production: the
// FastAPI backend serves this built frontend, so the API is same-origin (relative
// paths) — one service, one URL, no CORS.
const BASE = import.meta.env.DEV ? 'http://127.0.0.1:8000' : ''

// Session result cache — the fix for "switch tabs and everything reloads".
// Like a browser tab, a stock already researched this session is restored from
// memory instead of being re-fetched (and, crucially, never re-runs the paid
// /analyze call). Pass { fresh: true } to bypass it (the 7-min auto-refresh does).
const _cache = { research: new Map(), analyze: new Map(), ecosystem: new Map(), patterns: new Map() }
export function clearCache(ticker) {
  if (!ticker) { for (const m of Object.values(_cache)) m.clear(); return }
  const k = ticker.trim().toUpperCase()
  for (const m of Object.values(_cache)) for (const key of [...m.keys()]) if (key.startsWith(k)) m.delete(key)
}

export async function research(ticker, { period, interval, fresh } = {}) {
  const qs = new URLSearchParams()
  if (period) qs.set('period', period)
  if (interval) qs.set('interval', interval)
  const q = qs.toString()
  const ckey = `${ticker.trim().toUpperCase()}|${period || '1y'}|${interval || '1d'}`
  if (!fresh && _cache.research.has(ckey)) return _cache.research.get(ckey)
  const res = await fetch(`${BASE}/research/${encodeURIComponent(ticker.trim())}${q ? '?' + q : ''}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Request failed (HTTP ${res.status})` }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  const data = await res.json()
  _cache.research.set(ckey, data)
  return data
}

// Resolve a company name or partial ticker to candidate symbols.
export async function search(q) {
  try {
    const res = await fetch(`${BASE}/search?q=${encodeURIComponent(q.trim())}`)
    if (!res.ok) return { candidates: [] }
    return res.json()
  } catch {
    return { candidates: [] }
  }
}

// Company profile / ecosystem: sector, industry, beta, market cap, peers.
export async function ecosystem(ticker) {
  const k = ticker.trim().toUpperCase()
  if (_cache.ecosystem.has(k)) return _cache.ecosystem.get(k)
  try {
    const res = await fetch(`${BASE}/ecosystem/${encodeURIComponent(ticker.trim())}`)
    if (!res.ok) return null
    const data = await res.json()
    _cache.ecosystem.set(k, data)
    return data
  } catch {
    return null
  }
}

// Chart-pattern detection for a given timeframe.
export async function patterns(ticker, { period, interval } = {}) {
  const qs = new URLSearchParams()
  if (period) qs.set('period', period)
  if (interval) qs.set('interval', interval)
  const q = qs.toString()
  const ckey = `${ticker.trim().toUpperCase()}|${period || '1y'}|${interval || '1d'}`
  if (_cache.patterns.has(ckey)) return _cache.patterns.get(ckey)
  try {
    const res = await fetch(`${BASE}/patterns/${encodeURIComponent(ticker.trim())}${q ? '?' + q : ''}`)
    if (!res.ok) return { patterns: [] }
    const data = await res.json()
    _cache.patterns.set(ckey, data)
    return data
  } catch {
    return { patterns: [] }
  }
}

// Ask-Claude chat over a stock's research bundle. Not cached — each question is
// a fresh, paid call; history is sent so the backend can keep the thread.
export async function ask(ticker, question, history = []) {
  try {
    const res = await fetch(`${BASE}/ask/${encodeURIComponent(ticker.trim())}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history }),
    })
    if (!res.ok) return { available: false, reason: `Ask request failed (HTTP ${res.status})` }
    return res.json()
  } catch {
    return { available: false, reason: 'Could not reach the backend for Ask-Claude.' }
  }
}

// AI narration — fetched separately so the chart never waits on it. This is the
// expensive, paid call, so its result is cached for the whole session: revisiting
// a stock (or returning from another tab) restores the read without spending the
// key again. In-flight dedupe still guards React StrictMode's double-invoke.
const _inflight = {}
export async function analyze(ticker) {
  const key = ticker.trim().toUpperCase()
  if (_cache.analyze.has(key)) return _cache.analyze.get(key)
  if (_inflight[key]) return _inflight[key]
  const p = (async () => {
    const res = await fetch(`${BASE}/analyze/${encodeURIComponent(key)}`)
    if (!res.ok) return { available: false, reason: `AI request failed (HTTP ${res.status})` }
    return res.json()
  })()
  _inflight[key] = p
  try {
    const result = await p
    // Cache only a usable result; let a transient failure be retried next time.
    if (result && result.available !== false) _cache.analyze.set(key, result)
    return result
  } finally {
    delete _inflight[key]
  }
}
