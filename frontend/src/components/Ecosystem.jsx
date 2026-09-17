import { useEffect, useState } from 'react'
import { ecosystem as fetchEco } from '../api.js'
import { currencySymbol } from '../lib/currency.js'

// marketCap arrives from the backend in the LISTING'S OWN currency (yfinance
// convention) — never assume USD. Formatting with the wrong symbol doesn't just
// mislabel the unit, it makes a false claim: without this, Nintendo's cap (in
// JPY) rendered as "$9.36T", larger than Apple's real $4.81T.
function marketCap(v, currency) {
  if (v == null) return '—'
  const sym = currencySymbol(currency)
  if (v >= 1e12) return sym + (v / 1e12).toFixed(2) + 'T'
  if (v >= 1e9) return sym + (v / 1e9).toFixed(1) + 'B'
  if (v >= 1e6) return sym + (v / 1e6).toFixed(0) + 'M'
  return sym + v
}

// Names the actual benchmark (e.g. "the S&P 500", "the Nikkei 225") instead of
// vaguely saying "the market" — the backend always supplies eco.betaIndex now,
// whether beta came from the provider or was computed in-house.
function betaNote(b, indexName) {
  if (b == null) return 'Beta unavailable for this stock.'
  const idx = indexName ? `the ${indexName}` : 'the broader market'
  const mag = b > 1.15 ? `more volatile than ${idx} (~${Math.round((b - 1) * 100)}% bigger swings)`
    : b < 0.85 ? (b < 0 ? `tends to move opposite ${idx}` : `calmer than ${idx}`)
    : `moves roughly in line with ${idx}`
  return `Beta ${b} — this stock is ${mag}. Beta measures how much a stock's price tends to move for a given move in ${idx}: 1 = in step, above 1 = amplified, below 1 = muted. It's how ${idx}'s swings tend to ripple into this name specifically — not the sector in general, though a stock's sector is usually a big part of why its beta looks the way it does.`
}

// Fundamentals formatting — values arrive exact from the backend (docs/AUDIT.md
// M5); this only formats, never computes. pctFrac takes a FRACTION (0.164 ->
// "16.4%"); pctRaw takes an already-percentage figure (yfinance's own
// convention for dividendYield/debtToEquity — see services/company.py).
const pctFrac = (v) => (v == null ? '—' : (v * 100).toFixed(1) + '%')
const pctRaw = (v) => (v == null ? '—' : v.toFixed(2) + '%')
const num = (v, digits = 2) => (v == null ? '—' : v.toFixed(digits))

// Radial node graph: the company at the centre, peers on a ring around it,
// each clickable to research. Richer than a flat chip list — shows the company
// sitting in a web of related names.
//
// Bug (user-reported 2026-09-17): the always-visible label was the bare
// ticker, with the resolved company name shown only on hover. Fine for a US
// stock (AAPL, MSFT read fine on their own) but useless for most non-US
// listings, whose tickers are opaque numeric codes (Samsung is "005930",
// not a name a human recognizes at a glance) — the resolved name sat unused
// in a tooltip while the graph showed nothing but numbers. Now the label
// prefers the resolved name (peerNames for peers, `centerName` for the
// searched stock itself) and falls back to the ticker only when no name was
// resolved; the tooltip flips to show BOTH ("TICKER — Full Name") so the
// ticker is still one hover away for confirmation.
function EcoGraph({ ticker, centerName, peers, peerNames, onSearch }) {
  const cx = 160, cy = 108, rx = 122, ry = 80
  const nodes = peers.slice(0, 8)
  const short = (s) => (s.length > 9 ? s.slice(0, 8) + '…' : s)
  // Prefer the resolved name's first word/two (reads better truncated than a
  // full "Samsung Electronics Co., Ltd." would) — fall back to the ticker.
  const labelFor = (p) => {
    const name = peerNames?.[p]
    if (!name) return p
    const words = name.replace(/,.*$/, '').split(' ')
    return words.length > 1 && (words[0] + ' ' + words[1]).length <= 9
      ? words[0] + ' ' + words[1] : words[0]
  }
  const titleFor = (p) => peerNames?.[p] ? `${p} — ${peerNames[p]}` : p
  const go = (p) => onSearch(p)
  return (
    <svg className="ecograph" viewBox="0 0 320 216" role="img" aria-label={`${ticker} peer graph`}>
      {nodes.map((p, i) => {
        const a = (-90 + i * (360 / nodes.length)) * Math.PI / 180
        const x = cx + rx * Math.cos(a), y = cy + ry * Math.sin(a)
        return <line key={'e' + i} x1={cx} y1={cy} x2={x} y2={y} stroke="#1d4551" strokeWidth="1.5" />
      })}
      {nodes.map((p, i) => {
        const a = (-90 + i * (360 / nodes.length)) * Math.PI / 180
        const x = cx + rx * Math.cos(a), y = cy + ry * Math.sin(a)
        return (
          <g key={p} className="eco-node" onClick={() => go(p)}
             role="button" tabIndex={0} aria-label={`Research ${peerNames?.[p] || p}`}
             onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(p) } }}>
            <title>{titleFor(p)}</title>
            <circle cx={x} cy={y} r="19" />
            <text x={x} y={y + 3.5} textAnchor="middle">{short(labelFor(p))}</text>
          </g>
        )
      })}
      <g className="eco-center">
        <circle cx={cx} cy={cy} r="30" />
        <title>{centerName ? `${ticker} — ${centerName}` : ticker}</title>
        <text x={cx} y={cy + 4} textAnchor="middle">{short(centerName ? centerName.replace(/,.*$/, '').split(' ')[0] : ticker)}</text>
      </g>
    </svg>
  )
}

