import { useEffect, useRef, useState } from 'react'
import { createChart } from 'lightweight-charts'
import Logo from './Logo.jsx'
import { compare as fetchCompare, search as searchSymbols } from '../api.js'

// Comparison — several companies on the same axes.
//
// Two things this screen must never do: put the companies in an order that
// implies a ranking, and let a rebased chart imply that the better-looking line
// is the better company. So the metric table is rendered in the order the user
// added them, no cell is highlighted as a "win", and the comparability warnings
// sit above the numbers rather than below.

const LINE_COLOURS = ['#34A9BE', '#00D68F', '#E8B14A', '#C88BE8']
const PERIODS = [['1mo', '1M'], ['6mo', '6M'], ['1y', '1Y'], ['5y', '5Y']]

function RebasedChart({ entries }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current || !entries?.length) return
    const chart = createChart(ref.current, {
      autoSize: true,
      layout: { background: { color: 'transparent' }, textColor: '#9FB4C4',
                fontFamily: 'Segoe UI, system-ui, sans-serif' },
      grid: { vertLines: { color: '#1c2f3f' }, horzLines: { color: '#1c2f3f' } },
      rightPriceScale: { borderColor: '#294056' },
      timeScale: { borderColor: '#294056' },
      crosshair: { mode: 0 },
    })
    entries.forEach((e, i) => {
      const s = chart.addLineSeries({
        color: LINE_COLOURS[i % LINE_COLOURS.length], lineWidth: 2, title: e.ticker,
      })
      s.setData(e.series)
    })
    // The 100 line is the only meaningful reference on a rebased chart.
    const base = chart.addLineSeries({ color: '#4a5f72', lineWidth: 1, lineStyle: 2,
                                       lastValueVisible: false, crosshairMarkerVisible: false })
    const times = entries[0].series.map((p) => p.time)
    base.setData(times.map((t) => ({ time: t, value: 100 })))

    chart.timeScale().fitContent()
    return () => chart.remove()
  }, [entries])

  return <div className="chartwrap" ref={ref} />
}

function Row({ label, render, entries, hint }) {
  return (
    <tr>
      <th scope="row" title={hint}>{label}</th>
      {entries.map((e) => <td key={e.ticker}>{render(e)}</td>)}
    </tr>
  )
}

function pct(v) {
  if (v == null) return '—'
  const cls = v > 0 ? 'up' : v < 0 ? 'down' : 'flat'
  return <span className={'chip ' + cls}>{v > 0 ? '+' : ''}{v}%</span>
}

