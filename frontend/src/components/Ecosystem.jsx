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

function betaNote(b) {
  if (b == null) return 'Beta unavailable for this stock.'
  const mag = b > 1.15 ? `more volatile than the market (~${Math.round((b - 1) * 100)}% bigger swings)`
    : b < 0.85 ? (b < 0 ? 'tends to move opposite the market' : 'calmer than the market')
    : 'moves roughly in line with the market'
  return `Beta ${b} — this stock is ${mag}. Beta measures how much a stock moves versus the overall market: 1 = in step, above 1 = amplified, below 1 = muted. It's how the index's moves tend to ripple into this name.`
}

// Radial node graph: the company at the centre, peers on a ring around it,
// each clickable to research. Richer than a flat chip list — shows the company
// sitting in a web of related names.
function EcoGraph({ ticker, peers, onSearch }) {
  const cx = 160, cy = 108, rx = 122, ry = 80
  const nodes = peers.slice(0, 8)
  const short = (s) => (s.length > 7 ? s.slice(0, 6) + '…' : s)
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
          <g key={p} className="eco-node" onClick={() => onSearch(p)}>
            <circle cx={x} cy={y} r="19" />
            <text x={x} y={y + 3.5} textAnchor="middle">{short(p)}</text>
          </g>
        )
      })}
      <g className="eco-center">
        <circle cx={cx} cy={cy} r="30" />
        <text x={cx} y={cy + 4} textAnchor="middle">{short(ticker)}</text>
      </g>
    </svg>
  )
}

export default function Ecosystem({ ticker, onSearch }) {
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
            <p style={{ margin: 0 }}>{betaNote(eco.beta)}</p>
            {eco.beta != null && eco.betaSource === 'computed' && (
              <p className="faint" style={{ margin: '6px 0 0', fontSize: 11.5 }}>
                Computed by Trade Craft from ~1y of daily returns vs the {eco.betaIndex || 'regional index'} (no provider beta for this listing).
              </p>
            )}
          </div>

          {eco.peers?.length > 0 ? (
            <div style={{ marginTop: 14 }}>
              <div className="faint" style={{ fontSize: 12, marginBottom: 2 }}>Peers / ecosystem — tap a node to research</div>
              <EcoGraph ticker={ticker} peers={eco.peers} onSearch={onSearch} />
            </div>
          ) : eco.coverage?.peers && (
            <div className="faint" style={{ fontSize: 12, marginTop: 14 }}>{eco.coverage.peers}</div>
          )}

          {eco.summary && <p className="placeholder" style={{ marginTop: 12 }}>{eco.summary}…</p>}
        </>
      )}

      {!loading && !eco && <div className="placeholder">Company profile unavailable for {ticker}.</div>}
    </div>
  )
}
