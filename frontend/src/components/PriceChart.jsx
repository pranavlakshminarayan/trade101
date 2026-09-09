import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

// Renders the OHLCV bundle as a candlestick + volume chart (Lightweight-Charts).
export default function PriceChart({ ohlcv }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current || !ohlcv?.length) return
    const chart = createChart(ref.current, {
      autoSize: true,
      layout: { background: { color: 'transparent' }, textColor: '#9FB4C4', fontFamily: 'Segoe UI, system-ui, sans-serif' },
      grid: { vertLines: { color: '#1c2f3f' }, horzLines: { color: '#1c2f3f' } },
      rightPriceScale: { borderColor: '#294056' },
      timeScale: { borderColor: '#294056', timeVisible: false },
      crosshair: { mode: 0 },
    })

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

    chart.timeScale().fitContent()
    return () => chart.remove()
  }, [ohlcv])

  return <div className="chartwrap" ref={ref} />
}
