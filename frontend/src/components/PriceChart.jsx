import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

const PAT = '#F2A93B' // amber — stands out over green/red candles

// OHLCV as candlesticks (+volume) or a directional line/area. When `showPatterns`
// is on, overlays detected patterns: a line through the swing points, labeled
// markers, and the neckline.
export default function PriceChart({ ohlcv, type = 'candles', patterns = [], showPatterns = false }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current || !ohlcv?.length) return
    const chart = createChart(ref.current, {
      autoSize: true,
      layout: { background: { color: 'transparent' }, textColor: '#9FB4C4', fontFamily: 'Segoe UI, system-ui, sans-serif' },
      grid: { vertLines: { color: '#1c2f3f' }, horzLines: { color: '#1c2f3f' } },
      rightPriceScale: { borderColor: '#294056' },
      timeScale: { borderColor: '#294056', timeVisible: type === 'line', secondsVisible: false },
      crosshair: { mode: 0 },
    })

    if (type === 'line') {
      const up = ohlcv[ohlcv.length - 1].close >= ohlcv[0].close
      const line = up ? '#00D68F' : '#F0616D'
      const top = up ? 'rgba(0,214,143,.28)' : 'rgba(240,97,109,.26)'
      const area = chart.addAreaSeries({ lineColor: line, lineWidth: 2, topColor: top, bottomColor: 'rgba(10,20,30,0)' })
      area.setData(ohlcv.map((b) => ({ time: b.time, value: b.close })))
    } else {
      const candles = chart.addCandlestickSeries({
        upColor: '#00D68F', downColor: '#F0616D', wickUpColor: '#00D68F', wickDownColor: '#F0616D', borderVisible: false,
      })
      candles.setData(ohlcv.map((b) => ({ time: b.time, open: b.open, high: b.high, low: b.low, close: b.close })))
      const vol = chart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: '' })
      vol.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })
      vol.setData(ohlcv.map((b) => ({ time: b.time, value: b.volume, color: b.close >= b.open ? 'rgba(0,214,143,.35)' : 'rgba(240,97,109,.35)' })))
    }

    // Pattern overlay
    if (showPatterns && patterns?.length) {
      patterns.forEach((pat) => {
        const pts = (pat.points || []).map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time)
        // Trendline shapes (triangles/wedges/channels) carry `lines`; reversal
        // shapes connect their swing `points` instead.
        if (pat.lines?.length) {
          pat.lines.forEach((ln) => {
            const s = chart.addLineSeries({ color: PAT, lineWidth: 2, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
            s.setData(ln.map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time))
          })
        } else if (pts.length) {
          const ls = chart.addLineSeries({ color: PAT, lineWidth: 2, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
          ls.setData(pts)
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
        }
        if (pat.neckline?.length === 2) {
          const nl = chart.addLineSeries({ color: PAT, lineWidth: 1, lineStyle: 2, lastValueVisible: false, priceLineVisible: false, crosshairMarkerVisible: false })
          nl.setData(pat.neckline.map((p) => ({ time: p.time, value: p.price })).sort((a, b) => a.time - b.time))
        }
      })
    }

    chart.timeScale().fitContent()
    return () => chart.remove()
  }, [ohlcv, type, patterns, showPatterns])

  return <div className="chartwrap" ref={ref} />
}
