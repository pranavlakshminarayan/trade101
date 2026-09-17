import { useEffect, useState } from 'react'
import Logo from './Logo.jsx'
import { research, search } from '../api.js'
import { currencySymbol } from '../lib/currency.js'
import { getPortfolio, resetPortfolio, buy, sell, STARTING_CASH } from '../lib/practiceLab.js'
import { PlusIcon } from './Icons.jsx'

function money(v) {
  const n = Number(v) || 0
  return (n < 0 ? '-$' : '$') + Math.abs(n).toFixed(2)
}
function pctStr(v) {
  if (v == null) return '—'
  return (v > 0 ? '+' : '') + v.toFixed(2) + '%'
}
function pnlClass(v) {
  return v > 0 ? 'pos' : v < 0 ? 'neg' : 'faint'
}

// A hypothetical trade journal + simulated portfolio — deliberately separate
// from the main research/learning flow. Deterministic only (no Claude spend):
// every price is a real live quote fetched at the moment of logging, never a
// user-typed number, and nothing here is a recommendation — it only records
// the user's OWN decisions so they can reflect on the outcome later.
export default function PracticeLab({ onNavigate, onOpen, onHome }) {
  const [portfolio, setPortfolio] = useState(getPortfolio())
  const [quotes, setQuotes] = useState({}) // ticker -> live quote

  const tickers = Object.keys(portfolio.positions)
  useEffect(() => {
    let alive = true
    tickers.forEach((t) => {
      research(t).then((r) => { if (alive) setQuotes((q) => ({ ...q, [t]: r.quote })) }).catch(() => {})
    })
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tickers.join(',')])

  // --- Buy form: same name→symbol disambiguation pattern as Compare/search bar ---
  const [query, setQuery] = useState('')
  const [cands, setCands] = useState(null)
  const [busy, setBusy] = useState(false)
  const [picked, setPicked] = useState(null) // { symbol, name, price, currency }
  const [buyQty, setBuyQty] = useState('')
  const [buyReason, setBuyReason] = useState('')
  const [buyError, setBuyError] = useState(null)

  async function loadQuote(sym) {
    setBusy(true); setBuyError(null)
    try {
      const r = await research(sym)
      setPicked({ symbol: r.quote.symbol, name: r.quote.name, price: r.quote.price, currency: r.quote.currency })
    } catch (e) {
      setBuyError(e.message || 'Could not load a price for that ticker.')
    } finally {
      setBusy(false)
    }
  }

  async function resolveQuery() {
    const q = query.trim()
    if (!q) return
    setCands(null); setPicked(null); setBusy(true); setBuyError(null)
    try {
      const { candidates = [] } = await search(q)
      if (candidates.length === 0) { await loadQuote(q); return }
      if (candidates.length === 1 || candidates[0].symbol.toUpperCase() === q.toUpperCase()) {
        await loadQuote(candidates[0].symbol); return
      }
      setCands(candidates)
    } finally {
      setBusy(false)
    }
  }
  const pick = (c) => { setQuery(c.name || c.symbol); setCands(null); loadQuote(c.symbol) }

  function submitBuy() {
    if (!picked) return
    if (picked.currency !== 'USD') {
      setBuyError('Practice Lab tracks one simulated USD balance for now, so only USD-priced tickers can be logged here.')
      return
    }
    const r = buy({ ticker: picked.symbol, name: picked.name, qty: buyQty, price: picked.price, reason: buyReason })
    if (!r.ok) { setBuyError(r.error); return }
    setPortfolio(r.state); setQuery(''); setPicked(null); setBuyQty(''); setBuyReason(''); setBuyError(null)
  }

  // --- Inline sell form, one open at a time ---
  const [sellFor, setSellFor] = useState(null) // ticker
  const [sellQty, setSellQty] = useState('')
  const [sellReason, setSellReason] = useState('')
  const [sellError, setSellError] = useState(null)

  function openSell(t) { setSellFor(t); setSellQty(''); setSellReason(''); setSellError(null) }
  function submitSell(t) {
    const q = quotes[t]
    if (!q) { setSellError('Still loading a live price for this position — try again in a moment.'); return }
    const r = sell({ ticker: t, qty: sellQty, price: q.price, reason: sellReason })
    if (!r.ok) { setSellError(r.error); return }
    setPortfolio(r.state); setSellFor(null)
  }

  function doReset() {
    if (!window.confirm('Reset the practice lab? This clears all simulated positions and journal entries — it cannot be undone.')) return
    setPortfolio(resetPortfolio()); setQuotes({})
  }

  const positionsValue = tickers.reduce((sum, t) => sum + (portfolio.positions[t].qty * (quotes[t]?.price ?? portfolio.positions[t].avgCost)), 0)
  const totalValue = portfolio.cash + positionsValue
  const totalPnl = totalValue - STARTING_CASH

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <button className="logo logo-btn" onClick={onHome}><Logo /> Trade Craft</button>
          <div className="tabs">
            <button onClick={() => onNavigate('home')}>Research</button>
            <button onClick={() => onNavigate('compare')}>Comparison</button>
            <button onClick={() => onNavigate('watchlist')}>Watchlist</button>
            <button onClick={() => onNavigate('history')}>History</button>
            <button className="on" aria-current="page">Practice Lab</button>
          </div>
        </div>
        <button className="backbtn" onClick={() => onNavigate('home')}><PlusIcon className="icon" /> New research</button>
      </div>

      <div className="headline">
        <h1 style={{ fontSize: 30 }}>Practice Lab</h1>
        <span className="faint" style={{ fontSize: 13, alignSelf: 'center' }}>
          simulated trades only · no real money · a decision journal, not advice
        </span>
      </div>

      <div className="card">
        <div className="lbl">Your simulated portfolio (USD)</div>
        <div className="plab-summary">
          <div><div className="faint">Practice cash</div><div className="mono plab-stat">{money(portfolio.cash)}</div></div>
          <div><div className="faint">Positions value</div><div className="mono plab-stat">{money(positionsValue)}</div></div>
          <div><div className="faint">Total value</div><div className="mono plab-stat">{money(totalValue)}</div></div>
          <div><div className="faint">Total P&amp;L vs {money(STARTING_CASH)} start</div>
            <div className={'mono plab-stat ' + pnlClass(totalPnl)}>{money(totalPnl)}</div></div>
        </div>
        <button className="backbtn" style={{ marginTop: 14 }} onClick={doReset}>Reset practice lab</button>
      </div>

      <div className="card">
        <div className="lbl">Log a hypothetical buy</div>
        <div className="cmp-slot">
          <div className="cmp-pick">
            <input placeholder="Company or ticker (USD only)…" value={query}
                   onChange={(e) => setQuery(e.target.value)}
                   onKeyDown={(e) => { if (e.key === 'Enter') resolveQuery() }} />
            <button className="go" onClick={resolveQuery} disabled={busy}>{busy ? '…' : 'Find'}</button>
          </div>
          {cands && (
            <div className="cmp-cands">
              <div className="cmp-cands-hd">Did you mean… — pick one</div>
              {cands.map((c) => (
                <button key={c.symbol} className="cmp-cand" onClick={() => pick(c)}>
                  <span className="cmp-cand-sym mono">{c.symbol}</span>
                  <span className="cmp-cand-name">{c.name}</span>
                  <span className="faint" style={{ fontSize: 11 }}>{c.exchange}</span>
                </button>
              ))}
              <button className="cmp-cand-cancel" onClick={() => setCands(null)}>Cancel</button>
            </div>
          )}
        </div>

        {picked && (
          <div className="plab-trade">
            <div className="plab-trade-price">
              <span className="mono" style={{ fontWeight: 700 }}>{picked.symbol}</span> — {picked.name}
              {' '}at <span className="mono">{currencySymbol(picked.currency)}{picked.price}</span> (live price)
            </div>
            <div className="plab-trade-row">
              <input type="number" min="1" step="1" placeholder="Quantity" value={buyQty}
                     onChange={(e) => setBuyQty(e.target.value)} className="plab-qty" />
              <input placeholder="Why are you making this trade? (your reasoning, for later reflection)"
                     value={buyReason} onChange={(e) => setBuyReason(e.target.value)} className="plab-reason" />
              <button className="go" onClick={submitBuy}>Buy</button>
            </div>
          </div>
        )}
        {buyError && <div className="err" style={{ marginTop: 12 }}>{buyError}</div>}
      </div>

      <div className="card">
        <div className="lbl">Open positions</div>
        {tickers.length === 0 ? (
          <div className="placeholder">No simulated positions yet. Log a hypothetical buy above to start.</div>
        ) : (
          <div className="watch-list">
            {tickers.map((t) => {
              const p = portfolio.positions[t]
              const q = quotes[t]
              const value = p.qty * (q?.price ?? p.avgCost)
              const unrealized = q ? value - p.qty * p.avgCost : null
              const unrealizedPct = q ? (unrealized / (p.qty * p.avgCost)) * 100 : null
              return (
                <div key={t}>
                  <div className="watch-item">
                    <button className="watch-open" onClick={() => onOpen(t)}>
                      <span className="watch-tk mono">{t}</span>
                      <span className="watch-name">{p.name} · {p.qty} sh @ avg {money(p.avgCost)}</span>
                      <span className="watch-px mono">{q ? money(q.price) : '…'}</span>
                      <span className={pnlClass(unrealized)}>{unrealized == null ? '—' : `${money(unrealized)} (${pctStr(unrealizedPct)})`}</span>
                    </button>
                    <button className="watch-x" title="Sell" onClick={() => openSell(t)}>Sell</button>
                  </div>
                  {sellFor === t && (
                    <div className="plab-trade" style={{ marginTop: 8 }}>
                      <div className="plab-trade-row">
                        <input type="number" min="1" max={p.qty} step="1" placeholder={`Qty (max ${p.qty})`}
                               value={sellQty} onChange={(e) => setSellQty(e.target.value)} className="plab-qty" />
                        <input placeholder="Why are you closing this? (reasoning, for the journal)"
                               value={sellReason} onChange={(e) => setSellReason(e.target.value)} className="plab-reason" />
                        <button className="go" onClick={() => submitSell(t)}>Sell</button>
                        <button className="cmp-cand-cancel" onClick={() => setSellFor(null)}>Cancel</button>
                      </div>
                      {sellError && <div className="err" style={{ marginTop: 10 }}>{sellError}</div>}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      <div className="card">
        <div className="lbl">Trade journal — closed trades</div>
        {portfolio.closed.length === 0 ? (
          <div className="placeholder">Closed trades will show up here once you sell a practice position — entry reasoning, exit price, and the real realized result, for reflection.</div>
        ) : (
          <div className="hist-list">
            {portfolio.closed.map((c, i) => (
              <div key={i} className="hist-item" style={{ cursor: 'default' }}>
                <div className="hist-head">
                  <span className="hist-tk mono">{c.ticker}</span>
                  <span className="hist-name">{c.qty} sh · entry {money(c.entryPrice)} → exit {money(c.exitPrice)}</span>
                  <span className={pnlClass(c.realizedPnl) + ' faint'} style={{ marginLeft: 'auto' }}>
                    {money(c.realizedPnl)} ({pctStr(c.realizedPct)})
                  </span>
                </div>
                {c.reason && <div className="hist-sum">Reasoning: {c.reason}</div>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