export default function Compare({ onNavigate, onOpen, initial = [] }) {
  const [tickers, setTickers] = useState(initial)
  const [period, setPeriod] = useState('1y')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [q, setQ] = useState('')
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    if (tickers.length < 2) { setData(null); return }
    let alive = true
    setLoading(true)
    fetchCompare(tickers, period).then((r) => { if (alive) { setData(r); setLoading(false) } })
    return () => { alive = false }
  }, [tickers, period])

  async function add() {
    const term = q.trim()
    if (!term || tickers.length >= 4) return
    setAdding(true)
    const { candidates = [] } = await searchSymbols(term)
    const sym = candidates[0]?.symbol || term.toUpperCase()
    setTickers((t) => (t.includes(sym) ? t : [...t, sym]))
    setQ(''); setAdding(false)
  }

  const entries = data?.entries || []

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo"><Logo /> Trade101</div>
          <div className="tabs">
            <a onClick={() => onNavigate('home')} style={{ cursor: 'pointer' }}>Research</a>
            <a className="on">Comparison</a>
            <a onClick={() => onNavigate('watchlist')} style={{ cursor: 'pointer' }}>Watchlist</a>
            <a onClick={() => onNavigate('journal')} style={{ cursor: 'pointer' }}>Journal</a>
          </div>
        </div>
        <button className="backbtn" onClick={() => onNavigate('home')}>← New search</button>
      </div>

      <div className="headline"><h1>Comparison</h1></div>
      <p className="study-lead" style={{ maxWidth: 760 }}>
        Two to four companies on the same axes. This screen deliberately picks no winner:
        it shows how these businesses differ, and where comparing them directly is weak.
      </p>

      <div className="cmp-controls">
        <div className="cmp-chips">
          {tickers.map((t, i) => (
            <span key={t} className="cmp-chip"
                  style={{ borderColor: LINE_COLOURS[i % LINE_COLOURS.length] }}>
              <i style={{ background: LINE_COLOURS[i % LINE_COLOURS.length] }} />
              <button className="cmp-open" onClick={() => onOpen(t)}>{t}</button>
              <button className="cmp-x" aria-label={`Remove ${t}`}
                      onClick={() => setTickers((c) => c.filter((x) => x !== t))}>✕</button>
            </span>
          ))}
          {tickers.length < 4 && (
            <span className="strip-search" style={{ maxWidth: 260 }}>
              <span className="faint">🔍</span>
              <input placeholder="Add a company…" value={q} disabled={adding}
                     onChange={(e) => setQ(e.target.value)}
                     onKeyDown={(e) => { if (e.key === 'Enter') add() }} />
            </span>
          )}
        </div>
        <div className="chart-toggle">
          {PERIODS.map(([v, label]) => (
            <button key={v} className={period === v ? 'on' : ''} onClick={() => setPeriod(v)}>{label}</button>
          ))}
        </div>
      </div>

      {tickers.length < 2 && (
        <div className="placeholder">Add at least two companies to compare.</div>
      )}

      {loading && <div className="scraping"><div className="spinner" />
        <div className="faint">Loading both companies…</div></div>}

      {data?.failed?.length > 0 && (
        <div className="err" style={{ marginBottom: 14 }}>
          {data.failed.map((f) => (
            <div key={f.ticker}>⚠️ <b>{f.ticker}</b> — {f.reason}</div>
          ))}
        </div>
      )}

      {entries.length >= 2 && (
        <>
          {data.comparability.warnings.length > 0 && (
            <div className={'disagree ' + (data.comparability.level === 'weak' ? 'high' : 'low')}>
              <b>Read this comparison carefully</b>
              <ul style={{ margin: '6px 0 0', paddingLeft: 18, lineHeight: 1.6 }}>
                {data.comparability.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}

          <div className="card">
            <div className="lbl">Relative performance — each rebased to 100</div>
            <RebasedChart entries={entries} />
            <div className="note faint">{data.basis}</div>
          </div>

          <div className="card">
            <div className="lbl">Side by side</div>
            <div className="cmp-tablewrap">
              <table className="cmp-table">
                <thead>
                  <tr>
                    <th scope="col"></th>
                    {entries.map((e, i) => (
                      <th key={e.ticker} scope="col">
                        <i style={{ background: LINE_COLOURS[i % LINE_COLOURS.length] }} />
                        {e.ticker}
                        <span className="faint">{e.name}</span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <Row label="Change over window" entries={entries}
                       render={(e) => pct(e.performance.changePercent)} />
                  <Row label="Annualised volatility" entries={entries}
                       hint="Standard deviation of daily returns, annualised. A comparability measure, not a forecast."
                       render={(e) => <span className="mono">{e.performance.annualisedVolatilityPercent ?? '—'}%</span>} />
                  <Row label="Worst drawdown in window" entries={entries}
                       hint="Largest peak-to-trough fall inside this window."
                       render={(e) => <span className="mono">{e.performance.maxDrawdownPercent}%</span>} />
                  <Row label="RSI(14)" entries={entries}
                       render={(e) => <span className="mono">{e.indicators.rsi14 ?? '—'}</span>} />
                  <Row label="Above 200-day avg" entries={entries}
                       render={(e) => (e.indicators.above_sma200 ? 'yes' : 'no')} />
                  <Row label="Beta" entries={entries}
                       hint="How much the stock has moved versus the market."
                       render={(e) => <span className="mono">{e.profile.beta ?? '—'}</span>} />
                  <Row label="Sector" entries={entries} render={(e) => e.profile.sector || '—'} />
                  <Row label="Revenue change" entries={entries}
                       render={(e) => pct(e.fundamentals.revenueChangePercent)} />
                  <Row label="Net income change" entries={entries}
                       render={(e) => pct(e.fundamentals.netIncomeChangePercent)} />
                  <Row label="Trailing P/E" entries={entries}
                       render={(e) => <span className="mono">{e.fundamentals.valuation?.trailingPE ?? '—'}</span>} />
                  <Row label="Next earnings" entries={entries}
                       render={(e) => e.fundamentals.nextEarnings
                         ? new Date(e.fundamentals.nextEarnings).toLocaleDateString() : '—'} />
                  <Row label="Statement coverage" entries={entries}
                       render={(e) => e.fundamentals.coverage || '—'} />
                </tbody>
              </table>
            </div>
            <div className="notadvice" style={{ marginTop: 12 }}>{data.note}</div>
          </div>
        </>
      )}
    </div>
  )
}
