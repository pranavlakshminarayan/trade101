import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

const PAT = '#F2A93B' // amber — stands out over green/red candles

// OHLCV as candlesticks (+volume) or a directional line/area. When `showPatterns`
// is on, overlays detected patterns: a line through the swing points, labeled
// markers, and the neckline.
//
// Split into THREE independent effects (chart lifecycle / price data / pattern
// overlay) instead of one effect that tore the whole chart down and rebuilt it
// on ANY prop change. That used to mean typing in the header search — which
// re-renders this component's parent on every keystroke — destroyed and
// recreated the chart several times a second, and the 7-min auto-refresh reset
// the user's zoom/pan every time (docs/AUDIT.md finding H4). Now: the chart
// object itself is created once and lives for the component's lifetime; price
// data updates via `setData` on the existing series; the view is only
// re-fit when the dataset is actually a different window (new ticker/
// timeframe), not on a same-shape refresh — so pan/zoom survive a refresh.
export default function PriceChart({ ohlcv, type = 'candles', patterns = [], showPatterns = false }) {
  const containerRef = useRef(null)
  const chartRef = useRef(null)
  const seriesRef = useRef({ type: null, main: null, vol: null })
  const patternSeriesRef = useRef([])
  const fitKeyRef = useRef(null)

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
      patternSeriesRef.current = []
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
        seriesRef.current.main = chart.addAreaSeries({ lineColor: line, lineWidth: 2, topColor: top, bottomColor: 'rgba(10,20,30,0)' })
        seriesRef.current.vol = null
        chart.timeScale().applyOptions({ timeVisible: true })
      } else {
        seriesRef.current.main = chart.addCandlestickSeries({
          upColor: '#00D68F', downColor: '#F0616D', wickUpColor: '#00D68F', wickDownColor: '#F0616D', borderVisible: false,
        })
        seriesRef.current.vol = chart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: '' })
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

  // 3. Pattern overlay: fully independent of the price series — toggling or
  // switching a pattern never touches (or rebuilds) the chart/price data.
  useEffect(() => {
    const chart = chartRef.current
    if (!chart) return
    patternSeriesRef.current.forEach((s) => { try { chart.removeSeries(s) } catch { /* already gone with the chart */ } })
    patternSeriesRef.current = []

    if (!showPatterns || !patterns?.length) return
    patterns.forEach((pat) => {
      const pts = (pat.points || []).map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time)
      // Trendline shapes (triangles/wedges/channels) carry `lines`; reversal
      // shapes connect their swing `points` instead.
      if (pat.lines?.length) {
        pat.lines.forEach((ln) => {
          const s = chart.addLineSeries({ color: PAT, lineWidth: 2, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
          s.setData(ln.map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time))
          patternSeriesRef.current.push(s)
        })
      } else if (pts.length) {
        const ls = chart.addLineSeries({ color: PAT, lineWidth: 2, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
        ls.setData(pts)
        patternSeriesRef.current.push(ls)
      }
      const labelled = (pat.points || []).filter((p) => p.label)
      if (labelled.length) {
        const marker = chart.addLineSeries({ color: 'rgba(0,0,0,0)', lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
        marker.setData(labelled.map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time))
        marker.setMarkers(
          labelled.slice().sort((a, b) => a.time - b.time).map((p) => ({
            time: p.time, position: pat.direction === 'bearish' ? 'aboveBar' : 'belowBar',
            color: PAT, shape: 'circle', text: p.label,
          }))
        )
        patternSeriesRef.current.push(marker)
      }
      if (pat.neckline?.length === 2) {
        const nl = chart.addLineSeries({ color: PAT, lineWidth: 1, lineStyle: 2, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
        nl.setData(pat.neckline.map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time))
        patternSeriesRef.current.push(nl)
      }
    })
  }, [patterns, showPatterns])

  return <div className="chartwrap" ref={containerRef} />
}
