import { useEffect, useRef } from 'react'
import {
  createChart, CandlestickSeries, AreaSeries, HistogramSeries, LineSeries, createSeriesMarkers,
} from 'lightweight-charts'

const PAT = '#F2A93B'   // amber — pattern overlay, stands out over green/red candles
const SMA50_C = '#5B9BD5'
const SMA200_C = '#C99A5A'
const BOLL_C = 'rgba(158,124,255,0.55)'
const RSI_C = '#8FD6FF'
const MACD_LINE_C = '#5B9BD5'
const MACD_SIGNAL_C = '#F2A93B'

// OHLCV as candlesticks (+volume) or a directional line/area, with optional
// SMA/Bollinger overlays, RSI/MACD sub-panes, a crosshair OHLC+indicator
// legend, and detected-pattern overlays. Ported to lightweight-charts v5 for
// this (docs/AUDIT.md finding H5) — v4 has no multi-pane support, which is
// what makes RSI/MACD sit properly below price instead of being crammed onto
// the same axis or omitted entirely (the app used to only ever EXPLAIN these
// indicators in prose next to a chart that never plotted them).
//
// Lifecycle is split into independent effects so no single prop change tears
// the whole chart down (docs/AUDIT.md finding H4 — the earlier fix this
// builds on): chart creation (mount-once) / price series / overlays /
// indicator panes / pattern overlay / crosshair legend subscription.
export default function PriceChart({
  ohlcv, type = 'candles', patterns = [], showPatterns = false,
  indicatorSeries = null, overlays = { sma: false, bollinger: false },
  panes = { rsi: false, macd: false },
}) {
  const containerRef = useRef(null)
  const legendRef = useRef(null)
  const chartRef = useRef(null)
  const seriesRef = useRef({ type: null, main: null, vol: null })
  const overlaySeriesRef = useRef([])
  const paneSeriesRef = useRef({ rsi: null, macd: null, macdSignal: null, macdHist: null })
  const patternSeriesRef = useRef([])
  const patternMarkersRef = useRef([])
  const fitKeyRef = useRef(null)
  // Latest data, read imperatively by the crosshair handler so that handler
  // doesn't need to be re-subscribed (and so re-subscribing) on every render.
  const liveRef = useRef({ ohlcv, type, indicatorSeries })
  liveRef.current = { ohlcv, type, indicatorSeries }

  // 1. Create the chart once, on mount. Never recreated by a data/prop change.
  useEffect(() => {
    if (!containerRef.current) return
    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: { background: { color: 'transparent' }, textColor: '#9FB4C4', fontFamily: 'Segoe UI, system-ui, sans-serif' },
      grid: { vertLines: { color: '#1c2f3f' }, horzLines: { color: '#1c2f3f' } },
      rightPriceScale: { borderColor: '#294056' },
      timeScale: { borderColor: '#294056', secondsVisible: false },
      crosshair: { mode: 0 },
    })
    chartRef.current = chart
    return () => {
      chart.remove()
      chartRef.current = null
      seriesRef.current = { type: null, main: null, vol: null }
      overlaySeriesRef.current = []
      paneSeriesRef.current = { rsi: null, macd: null, macdSignal: null, macdHist: null }
      patternSeriesRef.current = []
      patternMarkersRef.current = []
      fitKeyRef.current = null
    }
  }, [])

  // 2. Price series: swap series type only when `type` actually changes
  // (candles <-> line); otherwise just refresh the existing series' data.
  useEffect(() => {
    const chart = chartRef.current
    if (!chart || !ohlcv?.length) return

    if (seriesRef.current.type !== type) {
      if (seriesRef.current.main) chart.removeSeries(seriesRef.current.main)
      if (seriesRef.current.vol) chart.removeSeries(seriesRef.current.vol)
      if (type === 'line') {
        const up = ohlcv[ohlcv.length - 1].close >= ohlcv[0].close
        const line = up ? '#00D68F' : '#F0616D'
        const top = up ? 'rgba(0,214,143,.28)' : 'rgba(240,97,109,.26)'
        seriesRef.current.main = chart.addSeries(AreaSeries, { lineColor: line, lineWidth: 2, topColor: top, bottomColor: 'rgba(10,20,30,0)' })
        seriesRef.current.vol = null
        chart.timeScale().applyOptions({ timeVisible: true })
      } else {
        seriesRef.current.main = chart.addSeries(CandlestickSeries, {
          upColor: '#00D68F', downColor: '#F0616D', wickUpColor: '#00D68F', wickDownColor: '#F0616D', borderVisible: false,
        })
        seriesRef.current.vol = chart.addSeries(HistogramSeries, { priceFormat: { type: 'volume' }, priceScaleId: '' })
        seriesRef.current.vol.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })
        chart.timeScale().applyOptions({ timeVisible: false })
      }
      seriesRef.current.type = type
    }

    if (type === 'line') {
      seriesRef.current.main.setData(ohlcv.map((b) => ({ time: b.time, value: b.close })))
    } else {
      seriesRef.current.main.setData(ohlcv.map((b) => ({ time: b.time, open: b.open, high: b.high, low: b.low, close: b.close })))
      seriesRef.current.vol.setData(ohlcv.map((b) => ({ time: b.time, value: b.volume, color: b.close >= b.open ? 'rgba(0,214,143,.35)' : 'rgba(240,97,109,.35)' })))
    }

    // Re-fit the view only when this is genuinely a different window (new
    // ticker or timeframe changes the bar count and/or the first timestamp),
    // not on a same-shape auto-refresh tick — so the user's zoom/pan survive
    // a refresh instead of being reset every 7 minutes.
    const key = `${ohlcv.length}|${ohlcv[0]?.time}|${ohlcv[ohlcv.length - 1]?.time}`
    if (fitKeyRef.current !== key) {
      const isFirstFit = fitKeyRef.current === null
      fitKeyRef.current = key
      if (isFirstFit) chart.timeScale().fitContent()
    }
  }, [ohlcv, type])

  // 3. Overlays (SMA50/SMA200, Bollinger) — pane 0, sharing the price scale.
  // Independent of the price series itself: toggling an overlay never
  // touches the candles/volume.
  useEffect(() => {
    const chart = chartRef.current
    if (!chart) return
    overlaySeriesRef.current.forEach((s) => { try { chart.removeSeries(s) } catch { /* chart/series already gone */ } })
    overlaySeriesRef.current = []
    if (!indicatorSeries) return

    if (overlays.sma) {
      if (indicatorSeries.sma50?.length) {
        const s = chart.addSeries(LineSeries, { color: SMA50_C, lineWidth: 2, priceLineVisible: false, lastValueVisible: false, title: 'SMA 50' })
        s.setData(indicatorSeries.sma50)
        overlaySeriesRef.current.push(s)
      }
      if (indicatorSeries.sma200?.length) {
        const s = chart.addSeries(LineSeries, { color: SMA200_C, lineWidth: 2, priceLineVisible: false, lastValueVisible: false, title: 'SMA 200' })
        s.setData(indicatorSeries.sma200)
        overlaySeriesRef.current.push(s)
      }
    }
    if (overlays.bollinger && indicatorSeries.bollinger?.upper?.length) {
      const { upper, middle, lower } = indicatorSeries.bollinger
      const up = chart.addSeries(LineSeries, { color: BOLL_C, lineWidth: 1, priceLineVisible: false, lastValueVisible: false, title: 'Bollinger' })
      up.setData(upper)
      const mid = chart.addSeries(LineSeries, { color: BOLL_C, lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false })
      mid.setData(middle)
      const low = chart.addSeries(LineSeries, { color: BOLL_C, lineWidth: 1, priceLineVisible: false, lastValueVisible: false })
      low.setData(lower)
      overlaySeriesRef.current.push(up, mid, low)
    }
  }, [indicatorSeries, overlays.sma, overlays.bollinger])

  // 4. Indicator panes (RSI, MACD) — each in its own pane below price. Torn
  // down and rebuilt fresh on any toggle change (removing every pane past
  // the main one first) rather than trying to patch individual panes in
  // place — panes shift index when one is removed, so a full rebuild avoids
  // a whole class of off-by-one bugs for a UI action that's rare (a toggle
  // click) and cheap to redo.
  useEffect(() => {
    const chart = chartRef.current
    if (!chart) return
    while (chart.panes().length > 1) chart.removePane(1)
    paneSeriesRef.current = { rsi: null, macd: null, macdSignal: null, macdHist: null }
    if (!indicatorSeries) return

    let nextPane = 1
    if (panes.rsi && indicatorSeries.rsi14?.length) {
      const p = nextPane++
      const rsi = chart.addSeries(LineSeries, {
        color: RSI_C, lineWidth: 2, priceLineVisible: false, lastValueVisible: true, title: 'RSI (14)',
        autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 100 } }),
      }, p)
      rsi.setData(indicatorSeries.rsi14)
      rsi.createPriceLine({ price: 70, color: '#F0616D', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'overbought' })
      rsi.createPriceLine({ price: 30, color: '#00D68F', lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: 'oversold' })
      chart.panes()[p]?.setStretchFactor(0.28)
      paneSeriesRef.current.rsi = rsi
    }
    if (panes.macd && indicatorSeries.macd?.macd?.length) {
      const p = nextPane++
      // `title` renders its own persistent axis label independent of
      // lastValueVisible — set on only ONE series per pane (else every
      // series' label stacks up and overlaps, as MACD's hist+line did here).
      const hist = chart.addSeries(HistogramSeries, { priceLineVisible: false, lastValueVisible: false }, p)
      hist.setData(indicatorSeries.macd.hist.map((pt) => ({
        ...pt, color: pt.value >= 0 ? 'rgba(0,214,143,.55)' : 'rgba(240,97,109,.55)',
      })))
      const macdLine = chart.addSeries(LineSeries, { color: MACD_LINE_C, lineWidth: 2, priceLineVisible: false, lastValueVisible: true, title: 'MACD (12,26,9)' }, p)
      macdLine.setData(indicatorSeries.macd.macd)
      const signal = chart.addSeries(LineSeries, { color: MACD_SIGNAL_C, lineWidth: 1, priceLineVisible: false, lastValueVisible: false }, p)
      signal.setData(indicatorSeries.macd.signal)
      chart.panes()[p]?.setStretchFactor(0.28)
      paneSeriesRef.current.macd = macdLine
      paneSeriesRef.current.macdSignal = signal
      paneSeriesRef.current.macdHist = hist
    }
    chart.panes()[0]?.setStretchFactor(1)
  }, [indicatorSeries, panes.rsi, panes.macd])

  // 5. Pattern overlay: fully independent of the price series/panes above —
  // toggling or switching a pattern never touches the chart/price data.
  useEffect(() => {
    const chart = chartRef.current
    if (!chart) return
    patternSeriesRef.current.forEach((s) => { try { chart.removeSeries(s) } catch { /* already gone with the chart */ } })
    patternSeriesRef.current = []
    patternMarkersRef.current.forEach((m) => { try { m.setMarkers([]) } catch { /* series already removed */ } })
    patternMarkersRef.current = []

    if (!showPatterns || !patterns?.length) return
    patterns.forEach((pat) => {
      const pts = (pat.points || []).map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time)
      // Trendline shapes (triangles/wedges/channels) carry `lines`; reversal
      // shapes connect their swing `points` instead.
      if (pat.lines?.length) {
        pat.lines.forEach((ln) => {
          const s = chart.addSeries(LineSeries, { color: PAT, lineWidth: 2, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
          s.setData(ln.map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time))
          patternSeriesRef.current.push(s)
        })
      } else if (pts.length) {
        const ls = chart.addSeries(LineSeries, { color: PAT, lineWidth: 2, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
        ls.setData(pts)
        patternSeriesRef.current.push(ls)
      }
      const labelled = (pat.points || []).filter((p) => p.label)
      if (labelled.length) {
        const marker = chart.addSeries(LineSeries, { color: 'rgba(0,0,0,0)', lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
        marker.setData(labelled.map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time))
        const markersApi = createSeriesMarkers(marker,
          labelled.slice().sort((a, b) => a.time - b.time).map((p) => ({
            time: p.time, position: pat.direction === 'bearish' ? 'aboveBar' : 'belowBar',
            color: PAT, shape: 'circle', text: p.label,
          })))
        patternSeriesRef.current.push(marker)
        patternMarkersRef.current.push(markersApi)
      }
      if (pat.neckline?.length === 2) {
        const nl = chart.addSeries(LineSeries, { color: PAT, lineWidth: 1, lineStyle: 2, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
        nl.setData(pat.neckline.map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time))
        patternSeriesRef.current.push(nl)
      }
    })
  }, [patterns, showPatterns])

  // 6. Crosshair legend — subscribed once on chart creation; reads the LATEST
  // data via `liveRef` so it never needs to be torn down/re-subscribed when
  // props change (that would risk missing events during the swap).
  useEffect(() => {
    const chart = chartRef.current
    if (!chart) return
    const handler = (param) => {
      const el = legendRef.current
      if (!el) return
      const { ohlcv: bars, type: t } = liveRef.current
      if (!param.time || !bars?.length) { el.innerHTML = ''; return }
      const bar = bars.find((b) => b.time === param.time)
      if (!bar) { el.innerHTML = ''; return }
      const chg = bar.close - bar.open
      const chgPct = bar.open ? (chg / bar.open) * 100 : 0
      const cls = chg > 0 ? 'up' : chg < 0 ? 'down' : 'flat'
      const parts = [`<b>O</b> ${bar.open.toFixed(2)}`, `<b>H</b> ${bar.high.toFixed(2)}`,
        `<b>L</b> ${bar.low.toFixed(2)}`, `<b>C</b> ${bar.close.toFixed(2)}`,
        `<span class="chartlegend-${cls}">${chg >= 0 ? '+' : ''}${chgPct.toFixed(2)}%</span>`]
      if (t !== 'line') parts.push(`<b>Vol</b> ${(bar.volume / 1e6).toFixed(2)}M`)
      el.innerHTML = parts.join('  ·  ')
    }
    chart.subscribeCrosshairMove(handler)
    return () => { try { chart.unsubscribeCrosshairMove(handler) } catch { /* chart already gone */ } }
  }, [])

  // Extra vertical room per active indicator pane, so RSI/MACD don't just
  // steal height from the price pane — each pane still gets a fixed
  // proportion of the total (see setStretchFactor above), but the total
  // itself grows to fit them.
  const paneCount = (panes.rsi ? 1 : 0) + (panes.macd ? 1 : 0)
  const height = 340 + paneCount * 110

  return (
    <div className="chartwrap-outer">
      <div className="chartlegend" ref={legendRef} />
      <div className="chartwrap" ref={containerRef} style={{ height }} />
    </div>
  )
}
