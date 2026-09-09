const BASE = 'http://localhost:8000'

export async function research(ticker) {
  const res = await fetch(`${BASE}/research/${encodeURIComponent(ticker.trim())}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Request failed (HTTP ${res.status})` }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}
