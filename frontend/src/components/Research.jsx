import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import Logo from './Logo.jsx'
import PriceChart from './PriceChart.jsx'
import Metrics from './Metrics.jsx'
import AiRead from './AiRead.jsx'
import NewsPanel from './NewsPanel.jsx'
import Ecosystem from './Ecosystem.jsx'
import AskClaude from './AskClaude.jsx'
import { analyze, research, patterns as fetchPatterns } from '../api.js'
import { addHistory } from '../lib/history.js'
import { isWatched, toggleWatch } from '../lib/watchlist.js'

const REFRESH_MS = 7 * 60 * 1000

const TF = {
  '1Y':  { period: '1y',  interval: '1d' },
  '1M':  { period: '1mo', interval: '1d' },
  '10D': { period: '1mo', interval: '30m', slice: 130 },
  '5D':  { period: '5d',  interval: '15m' },
  '1D':  { period: '1d',  interval: '5m' },
}
const TF_ORDER = ['1Y', '1M', '10D', '5D', '1D']
const FLOW = ['metrics', 'news', 'ecosystem', 'references'] // blocks the masonry distributes

function changeChip(pct) {
  if (pct == null) return <span className="chip flat">—</span>
  const cls = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  const arrow = pct > 0 ? '▲' : pct < 0 ? '▼' : '■'
  return <span className={'chip ' + cls}>{arrow} {pct > 0 ? '+' : ''}{pct}%</span>
}

