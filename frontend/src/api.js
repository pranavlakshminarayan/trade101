const BASE = 'http://127.0.0.1:8000'

export async function research(ticker, { period, interval } = {}) {
  const qs = new URLSearchParams()
  if (period) qs.set('period', period)
  if (interval) qs.set('interval', interval)
  const q = qs.toString()
  const res = await fetch(`${BASE}/research/${encodeURIComponent(ticker.trim())}${q ? '?' + q : ''}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Request failed (HTTP ${res.status})` }))
    throw new Error(err.detail || `HTTP ${res.status}`)
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
