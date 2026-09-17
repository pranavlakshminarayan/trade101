import { useEffect, useMemo, useRef, useState } from 'react'
import Logo from './Logo.jsx'
import PriceChart from './PriceChart.jsx'
import Metrics from './Metrics.jsx'
import AiRead from './AiRead.jsx'
import NewsPanel from './NewsPanel.jsx'
import Ecosystem from './Ecosystem.jsx'
import AskClaude from './AskClaude.jsx'
import { SearchIcon, StarIcon, PlusIcon, ArrowIcon, PaperclipIcon } from './Icons.jsx'
import { analyze, news as fetchNews, research, patterns as fetchPatterns } from '../api.js'
import { addHistory } from '../lib/history.js'
import { isWatched, toggleWatch } from '../lib/watchlist.js'
import { currencySymbol } from '../lib/currency.js'

const REFRESH_MS = 7 * 60 * 1000

const TF = {
  '1Y':  { period: '1y',  interval: '1d' },
  '1M':  { period: '1mo', interval: '1d' },
  '10D': { period: '1mo', interval: '30m', slice: 130 },
  '5D':  { period: '5d',  interval: '15m' },
  '1D':  { period: '1d',  interval: '5m' },
}
const TF_ORDER = ['1Y', '1M', '10D', '5D', '1D']

function changeChip(pct) {
  if (pct == null) return <span className="chip flat">—</span>
  const cls = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  const dir = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  return <span className={'chip ' + cls}><ArrowIcon direction={dir} className="icon" /> {pct > 0 ? '+' : ''}{pct}%</span>
}

