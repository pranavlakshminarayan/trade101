import { useEffect, useState } from 'react'
import { ecosystem as fetchEco } from '../api.js'

function marketCap(v) {
  if (v == null) return '—'
  if (v >= 1e12) return '$' + (v / 1e12).toFixed(2) + 'T'
  if (v >= 1e9) return '$' + (v / 1e9).toFixed(1) + 'B'
  if (v >= 1e6) return '$' + (v / 1e6).toFixed(0) + 'M'
  return '$' + v
}

function betaNote(b) {
  if (b == null) return 'Beta unavailable for this stock.'
  const mag = b > 1.15 ? `more volatile than the market (~${Math.round((b - 1) * 100)}% bigger swings)`
    : b < 0.85 ? (b < 0 ? 'tends to move opposite the market' : 'calmer than the market')
    : 'moves roughly in line with the market'
  return `Beta ${b} — this stock is ${mag}. Beta measures how much a stock moves versus the overall market: 1 = in step, above 1 = amplified, below 1 = muted. It's how the index's moves tend to ripple into this name.`
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
            <div><span className="faint">Market cap</span><b className="mono">{marketCap(eco.marketCap)}</b></div>
            <div><span className="faint">Listing</span><b>{eco.exchange}{eco.country ? ` · ${eco.country}` : ''}</b></div>
          </div>

          <div className="lesson" style={{ marginTop: 12 }}>
            <h4>Beta {eco.beta ?? '—'} — market sensitivity</h4>
            <p style={{ margin: 0 }}>{betaNote(eco.beta)}</p>
          </div>

          {eco.peers?.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <div className="faint" style={{ fontSize: 12, marginBottom: 6 }}>Peers / ecosystem — tap to research</div>
              <div className="eco-peers">
                {eco.peers.map((p) => (
                  <button key={p} className="chipx" onClick={() => onSearch(p)}>{p}</button>
                ))}
              </div>
            </div>
          )}

          {eco.summary && <p className="placeholder" style={{ marginTop: 12 }}>{eco.summary}…</p>}
        </>
      )}

      {!loading && !eco && <div className="placeholder">Company profile unavailable for {ticker}.</div>}
    </div>
  )
}
