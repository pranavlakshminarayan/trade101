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
    const existing = getWatchlist().find((e) => e.ticker.toUpperCase() === t)
    const rest = getWatchlist().filter((e) => e.ticker.toUpperCase() !== t)
    // If this ticker is already tracked, calling addWatch again (rather than
    // toggleWatch, which removes first) must not silently wipe its note.
    const next = [{ ticker: entry.ticker, name: entry.name || null, note: existing?.note || '', when: Date.now() }, ...rest].slice(0, 60)
    localStorage.setItem(KEY, JSON.stringify(next))
    return next
  } catch {
    return getWatchlist()
  }
}

// A one-line "why I'm watching this" note — the user forms a view while
// researching and otherwise has nowhere to record it (docs/AUDIT.md §9).
// Deliberately just a note, never a position/target/signal — stays inside
// the "describes, never advises" guardrail.
export function setNote(ticker, note) {
  try {
    const t = (ticker || '').toUpperCase()
    const next = getWatchlist().map((e) => (e.ticker.toUpperCase() === t ? { ...e, note } : e))
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
