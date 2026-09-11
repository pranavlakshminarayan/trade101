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

// ---- Phase 2: the learning engine ----------------------------------------

async function getJSON(path, fallback = null) {
  try {
    const res = await fetch(`${BASE}${path}`)
    if (!res.ok) return fallback
    return await res.json()
  } catch {
    return fallback
  }
}

// Earnings, revenue, margins, cash flow, valuation.
export const fundamentals = (ticker) =>
  getJSON(`/fundamentals/${encodeURIComponent(ticker.trim())}`)

// The VISIBLE half of a replay. Deliberately a separate call from the reveal:
// the outcome must not be in the browser before the learner commits a read.
export const replaySetup = (ticker, { horizon = 30, variant = 0 } = {}) =>
  getJSON(`/replay/${encodeURIComponent(ticker.trim())}?horizon=${horizon}&variant=${variant}`)

export const replayReveal = (ticker, { horizon = 30, variant = 0 } = {}) =>
  getJSON(`/replay/${encodeURIComponent(ticker.trim())}/reveal?horizon=${horizon}&variant=${variant}`)

// ---- learning journal ----
export const journalList = (ticker) =>
  getJSON(`/journal${ticker ? `?ticker=${encodeURIComponent(ticker)}` : ''}`, { entries: [] })

export async function journalAdd(entry) {
  const res = await fetch(`${BASE}/journal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Could not save (HTTP ${res.status})`)
  }
  return res.json()
}

export async function journalReflect(id, reflection) {
  const res = await fetch(`${BASE}/journal/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reflection }),
  })
  return res.ok
}

export async function journalDelete(id) {
  const res = await fetch(`${BASE}/journal/${id}`, { method: 'DELETE' })
  return res.ok
}

// Style lenses — deterministic, so this costs nothing to call.
export const lenses = (ticker, period) =>
  getJSON(`/lenses/${encodeURIComponent(ticker.trim())}${period ? `?period=${period}` : ''}`)

// ---- Phase 3: the research workspace -------------------------------------

export const compare = (tickers, period = '1y') =>
  getJSON(`/compare?tickers=${encodeURIComponent(tickers.join(','))}&period=${period}`)

export const watchlist = (refresh = true) =>
  getJSON(`/watchlist?refresh=${refresh}`, { items: [], errors: [] })

export async function watchAdd(entry) {
  const res = await fetch(`${BASE}/watchlist`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  })
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Could not add')
  return res.json()
}

export const watchRemove = (ticker) =>
  fetch(`${BASE}/watchlist/${encodeURIComponent(ticker)}`, { method: 'DELETE' }).then((r) => r.ok)

export const practiceList = () =>
  getJSON('/practice', { entries: [], disclaimer: '', purpose: '' })

export async function practiceOpen(entry) {
  const res = await fetch(`${BASE}/practice`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  })
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Could not open')
  return res.json()
}

export async function practiceClose(id, price, reflection) {
  const res = await fetch(`${BASE}/practice/${id}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ price, reflection }),
  })
  return res.ok
}

export const practiceDelete = (id) =>
  fetch(`${BASE}/practice/${id}`, { method: 'DELETE' }).then((r) => r.ok)
