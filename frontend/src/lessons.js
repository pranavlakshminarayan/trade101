// Metric learning: clicking a metric shows a FACT (deterministic, on this stock)
// then a richer LESSON (what it means and how to read it). Static text for
// Milestone 3; the AI read deepens the synthesis. Every fact uses the real value.

const f = (v) => (v == null ? '—' : v)

export const METRICS = ['RSI', 'MACD', 'SMA50', 'SMA200', 'Bollinger', 'Volume']

export function metricValue(metric, ind) {
  switch (metric) {
    case 'RSI': return f(ind.rsi14)
    case 'MACD': return ind.macd?.macd == null ? '—' : (ind.macd.macd > 0 ? '+' : '') + ind.macd.macd
    case 'SMA50': return f(ind.sma50)
    case 'SMA200': return f(ind.sma200)
    case 'Bollinger': return ind.bollinger?.middle == null ? '—' : 'mid ' + ind.bollinger.middle
    case 'Volume': return ind.volume_vs_20d_pct == null ? '—' : (ind.volume_vs_20d_pct > 0 ? '+' : '') + ind.volume_vs_20d_pct + '%'
    default: return '—'
  }
}

export function metricLabel(metric) {
  return { RSI: 'RSI (14)', MACD: 'MACD (12,26,9)', SMA50: 'SMA 50', SMA200: 'SMA 200', Bollinger: 'Bollinger (20,2)', Volume: 'Volume vs 20d' }[metric]
}

// The deterministic fact for THIS stock (what the old Technical Snapshot showed).
export function factFor(metric, ind, t) {
  const p = ind.price
  switch (metric) {
    case 'RSI': {
      const v = ind.rsi14
      const z = v == null ? 'n/a' : v >= 70 ? 'overbought' : v <= 30 ? 'oversold' : 'neutral'
      return `${t}'s RSI(14) is ${f(v)} — ${z}.`
    }
    case 'MACD': {
      const m = ind.macd || {}
      return `MACD line ${f(m.macd)} vs signal ${f(m.signal)}; histogram ${m.hist > 0 ? 'positive' : 'negative'} (${f(m.hist)}).`
    }
    case 'SMA50':
      return ind.sma50 == null ? `50-day average not available for ${t}.`
        : `Price ${f(p)} is ${ind.above_sma50 ? 'above' : 'below'} the 50-day average ${ind.sma50}.`
    case 'SMA200':
      return ind.sma200 == null ? `Not enough history for a 200-day average on ${t}.`
        : `Price ${f(p)} is ${ind.above_sma200 ? 'above' : 'below'} the 200-day average ${ind.sma200}.`
    case 'Bollinger': {
      const b = ind.bollinger || {}
      return `Price ${f(p)} sits within bands ${f(b.lower)} – ${f(b.upper)} (middle ${f(b.middle)}).`
    }
    case 'Volume': {
      const v = ind.volume_vs_20d_pct
      return `Latest volume is ${v == null ? 'n/a' : (v > 0 ? v + '% above' : Math.abs(v) + '% below')} the 20-day average.`
    }
    default: return ''
  }
}

// The richer teaching explanation.
export function lessonFor(metric, ind, t) {
  const p = ind.price
  switch (metric) {
    case 'RSI': {
      const v = ind.rsi14
      const lean = v == null ? '' : v > 50 ? ' Sitting above 50 tilts momentum upward,' : ' Sitting below 50 tilts momentum downward,'
      return `The Relative Strength Index compresses recent up-moves vs down-moves into a 0–100 score. Above 70 is "overbought" (the rally may be stretched); below 30 is "oversold" (the selloff may be stretched); the middle is the ordinary working range.${lean} but RSI is a *momentum* gauge, not a trend or a signal — its real value is as a cross-check: strong trend + mid-50s RSI is healthy; strong trend + 80 RSI is stretched. On its own it never tells you what happens next.`
    }
    case 'MACD':
      return `MACD is the distance between a fast (12-day) and slow (26-day) moving average, with a 9-day "signal" line smoothing it. When the MACD line is above the signal and the histogram (their gap) is positive and widening, short-term momentum is pulling ahead of the trend — accelerating. Negative and widening means it's fading. The *direction of the histogram* often matters more than the raw number: a shrinking positive histogram is momentum cooling even while still green.`
    case 'SMA50':
      return `The 50-day simple moving average is the average close over the last 50 sessions — a medium-term trend line that smooths daily noise. Price above it is generally read as a constructive medium-term trend; below it, a weak one. Traders also watch how the 50-day sits relative to the 200-day: 50 above 200 is a "stacked," healthy structure (a golden-cross regime); 50 below 200 is the opposite.`
    case 'SMA200':
      return `The 200-day average is the classic long-term trend line — many desks treat "above the 200-day" as a bull regime and "below" as a bear regime. The *distance* from it is a tell too: price far above the 200-day (like a stock up big on the year) shows strong trend but also room to mean-revert, so a single bad datapoint can snap it back hard.`
    case 'Bollinger':
      return `Bollinger Bands draw the 20-day average with an envelope two standard deviations above and below it. Price near the upper band means you're at the top of the recent statistical range — that can mean *strength* or *short-term overextension*, which is why it's read with the trend, not alone. The bands widening means volatility is rising; squeezing means it's calming.`
    case 'Volume':
      return `Volume is how many shares changed hands. It's the *confirmation* layer: a price move on heavy volume shows real participation and conviction, while the same move on light volume is a weaker, less-trusted signal. An up-day well below the 20-day average volume is exactly that — a move the crowd hasn't fully backed yet.`
    default:
      return ''
  }
}
