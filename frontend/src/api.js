// Dev: the API runs on its own port (separate Vite server). Production: the
// FastAPI backend serves this built frontend, so the API is same-origin (relative
// paths) — one service, one URL, no CORS. VITE_API_BASE (set in a local-only
// .env.local, gitignored) overrides the dev default — e.g. if port 8000 is
// stuck/unavailable on this machine and the backend has to run elsewhere.
const BASE = import.meta.env.DEV ? (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000') : ''

import { getAccessToken } from './lib/access.js'

// The pre-share access gate only guards /analyze and /ask (the paid calls) —
// every other endpoint is deterministic and free, so it stays open.
function authHeaders() {
  const token = getAccessToken()
  return token ? { 'X-Access-Token': token } : {}
}

// Session result cache — the fix for "switch tabs and everything reloads".
// Like a browser tab, a stock already researched this session is restored from
// memory instead of being re-fetched (and, crucially, never re-runs the paid
// /analyze call). Pass { fresh: true } to bypass it (the 7-min auto-refresh does).
const _cache = { research: new Map(), analyze: new Map(), ecosystem: new Map(), patterns: new Map(), news: new Map() }
export function clearCache(ticker) {
  if (!ticker) { for (const m of Object.values(_cache)) m.clear(); return }
  const k = ticker.trim().toUpperCase()
  for (const m of Object.values(_cache)) for (const key of [...m.keys()]) if (key.startsWith(k)) m.delete(key)
}

// Deterministic data (price/indicators/patterns/news) previously cached for
// the entire session with no expiry (docs/AUDIT.md finding M1) — a backend
// restart or code fix mid-session left the tab showing stale numbers
// indefinitely, with no way to tell (user-reported: a wrong SMA200 kept
// reappearing after the backend was already fixed and verified correct via a
// direct request — only the frontend's own forever-cache was stale). These
// four caches now expire after TTL_MS, matching the backend's own 5-min
// TTL (`services/cache.py`) and the 7-min auto-refresh cadence, so a stale
// entry ages out on its own instead of persisting until a full page reload.
// `analyze` is deliberately NOT included — it's the expensive, paid call, and
// caching it for the whole session (not just 5 min) is the intended fix for
// a different problem (docs/AUDIT.md M2/finding).
const TTL_MS = 5 * 60 * 1000
function cacheGet(map, key) {
  const entry = map.get(key)
  if (!entry) return undefined
  if (Date.now() - entry.ts > TTL_MS) { map.delete(key); return undefined }
  return entry.data
}
function cacheSet(map, key, data) { map.set(key, { data, ts: Date.now() }) }

export async function research(ticker, { period, interval, fresh } = {}) {
  const qs = new URLSearchParams()
  if (period) qs.set('period', period)
  if (interval) qs.set('interval', interval)
  const q = qs.toString()
  const ckey = `${ticker.trim().toUpperCase()}|${period || '1y'}|${interval || '1d'}`
  if (!fresh) {
    const cached = cacheGet(_cache.research, ckey)
    if (cached) return cached
  }
  const res = await fetch(`${BASE}/research/${encodeURIComponent(ticker.trim())}${q ? '?' + q : ''}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Request failed (HTTP ${res.status})` }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  const data = await res.json()
  cacheSet(_cache.research, ckey, data)
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
  const cached = cacheGet(_cache.ecosystem, k)
  if (cached) return cached
  try {
    const res = await fetch(`${BASE}/ecosystem/${encodeURIComponent(ticker.trim())}`)
    if (!res.ok) return null
    const data = await res.json()
    cacheSet(_cache.ecosystem, k, data)
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
  const cached = cacheGet(_cache.patterns, ckey)
  if (cached) return cached
  try {
    const res = await fetch(`${BASE}/patterns/${encodeURIComponent(ticker.trim())}${q ? '?' + q : ''}`)
    if (!res.ok) return { patterns: [] }
    const data = await res.json()
    cacheSet(_cache.patterns, ckey, data)
    return data
  } catch {
    return { patterns: [] }
  }
}

// Deterministic news feed — NO Claude call, no access-token/daily-cap gate.
// Loads independently of /analyze so headlines show up immediately and stay
// available even if the AI call is slow, erroring, missing a key, or capped
// (docs/AUDIT.md finding H3: news used to reach the UI only via /analyze).
export async function news(ticker) {
  const k = ticker.trim().toUpperCase()
  const cached = cacheGet(_cache.news, k)
  if (cached) return cached
  try {
    const res = await fetch(`${BASE}/news/${encodeURIComponent(ticker.trim())}`)
    if (!res.ok) return { available: false, reason: `News request failed (HTTP ${res.status})` }
    const data = await res.json()
    if (data && data.available !== false) cacheSet(_cache.news, k, data)
    return data
  } catch {
    return { available: false, reason: 'Could not reach the backend for news.' }
  }
}

// Ask-Claude chat over a stock's research bundle. Not cached — each question is
// a fresh, paid call; history is sent so the backend can keep the thread.
export async function ask(ticker, question, history = []) {
  try {
    const res = await fetch(`${BASE}/ask/${encodeURIComponent(ticker.trim())}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ question, history }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return { available: false, reason: err.detail || `Ask request failed (HTTP ${res.status})` }
    }
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
    const res = await fetch(`${BASE}/analyze/${encodeURIComponent(key)}`, { headers: authHeaders() })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      return { available: false, reason: err.detail || `AI request failed (HTTP ${res.status})` }
    }
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
