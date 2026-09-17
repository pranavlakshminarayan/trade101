import { useEffect, useRef } from 'react'
import { createChart, LineSeries } from 'lightweight-charts'

const A_COLOR = '#34A9BE' // teal — stock A
const B_COLOR = '#F2A93B' // amber — stock B (deliberately not green/red: no good/bad implied)

// Two price series rebased to 100 at the window start, so you compare % moves
// (not absolute prices). Deterministic; describes relative performance only.
function rebased(ohlcv) {
  if (!ohlcv?.length) return []
  const base = ohlcv[0].close
  if (!base) return []
  return ohlcv.map((b) => ({ time: b.time, value: +(b.close / base * 100).toFixed(2) }))
}

export default function ComparisonChart({ aOhlcv, bOhlcv }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current || (!aOhlcv?.length && !bOhlcv?.length)) return
    const chart = createChart(ref.current, {
      autoSize: true,
      layout: { background: { color: 'transparent' }, textColor: '#9FB4C4', fontFamily: 'Segoe UI, system-ui, sans-serif' },
      grid: { vertLines: { color: '#1c2f3f' }, horzLines: { color: '#1c2f3f' } },
      rightPriceScale: { borderColor: '#294056' },
      timeScale: { borderColor: '#294056', secondsVisible: false },
      crosshair: { mode: 0 },
    })
    const a = rebased(aOhlcv)
    const b = rebased(bOhlcv)
    if (a.length) {
      const s = chart.addSeries(LineSeries, { color: A_COLOR, lineWidth: 2, priceLineVisible: false, lastValueVisible: true })
      s.setData(a)
    }
    if (b.length) {
      const s = chart.addSeries(LineSeries, { color: B_COLOR, lineWidth: 2, priceLineVisible: false, lastValueVisible: true })
      s.setData(b)
    }
    chart.timeScale().fitContent()
    return () => chart.remove()
  }, [aOhlcv, bOhlcv])

  return <div className="chartwrap" ref={ref} />
}
