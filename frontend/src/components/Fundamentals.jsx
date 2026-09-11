import { useEffect, useState } from 'react'
import { fundamentals as fetchFundamentals } from '../api.js'

// The business behind the ticker: earnings, revenue, margins, cash flow,
// valuation. Every figure is optional — Yahoo's fundamentals coverage is strong
// for US large caps and patchy elsewhere — so a missing value is shown as
// missing rather than quietly omitted, which would imply the company has none.

function money(v, currency) {
  if (v == null) return '—'
  const sign = v < 0 ? '-' : ''
  const a = Math.abs(v)
  const unit = a >= 1e12 ? [1e12, 'T'] : a >= 1e9 ? [1e9, 'B'] : a >= 1e6 ? [1e6, 'M'] : [1, '']
  return `${sign}${(a / unit[0]).toFixed(unit[0] === 1 ? 0 : 2)}${unit[1]}${currency ? ' ' + currency : ''}`
}

function Delta({ pct }) {
  if (pct == null) return null
  const cls = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  return <span className={'chip ' + cls}>{pct > 0 ? '+' : ''}{pct}%</span>
}

// A tiny inline bar series — enough to see a direction without pretending to be
// a chart with an axis.
function Spark({ series }) {
  if (!series?.length) return null
  const vals = series.map((d) => d.value)
  const max = Math.max(...vals.map(Math.abs)) || 1
  return (
    <div className="spark" role="img" aria-label={`${series.length} periods`}>
      {series.map((d, i) => (
        <div key={i} className="spark-bar" title={`${d.period}: ${d.value}`}
             style={{ height: `${Math.max(4, (Math.abs(d.value) / max) * 100)}%`,
                      background: d.value < 0 ? 'var(--down, #F0616D)' : 'var(--teal, #34A9BE)' }} />
      ))}
    </div>
  )
}

function Line({ label, block, currency, children }) {
  const has = block?.series?.length
  return (
    <div className="fund-row">
      <div className="fund-k">
        {label}
        {has ? <Delta pct={block.changePercent} /> : null}
      </div>
      {has ? (
        <div className="fund-v">
          <span className="mono">{money(block.series[block.series.length - 1].value, currency)}</span>
          <Spark series={block.series} />
        </div>
      ) : (
        <div className="fund-v faint">not reported for this company</div>
      )}
      {children}
    </div>
  )
}

export default function Fundamentals({ ticker, filings }) {
  const [f, setF] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    setLoading(true); setF(null)
    fetchFundamentals(ticker).then((r) => { if (alive) { setF(r); setLoading(false) } })
    return () => { alive = false }
  }, [ticker])

  if (loading) {
    return (
      <div className="card">
        <div className="lbl">Fundamentals — the business behind the ticker</div>
        <div className="scraping"><div className="spinner" />
          <div className="faint" style={{ fontSize: 13 }}>Loading financial statements…</div>
        </div>
      </div>
    )
  }

  if (!f) {
    return (
      <div className="card">
        <div className="lbl">Fundamentals</div>
        <div className="placeholder">
          Fundamentals unavailable — the statements source did not respond. The chart,
          metrics and patterns are unaffected; retrying later may work.
        </div>
      </div>
    )
  }

  const e = f.earnings || {}
  const v = f.valuation || {}
  const cur = f.currency

  return (
    <div className="card">
      <div className="lbl">Fundamentals — the business behind the ticker</div>

      {f.coverage?.level === 'none' ? (
        <div className="coverage cov-none">
          <div className="cov-head"><span className="cov-icon">○</span><b>No statements available</b></div>
          <p className="cov-note">
            {f.meta?.notes?.[0] ||
              'This provider returned no financial statements for this symbol.'} The price
            chart is unaffected, but nothing on this panel can be filled in — treat the
            company's finances as unknown here rather than assuming they are unremarkable.
          </p>
        </div>
      ) : (
        <>
          {/* Earnings — the scheduled event most likely to move the price */}
          <div className="fund-earn">
            <div>
              <span className="faint">Next earnings</span>
              <b>{e.nextDate ? new Date(e.nextDate).toLocaleDateString() : '—'}</b>
            </div>
            <div>
              <span className="faint">Last reported</span>
              <b>{e.lastDate ? new Date(e.lastDate).toLocaleDateString() : '—'}</b>
            </div>
            <div>
              <span className="faint">EPS vs estimate</span>
              <b className="mono">
                {e.epsActual != null ? e.epsActual : '—'}
                {e.epsEstimate != null ? ` vs ${e.epsEstimate}` : ''}
              </b>
              {e.surprisePercent != null && <Delta pct={e.surprisePercent} />}
            </div>
          </div>
          {e.note && <div className="faint" style={{ fontSize: 11.5 }}>{e.note}</div>}

          <Line label="Revenue" block={f.revenue} currency={cur} />
          <Line label="Net income" block={f.netIncome} currency={cur} />
          <Line label="Free cash flow" block={f.cashFlow} currency={cur} />

          {f.margins?.net?.length > 0 && (
            <div className="fund-row">
              <div className="fund-k">Net margin</div>
              <div className="fund-v">
                <span className="mono">{f.margins.net[f.margins.net.length - 1].value}%</span>
                <Spark series={f.margins.net} />
              </div>
            </div>
          )}

          <div className="lesson" style={{ marginTop: 12 }}>
            <h4>Reading these together</h4>
            <p style={{ margin: 0 }}>{f.margins?.note} {f.cashFlow?.note}</p>
          </div>

          <div className="fund-val">
            {[['P/E (trailing)', v.trailingPE], ['P/E (forward)', v.forwardPE],
              ['P/B', v.priceToBook], ['P/S', v.priceToSales],
              ['EV/EBITDA', v.enterpriseToEbitda]].map(([k, val]) => (
              <div key={k}><span className="faint">{k}</span><b className="mono">{val ?? '—'}</b></div>
            ))}
          </div>
          <p className="faint" style={{ fontSize: 11.5, lineHeight: 1.55 }}>{v.note}</p>
        </>
      )}

      {filings?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div className="faint" style={{ fontSize: 12, marginBottom: 6 }}>
            Read it at the source — primary filings
          </div>
          <div className="reflist">
            {filings.slice(0, 5).map((fl, i) => (
              <div key={i}>
                <a href={fl.url} target="_blank" rel="noreferrer">SEC {fl.form} — {fl.date}</a>
              </div>
            ))}
          </div>
        </div>
      )}

      {f.meta?.note && <div className="note faint" style={{ marginTop: 10 }}>{f.meta.note}</div>}
    </div>
  )
}
