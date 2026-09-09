import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

// Renders OHLCV as candlesticks (+volume) or a line/area, depending on `type`.
// `time` values are UNIX seconds so daily and intraday both render.
export default function PriceChart({ ohlcv, type = 'candles' }) {
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
      // Color the line by the window's net direction — green if it closed up
      // over the shown range, red if down (like a real ticker).
      const up = ohlcv[ohlcv.length - 1].close >= ohlcv[0].close
      const line = up ? '#00D68F' : '#F0616D'
      const top = up ? 'rgba(0,214,143,.28)' : 'rgba(240,97,109,.26)'
      const area = chart.addAreaSeries({
        lineColor: line, lineWidth: 2, topColor: top, bottomColor: 'rgba(10,20,30,0)',
      })
      area.setData(ohlcv.map((b) => ({ time: b.time, value: b.close })))
    } else {
      const candles = chart.addCandlestickSeries({
        upColor: '#00D68F', downColor: '#F0616D',
        wickUpColor: '#00D68F', wickDownColor: '#F0616D', borderVisible: false,
      })
      candles.setData(ohlcv.map((b) => ({ time: b.time, open: b.open, high: b.high, low: b.low, close: b.close })))
      const vol = chart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: '' })
      vol.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })
      vol.setData(ohlcv.map((b) => ({
        time: b.time, value: b.volume,
        color: b.close >= b.open ? 'rgba(0,214,143,.35)' : 'rgba(240,97,109,.35)',
      })))
    }

    chart.timeScale().fitContent()
    return () => chart.remove()
  }, [ohlcv, type])

  return <div className="chartwrap" ref={ref} />
}
