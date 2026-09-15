// Practice Lab — a simulated portfolio + trade journal (per browser, via
// localStorage). Entirely deterministic: no AI, no real money, no live broker,
// no advice — the user logs their OWN hypothetical decisions at real live
// prices and later sees the real outcome. Mirrors lib/watchlist.js's storage
// pattern.
//
// Scope (v1): a single simulated cash pool, USD only. Mixing currencies into
// one balance would need a real FX rate, which this app doesn't have and
// won't fake — so buys are restricted to USD-priced tickers for now.
const KEY = 'trade101_practice_lab'
export const STARTING_CASH = 100000

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY))
    if (raw && typeof raw.cash === 'number' && raw.positions && Array.isArray(raw.closed)) return raw
  } catch {
    // fall through to a fresh portfolio
  }
  return { cash: STARTING_CASH, positions: {}, closed: [] }
}

function save(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state))
  } catch {
    // localStorage unavailable — the in-memory state still works for this
    // page load, it just won't persist.
  }
  return state
}

export function getPortfolio() {
  return load()
}

export function resetPortfolio() {
  return save({ cash: STARTING_CASH, positions: {}, closed: [] })
}

// Buy `qty` shares of `ticker` at `price` — always the real live quote price
// at the moment of logging, never a user-typed number, so the numbers stay
// exact even though the trade itself is hypothetical.
export function buy({ ticker, name, qty, price, reason }) {
  qty = Number(qty)
  if (!ticker || !price || !(qty > 0)) return { ok: false, error: 'Enter a valid quantity.' }
  const state = load()
  const cost = qty * price
  if (cost > state.cash) {
    return { ok: false, error: `That would cost $${cost.toFixed(2)}, more than your $${state.cash.toFixed(2)} practice cash.` }
  }
  const t = ticker.toUpperCase()
  const existing = state.positions[t]
  const nextQty = (existing?.qty || 0) + qty
  const priorCost = existing ? existing.avgCost * existing.qty : 0
  state.positions[t] = {
    ticker: t,
    name: name || existing?.name || t,
    qty: nextQty,
    avgCost: (priorCost + cost) / nextQty,
    entries: [...(existing?.entries || []), { qty, price, date: Date.now(), reason: reason || '' }],
  }
  state.cash -= cost
  return { ok: true, state: save(state) }
}

// Sell `qty` shares of `ticker` at `price`, realizing P&L against the
// position's average cost basis, and logs a closed-trade journal entry.
export function sell({ ticker, qty, price, reason }) {
  qty = Number(qty)
  const state = load()
  const t = (ticker || '').toUpperCase()
  const pos = state.positions[t]
  if (!pos) return { ok: false, error: "You don't hold a practice position in this ticker." }
  if (!(qty > 0)) return { ok: false, error: 'Enter a valid quantity.' }
  if (qty > pos.qty) return { ok: false, error: `You only hold ${pos.qty} practice shares of ${t}.` }

  const proceeds = qty * price
  const costBasis = qty * pos.avgCost
  const realizedPnl = proceeds - costBasis
  const remaining = pos.qty - qty
  if (remaining <= 1e-9) delete state.positions[t]
  else state.positions[t] = { ...pos, qty: remaining }
  state.cash += proceeds
  state.closed = [{
    ticker: t, name: pos.name, qty,
    entryPrice: pos.avgCost, exitPrice: price,
    realizedPnl, realizedPct: costBasis ? (realizedPnl / costBasis) * 100 : 0,
    reason: reason || '', date: Date.now(),
  }, ...state.closed].slice(0, 200)
  return { ok: true, state: save(state) }
}
