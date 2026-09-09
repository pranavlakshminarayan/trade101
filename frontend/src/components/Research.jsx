import { useEffect, useRef, useState } from 'react'
import Logo from './Logo.jsx'
import PriceChart from './PriceChart.jsx'
import Metrics from './Metrics.jsx'
import AiRead from './AiRead.jsx'
import NewsPanel from './NewsPanel.jsx'
import { analyze, research, patterns as fetchPatterns } from '../api.js'

const REFRESH_MS = 7 * 60 * 1000 // auto-refresh every 7 minutes

// Timeframe presets → Yahoo period/interval (+ optional slice to trim bars).
const TF = {
  '1Y':  { period: '1y',  interval: '1d' },
  '1M':  { period: '1mo', interval: '1d' },
  '10D': { period: '1mo', interval: '30m', slice: 130 }, // Yahoo has no 10d; slice ~10 sessions
  '5D':  { period: '5d',  interval: '15m' },
  '1D':  { period: '1d',  interval: '5m' },  // 24h / intraday
}
const TF_ORDER = ['1Y', '1M', '10D', '5D', '1D']

function changeChip(pct) {
  if (pct == null) return <span className="chip flat">—</span>
  const cls = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  const arrow = pct > 0 ? '▲' : pct < 0 ? '▼' : '■'
  return <span className={'chip ' + cls}>{arrow} {pct > 0 ? '+' : ''}{pct}%</span>
}

