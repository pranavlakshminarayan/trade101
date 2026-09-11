const BASE = 'http://127.0.0.1:8000'

export async function research(ticker, { period, interval } = {}) {
  const qs = new URLSearchParams()
  if (period) qs.set('period', period)
  if (interval) qs.set('interval', interval)
  const q = qs.toString()
  let res
  try {
    res = await fetch(`${BASE}/research/${encodeURIComponent(ticker.trim())}${q ? '?' + q : ''}`)
  } catch {
    // The backend itself is unreachable — distinct from a bad ticker.
    const e = new Error(
      'Cannot reach the Trade101 backend at ' + BASE + '. Start it with ' +
      '`uvicorn app:app --reload --port 8000` from backend/, then try again.')
    e.retryable = true
    e.failure = 'backend_unreachable'
    throw e
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Request failed (HTTP ${res.status})` }))
    const e = new Error(err.detail || `HTTP ${res.status}`)
    // A source outage is worth retrying; an unknown ticker is not.
    e.retryable = err.retryable ?? res.status >= 500
    e.failure = err.failure || (res.status === 404 ? 'not_found' : 'error')
    throw e
  }
  return res.json()
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
  try {
    const res = await fetch(`${BASE}/ecosystem/${encodeURIComponent(ticker.trim())}`)
    if (!res.ok) return null
    return res.json()
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
  try {
    const res = await fetch(`${BASE}/patterns/${encodeURIComponent(ticker.trim())}${q ? '?' + q : ''}`)
    if (!res.ok) return { patterns: [] }
    return res.json()
  } catch {
    return { patterns: [] }
  }
}

// AI narration — fetched separately so the chart never waits on it.
// In-flight dedupe: React StrictMode double-invokes effects in dev, which would
// otherwise fire two identical (paid) analysis calls; sharing the promise avoids that.
const _inflight = {}
export async function analyze(ticker) {
  const key = ticker.trim().toUpperCase()
  if (_inflight[key]) return _inflight[key]
  const p = (async () => {
    const res = await fetch(`${BASE}/analyze/${encodeURIComponent(key)}`)
    if (!res.ok) return { available: false, reason: `AI request failed (HTTP ${res.status})` }
    return res.json()
  })()
  _inflight[key] = p
  try {
    return await p
  } finally {
    delete _inflight[key]
  }
}
