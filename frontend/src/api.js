const BASE = 'http://localhost:8000'

export async function research(ticker) {
  const res = await fetch(`${BASE}/research/${encodeURIComponent(ticker.trim())}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Request failed (HTTP ${res.status})` }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
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