export default function Ecosystem({ ticker, name, onSearch }) {
  const [eco, setEco] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    setLoading(true); setEco(null)
    fetchEco(ticker).then((r) => { if (alive) { setEco(r); setLoading(false) } })
    return () => { alive = false }
  }, [ticker])

  return (
    <div className="card">
      <div className="lbl">Ecosystem &amp; how it sits in the market</div>

      {loading && <div className="scraping"><div className="spinner" /><div className="faint" style={{ fontSize: 13 }}>Loading company profile…</div></div>}

      {!loading && eco && (
        <>
          <div className="eco-facts">
            {eco.sector && <div><span className="faint">Sector</span><b>{eco.sector}</b></div>}
            {eco.industry && <div><span className="faint">Industry</span><b>{eco.industry}</b></div>}
            <div><span className="faint">Market cap</span><b className="mono">{marketCap(eco.marketCap, eco.marketCapCurrency)}</b></div>
            <div><span className="faint">Listing</span><b>{eco.exchange}{eco.country ? ` · ${eco.country}` : ''}</b></div>
          </div>

          <div className="lesson" style={{ marginTop: 12 }}>
            <h4>Beta {eco.beta ?? '—'} — market sensitivity</h4>
            <p style={{ margin: 0 }}>{betaNote(eco.beta, eco.betaIndex)}</p>
            {eco.beta != null && eco.betaSource === 'computed' && (
              <p className="faint" style={{ margin: '6px 0 0', fontSize: 11.5 }}>
                Computed by Trade Craft from ~1y of daily returns vs the {eco.betaIndex || 'regional index'} (no provider beta for this listing).
              </p>
            )}
          </div>

          {eco.peers?.length > 0 ? (
            <div style={{ marginTop: 14 }}>
              <div className="faint" style={{ fontSize: 12, marginBottom: 2 }}>
                {eco.peersSource === 'yahoo'
                  ? 'Related companies (commonly viewed together by other investors) — tap a node to research'
                  : 'Peers / ecosystem — tap a node to research'}
              </div>
              <EcoGraph ticker={ticker} centerName={name} peers={eco.peers} peerNames={eco.peerNames} onSearch={onSearch} />
              {eco.peersSource === 'yahoo' && (
                <div className="faint" style={{ fontSize: 11, marginTop: 4 }}>
                  Same-industry peer data isn't available for this listing, so these are shown
                  instead — not necessarily direct competitors.
                </div>
              )}
            </div>
          ) : eco.coverage?.peers && (
            <div className="faint" style={{ fontSize: 12, marginTop: 14 }}>{eco.coverage.peers}</div>
          )}

          {/* eco.summary already ends cleanly (a full sentence, or "…" appended
              by the backend only when genuinely cut at a word boundary) —
              appending another "…" here used to truncate mid-word regardless. */}
          {eco.summary && <p className="placeholder" style={{ marginTop: 12 }}>{eco.summary}</p>}

          {eco.fundamentals && (eco.coverage?.fundamentals ? (
            <div className="faint" style={{ fontSize: 12, marginTop: 14 }}>{eco.coverage.fundamentals}</div>
          ) : (
            <div style={{ marginTop: 14 }}>
              <div className="lbl" style={{ marginBottom: 8 }}>Fundamentals</div>
              <div className="eco-facts">
                <div><span className="faint">P/E (trailing)</span><b className="mono">{num(eco.fundamentals.pe)}</b></div>
                <div><span className="faint">P/E (forward)</span><b className="mono">{num(eco.fundamentals.forwardPe)}</b></div>
                <div><span className="faint">EPS</span><b className="mono">{num(eco.fundamentals.eps)}</b></div>
                <div><span className="faint">Revenue growth</span><b className="mono">{pctFrac(eco.fundamentals.revenueGrowth)}</b></div>
                <div><span className="faint">Profit margin</span><b className="mono">{pctFrac(eco.fundamentals.profitMargin)}</b></div>
                <div><span className="faint">Dividend yield</span><b className="mono">{pctRaw(eco.fundamentals.dividendYield)}</b></div>
                <div><span className="faint">Debt/Equity</span><b className="mono">{pctRaw(eco.fundamentals.debtToEquity)}</b></div>
                <div><span className="faint">Next earnings</span><b className="mono">{eco.fundamentals.nextEarningsDate || '—'}</b></div>
              </div>
            </div>
          ))}
        </>
      )}

      {!loading && !eco && <div className="placeholder">Company profile unavailable for {ticker}.</div>}
    </div>
  )
}
