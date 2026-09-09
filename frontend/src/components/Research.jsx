import { useEffect, useRef, useState } from 'react'
import Logo from './Logo.jsx'
import PriceChart from './PriceChart.jsx'
import Metrics from './Metrics.jsx'
import AiRead from './AiRead.jsx'
import NewsPanel from './NewsPanel.jsx'
import { analyze, research } from '../api.js'

const REFRESH_MS = 7 * 60 * 1000 // auto-refresh the chart every 7 minutes

function changeChip(pct) {
  if (pct == null) return <span className="chip flat">—</span>
  const cls = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  const arrow = pct > 0 ? '▲' : pct < 0 ? '▼' : '■'
  return <span className={'chip ' + cls}>{arrow} {pct > 0 ? '+' : ''}{pct}%</span>
}

export default function Research({ data, onBack, onSearch }) {
  const [live, setLive] = useState(data)          // refreshable market bundle
  const [ai, setAi] = useState(null)
  const [aiLoading, setAiLoading] = useState(true)
  const [chartMode, setChartMode] = useState('candles') // 'candles' | 'line'
  const [lineData, setLineData] = useState(null)  // intraday ohlcv for line view
  const [updatedAt, setUpdatedAt] = useState(new Date())
  const [q, setQ] = useState('')

  const ticker = live.ticker

  // New stock selected → reset everything.
  useEffect(() => {
    setLive(data); setLineData(null); setChartMode('candles'); setUpdatedAt(new Date())
  }, [data])

  // AI narration (once per stock).
  useEffect(() => {
    let alive = true
    setAiLoading(true); setAi(null)
    analyze(data.ticker).then((r) => { if (alive) { setAi(r); setAiLoading(false) } })
    return () => { alive = false }
  }, [data.ticker])

  // Fetch intraday data when switching to the line view.
  // Yahoo has no "10d" period (it jumps 5d→1mo), so fetch 1mo of 30-min bars
  // and slice to the most recent ~10 sessions below.
  useEffect(() => {
    if (chartMode !== 'line' || lineData) return
    let alive = true
    research(ticker, { period: '1mo', interval: '30m' })
      .then((r) => { if (alive) setLineData(r) })
      .catch(() => {})
    return () => { alive = false }
  }, [chartMode, lineData, ticker])

  // Auto-refresh the active chart + indicators every REFRESH_MS.
  const modeRef = useRef(chartMode)
  modeRef.current = chartMode
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const fresh = await research(data.ticker)
        setLive(fresh); setUpdatedAt(new Date())
        if (modeRef.current === 'line') {
          const l = await research(data.ticker, { period: '1mo', interval: '30m' })
          setLineData(l)
        }
      } catch { /* keep last good data */ }
    }, REFRESH_MS)
    return () => clearInterval(id)
  }, [data.ticker])

  const { quote, indicators, ohlcv, meta } = live
  const sym = quote.currency === 'INR' ? '₹' : quote.currency === 'USD' ? '$' : ''
  const sources = ai?.available ? (ai.sources || []) : []
  const lean = ai?.available ? ai.momentum?.lean : null
  // Line view: last ~10 trading days of 30-min bars (≈13 bars/session).
  const chartOhlcv = chartMode === 'line' ? (lineData?.ohlcv || []).slice(-130) : ohlcv

  const submit = () => { const s = q.trim(); if (s) onSearch(s) }

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo"><Logo /> Trade101</div>
          <div className="tabs"><a className="on">Research</a><a>Comparison</a><a>History</a></div>
        </div>
        <button className="backbtn" onClick={onBack}>← New search</button>
      </div>

      {/* top strip: search + current stock status */}
      <div className="strip">
        <div className="strip-search">
          <span className="faint">🔍</span>
          <input placeholder="Search another company or ticker…" value={q}
                 onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') submit() }} />
        </div>
        <span className="strip-tk"><b>{ticker}</b> — {quote.name}</span>
        {lean && <span className={'chip ' + (lean === 'bullish' ? 'up' : lean === 'bearish' ? 'down' : 'flat')}>{lean === 'bullish' ? '▲' : lean === 'bearish' ? '▼' : '■'} {lean}</span>}
        <span className="strip-meta">{quote.exchange}</span>
        <span className="strip-meta faint">delayed ~15m</span>
      </div>

      <div className="headline">
        <h1>{ticker}</h1>
        <span className="px mono">{sym}{quote.price}</span>
        {changeChip(quote.changePercent)}
      </div>

      <div className="row cockpit">
        {/* LEFT: chart + metrics (flows tall to fill the column) */}
        <div className="row" style={{ gridTemplateColumns: '1fr', margin: 0 }}>
          <div className="card">
            <div className="charthead">
              <div className="chart-toggle">
                <button className={chartMode === 'candles' ? 'on' : ''} onClick={() => setChartMode('candles')}>Candles · 1Y</button>
                <button className={chartMode === 'line' ? 'on' : ''} onClick={() => setChartMode('line')}>Line · 10D intraday</button>
              </div>
              <button className="patbtn">🔍 Patterns<span className="phase">M4</span></button>
            </div>
            {chartMode === 'line' && !lineData
              ? <div className="chartwrap placeholder" style={{ display: 'grid', placeItems: 'center' }}>Loading intraday…</div>
              : <PriceChart ohlcv={chartOhlcv} type={chartMode === 'line' ? 'line' : 'candles'} />}
            <div className="note">
              {chartMode === 'candles' ? `${meta.bars} daily sessions` : '10 days · 15-min bars'} · updated {updatedAt.toLocaleTimeString()} · auto-refreshes every 7 min · {meta.note}
            </div>
          </div>
          <Metrics indicators={indicators} ticker={ticker} />
        </div>

        {/* RIGHT: AI read + news */}
        <div className="row" style={{ gridTemplateColumns: '1fr', margin: 0 }}>
          <AiRead ai={ai} loading={aiLoading} />
          <NewsPanel ai={ai} loading={aiLoading} ticker={ticker} />
        </div>
      </div>

      <div className="card">
        <div className="lbl">Ecosystem &amp; index<span className="phase">M4</span></div>
        <div className="placeholder">Supply-chain chain + the index {ticker} lives in (S&amp;P/NASDAQ) with beta — Milestone 4.</div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <div className="lbl">📎 References — every source used</div>
        <div className="refs">
          <a href="#">Yahoo Finance</a> — price &amp; indicators
          {sources.map((s, i) => (
            <span key={i}> · <a href={s.url} target="_blank" rel="noreferrer">{s.label}</a></span>
          ))}
        </div>
      </div>
    </div>
  )
}