export default function Research({ data, onBack, onSearch, onNavigate, onHome }) {
  const [live, setLive] = useState(data)
  const [ai, setAi] = useState(null)
  const [aiLoading, setAiLoading] = useState(true)
  const [newsData, setNewsData] = useState(null)
  const [newsLoading, setNewsLoading] = useState(true)
  const [chartType, setChartType] = useState('candles')
  const [timeframe, setTimeframe] = useState('1Y')
  const [tfData, setTfData] = useState({})
  const [tfLoading, setTfLoading] = useState(false)
  const [showPatterns, setShowPatterns] = useState(false)
  const [patData, setPatData] = useState({})
  // Chart indicator overlays/panes (docs/AUDIT.md H5). SMA on by default — the
  // most commonly wanted overlay and light enough not to clutter the chart;
  // Bollinger/RSI/MACD are togglable but off by default so the chart isn't
  // busy the first time a beginner opens it.
  const [overlays, setOverlays] = useState({ sma: true, bollinger: false })
  const [showRsi, setShowRsi] = useState(false)
  const [showMacd, setShowMacd] = useState(false)
  const [patSel, setPatSel] = useState(0)
  const [updatedAt, setUpdatedAt] = useState(new Date())
  const [q, setQ] = useState('')
  const [watched, setWatched] = useState(false)

  const ticker = live.ticker

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

  // News loads independently of the AI call (docs/AUDIT.md H3) — free,
  // deterministic, and unaffected by a missing key / AI error / daily cap.
  useEffect(() => {
    let alive = true
    setNewsLoading(true); setNewsData(null)
    fetchNews(data.ticker).then((r) => { if (alive) { setNewsData(r); setNewsLoading(false) } })
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
      .then((r) => { if (alive) setTfData((c) => ({ ...c, [timeframe]: { ohlcv: r.ohlcv, indicatorSeries: r.indicatorSeries, indicators: r.indicators } })) })
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
        if (tf !== '1Y') {
          const r = await research(data.ticker, { ...TF[tf], fresh: true })
          setTfData((c) => ({ ...c, [tf]: { ohlcv: r.ohlcv, indicatorSeries: r.indicatorSeries, indicators: r.indicators } }))
        }
      } catch { /* keep last good */ }
    }, REFRESH_MS)
    return () => clearInterval(id)
  }, [data.ticker])

  const { quote, indicators: liveIndicators, ohlcv, meta, indicatorSeries: liveIndicatorSeries } = live
  // Metrics must reflect the SELECTED chart timeframe, not always the base
  // 1Y/daily snapshot — previously `indicators` here was unconditionally
  // `live.indicators` (the 1Y figures) even while a 10D/5D/1D tab was active,
  // so e.g. a 200-day SMA that's genuinely undefined on 30-min bars (not
  // enough intraday history for 200 bars) instead silently showed the
  // unrelated 1Y daily SMA200 value — a real number, just for the wrong
  // timeframe, and confusing next to a chart with no SMA200 line at all
  // (user-reported, TECA.F 10D). `null` fields render as "—" correctly once
  // the RIGHT (per-timeframe) indicators object is used.
  const indicators = timeframe === '1Y' ? liveIndicators : (tfData[timeframe]?.indicators || liveIndicators)
  const sym = currencySymbol(quote.currency)
  const sources = ai?.available ? (ai.sources || []) : []
  const lean = ai?.available ? ai.momentum?.lean : null

  const rawTf = timeframe === '1Y' ? ohlcv : (tfData[timeframe]?.ohlcv || [])
  const rawIndicatorSeries = timeframe === '1Y' ? liveIndicatorSeries : (tfData[timeframe]?.indicatorSeries || null)
  const sl = TF[timeframe].slice
  // Memoized: Research re-renders on every keystroke in the header search box
  // (the `q` state lives here). Without this, .slice() below returned a fresh
  // array identity on every render, which PriceChart's effect took as "the
  // data changed" and rebuilt the whole chart accordingly (docs/AUDIT.md H4).
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const chartOhlcv = useMemo(() => (sl ? rawTf.slice(-sl) : rawTf), [rawTf, sl])
  // Indicator points are timestamped absolutely, so slicing the OHLCV window
  // doesn't require slicing these too — lightweight-charts only draws the
  // points that fall inside the chart's own visible time range.
  const chartIndicatorSeries = rawIndicatorSeries
  const overlaysActive = useMemo(() => ({ sma: overlays.sma, bollinger: overlays.bollinger }), [overlays.sma, overlays.bollinger])
  const panesActive = useMemo(() => ({ rsi: showRsi, macd: showMacd }), [showRsi, showMacd])
  const chartLoading = timeframe !== '1Y' && !tfData[timeframe] && tfLoading

  const pats = patData[timeframe] || []
  const selPat = pats[patSel] || null
  // Same identity-stability fix for the pattern overlay passed to PriceChart.
  const chartPatterns = useMemo(() => (showPatterns && selPat ? [selPat] : []), [showPatterns, selPat])

  const submit = () => { const s = q.trim(); if (s) onSearch(s) }

  // side-column blocks (fixed order: news -> ecosystem -> references)
  const blocks = {
    metrics: <Metrics indicators={indicators} ticker={ticker} />,
    news: <NewsPanel newsData={newsData} newsLoading={newsLoading} ai={ai} aiLoading={aiLoading} ticker={ticker} />,
    ecosystem: <Ecosystem ticker={ticker} onSearch={onSearch} />,
    references: (
      <div className="card">
        <div className="lbl"><PaperclipIcon className="icon" /> References — every source used</div>
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
        <button className={'patbtn' + (showPatterns ? ' on' : '')} onClick={() => setShowPatterns((s) => !s)}><SearchIcon className="icon" /> Patterns{showPatterns ? ' ✓' : ''}</button>
      </div>
      <div className="chart-toggle chart-indtoggle">
        <button className={overlays.sma ? 'on' : ''} onClick={() => setOverlays((o) => ({ ...o, sma: !o.sma }))} title="50/200-day simple moving averages">SMA</button>
        <button className={overlays.bollinger ? 'on' : ''} onClick={() => setOverlays((o) => ({ ...o, bollinger: !o.bollinger }))} title="Bollinger Bands (20, 2)">Bollinger</button>
        <button className={showRsi ? 'on' : ''} onClick={() => setShowRsi((v) => !v)} title="RSI in its own pane below price">RSI</button>
        <button className={showMacd ? 'on' : ''} onClick={() => setShowMacd((v) => !v)} title="MACD in its own pane below price">MACD</button>
      </div>
      {chartLoading || !chartOhlcv.length
        ? <div className="chartwrap placeholder" style={{ display: 'grid', placeItems: 'center' }}>Loading {timeframe}…</div>
        : <PriceChart ohlcv={chartOhlcv} type={chartType} patterns={chartPatterns} showPatterns={showPatterns}
                      indicatorSeries={chartIndicatorSeries} overlays={overlaysActive} panes={panesActive} />}
      <div className="note">{timeframe} · {TF[timeframe].interval} bars · updated {updatedAt.toLocaleTimeString()} · auto-refreshes every 7 min · {meta.note}</div>
      {showPatterns && (
        <div className="patterns-panel">
          {pats.length ? (
            <>
              <div className="pat-select">
                {pats.map((p, i) => (
                  <button key={i} className={'pat-tab' + (i === patSel ? ' on' : '')} onClick={() => setPatSel(i)}>
                    <ArrowIcon direction={p.direction === 'bullish' ? 'up' : 'down'} className="icon" /> {p.name}
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
          <button className="logo logo-btn" onClick={onHome}><Logo /> Trade Craft</button>
          <div className="tabs"><button className="on" aria-current="page">Research</button><button onClick={() => onNavigate('compare')}>Comparison</button><button onClick={() => onNavigate('watchlist')}>Watchlist</button><button onClick={() => onNavigate('history')}>History</button><button onClick={() => onNavigate('practice')}>Practice Lab</button></div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className={'watchbtn' + (watched ? ' on' : '')} onClick={onWatch}>
            <StarIcon filled={watched} className="icon" /> {watched ? 'Watching' : 'Watch'}
          </button>
          <button className="backbtn" onClick={onBack}><PlusIcon className="icon" /> New search</button>
        </div>
      </div>

      <div className="strip">
        <div className="strip-search">
          <SearchIcon className="icon faint" />
          <input placeholder="Search another company or ticker…" value={q}
                 onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') submit() }} />
        </div>
        <span className="strip-tk"><b>{ticker}</b> — {quote.name}</span>
        {lean && (
          <span className={'chip ' + (lean === 'bullish' ? 'up' : lean === 'bearish' ? 'down' : 'flat')}>
            <ArrowIcon direction={lean === 'bullish' ? 'up' : lean === 'bearish' ? 'down' : 'flat'} className="icon" /> {lean}
          </span>
        )}
        <span className="strip-meta">{quote.exchange}</span>
        <span className="strip-meta faint">delayed ~15m</span>
      </div>

      <div className="headline">
        <h1>{quote.name || ticker}</h1>
        <span className="ticker-tag mono">{ticker}</span>
        <span className="px mono">{sym}{quote.price}</span>
        {changeChip(quote.changePercent)}
      </div>

      {/* Fixed two-zone layout: chart -> metrics -> AI read is the main spine
          (metrics sit right under the chart, since the indicators are the
          thing being learned here, not an afterthought at the bottom);
          news -> ecosystem -> references always sit in the side column.
          Panels no longer move between columns as data streams in
          (docs/AUDIT.md UI-UX #2 — the old height-balancing masonry
          reshuffled unpredictably mid-load, which was the actual bug, not
          the multi-column layout). */}
      <div className="cols">
        <div className="col">
          {chartBlock}
          {blocks.metrics}
          <AiRead ai={ai} loading={aiLoading} />
        </div>
        <div className="col">
          {blocks.news}
          {blocks.ecosystem}
          {blocks.references}
        </div>
      </div>

      <AskClaude ticker={ticker} />
    </div>
  )
}
