// Contextual metric lessons — explain each indicator ON the current stock,
// using its real value. Static text for Milestone 2; the AI agent deepens
// these in Milestone 3. Every lesson is factual about the number shown.

const fmt = (v) => (v == null ? '—' : v)

export const METRICS = ['RSI', 'MACD', 'SMA50', 'SMA200', 'Bollinger', 'Volume']

export function metricValue(metric, ind) {
  switch (metric) {
    case 'RSI': return fmt(ind.rsi14)
    case 'MACD': return ind.macd?.macd == null ? '—' : (ind.macd.macd > 0 ? '+' : '') + ind.macd.macd
    case 'SMA50': return fmt(ind.sma50)
    case 'SMA200': return fmt(ind.sma200)
    case 'Bollinger': return ind.bollinger?.middle == null ? '—' : 'mid ' + ind.bollinger.middle
    case 'Volume': return ind.volume_vs_20d_pct == null ? '—' : (ind.volume_vs_20d_pct > 0 ? '+' : '') + ind.volume_vs_20d_pct + '%'
    default: return '—'
  }
}

export function metricLabel(metric) {
  return { RSI: 'RSI (14)', MACD: 'MACD (12,26,9)', SMA50: 'SMA 50', SMA200: 'SMA 200', Bollinger: 'Bollinger (20,2)', Volume: 'Volume vs 20d' }[metric]
}

export function lessonFor(metric, ind, ticker) {
  const t = ticker
  switch (metric) {
    case 'RSI': {
      const v = ind.rsi14
      const zone = v == null ? 'unavailable' : v >= 70 ? 'overbought territory (≥70)' : v <= 30 ? 'oversold territory (≤30)' : 'the neutral zone'
      const lean = v == null ? '' : v > 50 ? ' Above 50 leans toward upward momentum.' : ' Below 50 leans toward downward momentum.'
      return {
        title: `RSI (14) = ${fmt(v)} on ${t}`,
        body: `The Relative Strength Index runs 0–100 and measures the speed of recent price moves — above 70 is "overbought," below 30 is "oversold." ${t} is currently at ${fmt(v)}, in ${zone}.${lean} RSI is a momentum gauge, not a buy/sell trigger — it's most useful read alongside the trend (the moving averages).`,
      }
    }
    case 'MACD': {
      const m = ind.macd || {}
      const state = m.hist == null ? '' : m.hist > 0 ? 'The histogram is positive — short-term momentum is above the longer trend (bullish tilt).' : 'The histogram is negative — short-term momentum is below the longer trend (bearish tilt).'
      return {
        title: `MACD on ${t}: line ${fmt(m.macd)}, signal ${fmt(m.signal)}`,
        body: `MACD compares a fast (12-day) and slow (26-day) moving average; the "signal" is a 9-day average of that difference. When the MACD line is above the signal, momentum is building up; below, it's fading. ${state}`,
      }
    }
    case 'SMA50': {
      const above = ind.above_sma50
      return {
        title: `50-day SMA = ${fmt(ind.sma50)} on ${t}`,
        body: `The 50-day simple moving average is the average closing price over the last 50 sessions — a medium-term trend line. ${t} is trading ${above ? 'ABOVE' : 'BELOW'} it (price ${fmt(ind.price)}), which is generally read as a ${above ? 'constructive medium-term' : 'weak medium-term'} trend.`,
      }
    }
    case 'SMA200': {
      if (ind.sma200 == null) return { title: `200-day SMA on ${t}`, body: `Not enough history yet to compute the 200-day average for ${t} — shown honestly as unavailable rather than guessed.` }
      const above = ind.above_sma200
      return {
        title: `200-day SMA = ${ind.sma200} on ${t}`,
        body: `The 200-day SMA is the classic long-term trend line. Trading above it is widely treated as a long-term uptrend; below, a long-term downtrend. ${t} is ${above ? 'ABOVE' : 'BELOW'} its 200-day average.`,
      }
    }
    case 'Bollinger': {
      const b = ind.bollinger || {}
      return {
        title: `Bollinger Bands (20,2) on ${t}`,
        body: `Bollinger Bands wrap the 20-day average (${fmt(b.middle)}) with a band two standard deviations above (${fmt(b.upper)}) and below (${fmt(b.lower)}). Price near the upper band = stretched high; near the lower band = stretched low; the bands widen when volatility rises. ${t}'s price is ${fmt(ind.price)}.`,
      }
    }
    case 'Volume': {
      const v = ind.volume_vs_20d_pct
      const dir = v == null ? '' : v > 0 ? `${v}% ABOVE its 20-day average — heavier participation` : `${Math.abs(v)}% BELOW its 20-day average — lighter participation`
      return {
        title: `Volume on ${t}`,
        body: `Volume is how many shares traded. Today's volume is ${dir}. Rising volume behind a price move suggests conviction; a move on thin volume is less reliable. Latest volume: ${ind.volume?.toLocaleString?.() ?? ind.volume}.`,
      }
    }
    default:
      return { title: metric, body: '' }
  }
}
