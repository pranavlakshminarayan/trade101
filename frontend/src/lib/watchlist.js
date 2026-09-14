// Watchlist — companies the learner is tracking (per browser, via localStorage).
// A tracking/study list, NOT a trade list: no positions, no P&L, no signals.
// Each entry: { ticker, name, when }.
const KEY = 'trade101_watchlist'

export function getWatchlist() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]')
  } catch {
    return []
  }
}

export function isWatched(ticker) {
  const t = (ticker || '').toUpperCase()
  return getWatchlist().some((e) => e.ticker.toUpperCase() === t)
}

export function addWatch(entry) {
  try {
    const t = entry.ticker.toUpperCase()
    const rest = getWatchlist().filter((e) => e.ticker.toUpperCase() !== t)
    const next = [{ ticker: entry.ticker, name: entry.name || null, when: Date.now() }, ...rest].slice(0, 60)
    localStorage.setItem(KEY, JSON.stringify(next))
    return next
  } catch {
    return getWatchlist()
  }
}

export function removeWatch(ticker) {
  try {
    const t = (ticker || '').toUpperCase()
    const next = getWatchlist().filter((e) => e.ticker.toUpperCase() !== t)
    localStorage.setItem(KEY, JSON.stringify(next))
    return next
  } catch {
    return getWatchlist()
  }
}

export function toggleWatch(entry) {
  return isWatched(entry.ticker) ? removeWatch(entry.ticker) : addWatch(entry)
}