export default function Research({ data, onBack, onSearch }) {
  const [live, setLive] = useState(data)           // main 1Y bundle: quote, indicators, 1Y chart
  const [ai, setAi] = useState(null)
  const [aiLoading, setAiLoading] = useState(true)
  const [chartType, setChartType] = useState('candles') // 'candles' | 'line'
  const [timeframe, setTimeframe] = useState('1Y')
  const [tfData, setTfData] = useState({})         // { [tf]: ohlcv } cache (1Y comes from `live`)
  const [tfLoading, setTfLoading] = useState(false)
  const [showPatterns, setShowPatterns] = useState(false)
  const [patData, setPatData] = useState({}) // { [tf]: patterns[] }
  const [updatedAt, setUpdatedAt] = useState(new Date())
  const [q, setQ] = useState('')

  const ticker = live.ticker

  // New stock → reset.
  useEffect(() => {
    setLive(data); setTfData({}); setPatData({}); setShowPatterns(false)
    setChartType('candles'); setTimeframe('1Y'); setUpdatedAt(new Date())
  }, [data])

  // Detect patterns for the current timeframe when the overlay is on.
  useEffect(() => {
    if (!showPatterns || patData[timeframe]) return
    let alive = true
    fetchPatterns(ticker, TF[timeframe]).then((r) => {
      if (alive) setPatData((c) => ({ ...c, [timeframe]: r.patterns || [] }))
    })
    return () => { alive = false }
  }, [showPatterns, timeframe, ticker, patData])

  // AI narration (once per stock).
  useEffect(() => {
    let alive = true
    setAiLoading(true); setAi(null)
    analyze(data.ticker).then((r) => { if (alive) { setAi(r); setAiLoading(false) } })
    return () => { alive = false }
  }, [data.ticker])

  // Ensure data for the selected timeframe (1Y comes from `live`).
  useEffect(() => {
    if (timeframe === '1Y' || tfData[timeframe]) return
    let alive = true
    setTfLoading(true)
    research(ticker, TF[timeframe])
      .then((r) => { if (alive) setTfData((c) => ({ ...c, [timeframe]: r.ohlcv })) })
      .catch(() => {})
      .finally(() => { if (alive) setTfLoading(false) })
    return () => { alive = false }
  }, [timeframe, ticker, tfData])

  // Auto-refresh the live bundle (+ active timeframe) every REFRESH_MS.
  const tfRef = useRef(timeframe); tfRef.current = timeframe
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const fresh = await research(data.ticker)
        setLive(fresh); setUpdatedAt(new Date())
        const tf = tfRef.current
        if (tf !== '1Y') {
          const r = await research(data.ticker, TF[tf])
          setTfData((c) => ({ ...c, [tf]: r.ohlcv }))
        }
      } catch { /* keep last good */ }
    }, REFRESH_MS)
    return () => clearInterval(id)
  }, [data.ticker])

  const { quote, indicators, ohlcv, meta } = live
  const sym = quote.currency === 'INR' ? '₹' : quote.currency === 'USD' ? '$' : ''
  const sources = ai?.available ? (ai.sources || []) : []
  const lean = ai?.available ? ai.momentum?.lean : null

  const rawTf = timeframe === '1Y' ? ohlcv : (tfData[timeframe] || [])
  const slice = TF[timeframe].slice
  const chartOhlcv = slice ? rawTf.slice(-slice) : rawTf
  const chartLoading = timeframe !== '1Y' && !tfData[timeframe] && tfLoading

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
        {/* LEFT: chart → metrics → news (fills the column) */}
        <div className="row" style={{ gridTemplateColumns: '1fr', margin: 0 }}>
          <div className="card">
            <div className="charthead">
              <div className="chart-toggle">
                <button className={chartType === 'candles' ? 'on' : ''} onClick={() => setChartType('candles')}>Candles</button>
                <button className={chartType === 'line' ? 'on' : ''} onClick={() => setChartType('line')}>Line</button>
              </div>
              <div className="chart-toggle">
                {TF_ORDER.map((t) => (
                  <button key={t} className={timeframe === t ? 'on' : ''} onClick={() => setTimeframe(t)}>{t}</button>
                ))}
              </div>
              <button className={'patbtn' + (showPatterns ? ' on' : '')} onClick={() => setShowPatterns((s) => !s)}>
                🔍 Patterns{showPatterns ? ' ✓' : ''}
              </button>
            </div>
            {chartLoading || !chartOhlcv.length
              ? <div className="chartwrap placeholder" style={{ display: 'grid', placeItems: 'center' }}>Loading {timeframe}…</div>
              : <PriceChart ohlcv={chartOhlcv} type={chartType} patterns={patData[timeframe] || []} showPatterns={showPatterns} />}
            <div className="note">
              {timeframe} · {TF[timeframe].interval} bars · updated {updatedAt.toLocaleTimeString()} · auto-refreshes every 7 min · {meta.note}
            </div>
            {showPatterns && (
              <div className="patterns-panel">
                {(patData[timeframe] || []).length ? (patData[timeframe]).map((p, i) => (
                  <div className="pat" key={i}>
                    <div>
                      <span className={'chip ' + (p.direction === 'bullish' ? 'up' : 'down')}>{p.name}</span>
                      <span className="faint" style={{ marginLeft: 8, fontSize: 12 }}>{p.direction} · confidence {p.confidence}</span>
                    </div>
                    <p>{p.explanation}</p>
                  </div>
                )) : (
                  <div className="placeholder">No clear pattern on the {timeframe} chart — try another timeframe. (Detection is a heuristic learning aid, not a signal.)</div>
                )}
              </div>
            )}
          </div>

          <Metrics indicators={indicators} ticker={ticker} />

          <NewsPanel ai={ai} loading={aiLoading} ticker={ticker} />

          <div className="card">
            <div className="lbl">Ecosystem &amp; index<span className="phase">M4</span></div>
            <div className="placeholder">Supply-chain chain + the index {ticker} lives in (S&amp;P/NASDAQ) with beta — Milestone 4.</div>
          </div>

          <div className="card">
            <div className="lbl">📎 References — every source used</div>
            <div className="reflist">
              <div><a href="#">Yahoo Finance</a> <span className="faint">— price &amp; indicators</span></div>
              {sources.map((s, i) => (
                <div key={i}>
                  <a href={s.url} target="_blank" rel="noreferrer" title={s.url}>{s.label}</a>
                  {s.source ? <span className="faint"> — {s.source}</span> : null}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT: AI read (tall) */}
        <AiRead ai={ai} loading={aiLoading} />
      </div>
    </div>
  )
}