export default function Research({ data, onBack, onSearch, onNavigate }) {
  const [live, setLive] = useState(data)
  const [ai, setAi] = useState(null)
  const [aiLoading, setAiLoading] = useState(true)
  const [chartType, setChartType] = useState('candles')
  const [timeframe, setTimeframe] = useState('1Y')
  const [tfData, setTfData] = useState({})
  const [tfLoading, setTfLoading] = useState(false)
  const [showPatterns, setShowPatterns] = useState(false)
  const [patData, setPatData] = useState({})
  const [patSel, setPatSel] = useState(0)
  const [updatedAt, setUpdatedAt] = useState(new Date())
  const [q, setQ] = useState('')
  const [assign, setAssign] = useState({ metrics: 'L', news: 'L', ecosystem: 'R', references: 'R' })
  const [tick, setTick] = useState(0)
  const [watched, setWatched] = useState(false)

  const ticker = live.ticker
  const refs = useRef({})
  const setRef = (id) => (el) => { refs.current[id] = el }

  useEffect(() => {
    setLive(data); setTfData({}); setPatData({}); setShowPatterns(false); setPatSel(0)
    setChartType('candles'); setTimeframe('1Y'); setUpdatedAt(new Date())
  }, [data])

  useEffect(() => {
    let alive = true
    setAiLoading(true); setAi(null)
    analyze(data.ticker).then((r) => { if (alive) { setAi(r); setAiLoading(false) } })
    return () => { alive = false }
  }, [data.ticker])

  useEffect(() => { setPatSel(0) }, [timeframe])
  useEffect(() => { setWatched(isWatched(live.ticker)) }, [live.ticker])
  const onWatch = () => { toggleWatch({ ticker: live.ticker, name: live.quote?.name }); setWatched(isWatched(live.ticker)) }

  // Save each analysed stock to history (with its 2-line AI takeaway).
  useEffect(() => {
    if (ai?.available && ai.momentum?.summary) {
      addHistory({ ticker: live.ticker, name: live.quote?.name, lean: ai.momentum.lean, summary: ai.momentum.summary })
    }
  }, [ai])

  useEffect(() => {
    if (timeframe === '1Y' || tfData[timeframe]) return
    let alive = true
    setTfLoading(true)
    research(ticker, TF[timeframe])
      .then((r) => { if (alive) setTfData((c) => ({ ...c, [timeframe]: r.ohlcv })) })
      .catch(() => {}).finally(() => { if (alive) setTfLoading(false) })
    return () => { alive = false }
  }, [timeframe, ticker, tfData])

  useEffect(() => {
    if (!showPatterns || patData[timeframe]) return
    let alive = true
    fetchPatterns(ticker, TF[timeframe]).then((r) => {
      if (alive) setPatData((c) => ({ ...c, [timeframe]: r.patterns || [] }))
    })
    return () => { alive = false }
  }, [showPatterns, timeframe, ticker, patData])

  const tfRef = useRef(timeframe); tfRef.current = timeframe
  useEffect(() => {
    const id = setInterval(async () => {
      try {
        const fresh = await research(data.ticker, { fresh: true })
        setLive(fresh); setUpdatedAt(new Date())
        const tf = tfRef.current
        if (tf !== '1Y') { const r = await research(data.ticker, { ...TF[tf], fresh: true }); setTfData((c) => ({ ...c, [tf]: r.ohlcv })) }
      } catch { /* keep last good */ }
    }, REFRESH_MS)
    return () => clearInterval(id)
  }, [data.ticker])

  // Masonry: measure each block and send each flow-block to the shorter column.
  useLayoutEffect(() => {
    const h = (id) => refs.current[id]?.offsetHeight || 0
    let L = h('chart'), R = h('ai')
    const next = {}
    for (const id of FLOW) {
      if (L <= R) { next[id] = 'L'; L += h(id) } else { next[id] = 'R'; R += h(id) }
    }
    if (FLOW.some((id) => next[id] !== assign[id])) setAssign(next)
  })
  useEffect(() => {
    const onResize = () => setTick((t) => t + 1)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const { quote, indicators, ohlcv, meta } = live
  const sym = quote.currency === 'INR' ? '₹' : quote.currency === 'USD' ? '$' : ''
  const sources = ai?.available ? (ai.sources || []) : []
  const lean = ai?.available ? ai.momentum?.lean : null

  const rawTf = timeframe === '1Y' ? ohlcv : (tfData[timeframe] || [])
  const sl = TF[timeframe].slice
  const chartOhlcv = sl ? rawTf.slice(-sl) : rawTf
  const chartLoading = timeframe !== '1Y' && !tfData[timeframe] && tfLoading

  const pats = patData[timeframe] || []
  const selPat = pats[patSel] || null

  const submit = () => { const s = q.trim(); if (s) onSearch(s) }

  // block elements the masonry places
  const blocks = {
    metrics: <Metrics indicators={indicators} ticker={ticker} />,
    news: <NewsPanel ai={ai} loading={aiLoading} ticker={ticker} />,
    ecosystem: <Ecosystem ticker={ticker} onSearch={onSearch} />,
    references: (
      <div className="card">
        <div className="lbl">📎 References — every source used</div>
        <div className="reflist">
          <div><a href="#">Yahoo Finance</a> <span className="faint">— price &amp; indicators</span></div>
          {sources.map((s, i) => (
            <div key={i}><a href={s.url} target="_blank" rel="noreferrer" title={s.url}>{s.label}</a>{s.source ? <span className="faint"> — {s.source}</span> : null}</div>
          ))}
        </div>
      </div>
    ),
  }
  const chartBlock = (
    <div className="card">
      <div className="charthead">
        <div className="chart-toggle">
          <button className={chartType === 'candles' ? 'on' : ''} onClick={() => setChartType('candles')}>Candles</button>
          <button className={chartType === 'line' ? 'on' : ''} onClick={() => setChartType('line')}>Line</button>
        </div>
        <div className="chart-toggle">
          {TF_ORDER.map((t) => <button key={t} className={timeframe === t ? 'on' : ''} onClick={() => setTimeframe(t)}>{t}</button>)}
        </div>
        <button className={'patbtn' + (showPatterns ? ' on' : '')} onClick={() => setShowPatterns((s) => !s)}>🔍 Patterns{showPatterns ? ' ✓' : ''}</button>
      </div>
      {chartLoading || !chartOhlcv.length
        ? <div className="chartwrap placeholder" style={{ display: 'grid', placeItems: 'center' }}>Loading {timeframe}…</div>
        : <PriceChart ohlcv={chartOhlcv} type={chartType} patterns={showPatterns && selPat ? [selPat] : []} showPatterns={showPatterns} />}
      <div className="note">{timeframe} · {TF[timeframe].interval} bars · updated {updatedAt.toLocaleTimeString()} · auto-refreshes every 7 min · {meta.note}</div>
      {showPatterns && (
        <div className="patterns-panel">
          {pats.length ? (
            <>
              <div className="pat-select">
                {pats.map((p, i) => (
                  <button key={i} className={'pat-tab' + (i === patSel ? ' on' : '')} onClick={() => setPatSel(i)}>
                    {p.direction === 'bullish' ? '▲' : '▼'} {p.name}
                  </button>
                ))}
              </div>
              {selPat && (
                <div className="pat">
                  <div>
                    <span className={'chip ' + (selPat.direction === 'bullish' ? 'up' : 'down')}>{selPat.name}</span>
                    <span className="faint" style={{ marginLeft: 8, fontSize: 12 }}>{selPat.direction} · confidence {selPat.confidence}</span>
                  </div>
                  <p>{selPat.explanation}</p>
                </div>
              )}
            </>
          ) : (
            <div className="placeholder">No clear pattern on the {timeframe} chart — try another timeframe. (Heuristic learning aid, not a signal.)</div>
          )}
        </div>
      )}
    </div>
  )

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo"><Logo /> Trade Craft</div>
          <div className="tabs"><a className="on">Research</a><a onClick={() => onNavigate('compare')} style={{ cursor: 'pointer' }}>Comparison</a><a onClick={() => onNavigate('watchlist')} style={{ cursor: 'pointer' }}>Watchlist</a><a onClick={() => onNavigate('history')} style={{ cursor: 'pointer' }}>History</a></div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className={'watchbtn' + (watched ? ' on' : '')} onClick={onWatch}>{watched ? '★ Watching' : '☆ Watch'}</button>
          <button className="backbtn" onClick={onBack}>← New search</button>
        </div>
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
        <h1>{quote.name || ticker}</h1>
        <span className="ticker-tag mono">{ticker}</span>
        <span className="px mono">{sym}{quote.price}</span>
        {changeChip(quote.changePercent)}
      </div>

      {/* self-balancing two-column masonry */}
      <div className="cols" data-tick={tick}>
        <div className="col">
          <div ref={setRef('chart')}>{chartBlock}</div>
          {FLOW.filter((id) => assign[id] === 'L').map((id) => <div key={id} ref={setRef(id)}>{blocks[id]}</div>)}
        </div>
        <div className="col">
          <div ref={setRef('ai')}><AiRead ai={ai} loading={aiLoading} /></div>
          {FLOW.filter((id) => assign[id] === 'R').map((id) => <div key={id} ref={setRef(id)}>{blocks[id]}</div>)}
        </div>
      </div>

      <AskClaude ticker={ticker} />
    </div>
  )
}
