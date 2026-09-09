// Persistent research history (per browser, via localStorage).
// Each entry: { ticker, name, lean, summary, when }.
const KEY = 'trade101_history'

export function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]')
  } catch {
    return []
  }
}

export function addHistory(entry) {
  try {
    const rest = getHistory().filter((e) => e.ticker !== entry.ticker)
    const next = [{ ...entry, when: Date.now() }, ...rest].slice(0, 50)
    localStorage.setItem(KEY, JSON.stringify(next))
    return next
  } catch {
    return getHistory()
  }
}

export function clearHistory() {
  try {
    localStorage.removeItem(KEY)
  } catch { /* ignore */ }
}

export function timeAgo(ts) {
  const s = Math.floor((Date.now() - ts) / 1000)
  if (s < 60) return 'just now'
  const m = Math.floor(s / 60); if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60); if (h < 24) return `${h}h ago`
  const d = Math.floor(h / 24); if (d < 7) return `${d}d ago`
  return new Date(ts).toLocaleDateString()
}
