// Glossary — a lookup for terms used throughout the app (indicators, chart
// patterns, ecosystem/fundamentals figures) but never explained in one place
// (docs/AUDIT.md §9: "a beginner meeting 'beta' or 'neckline' in prose has
// nowhere to look it up"). Static reference text, not tied to any one stock —
// contrast with lessons.js, which teaches a metric IN CONTEXT of the current
// stock's own numbers. Grouped so the Glossary view can section them.
export const GLOSSARY = [
  {
    group: 'Indicators',
    terms: [
      { term: 'RSI (Relative Strength Index)', def: 'A 0-100 score compressing recent up-moves vs down-moves. Above 70 is "overbought," below 30 is "oversold." A momentum gauge, not a trend or a buy/sell signal on its own.' },
      { term: 'MACD', def: 'The gap between a fast (12-day) and slow (26-day) moving average, with a 9-day "signal" line smoothing it. A positive, widening histogram (MACD above signal) reads as accelerating momentum; negative and widening reads as fading.' },
      { term: 'SMA (Simple Moving Average)', def: 'The average closing price over N sessions — a trend line that smooths day-to-day noise. SMA 50 is medium-term; SMA 200 is the classic long-term trend line.' },
      { term: 'Bollinger Bands', def: 'The 20-day average with an envelope two standard deviations above and below it. Price near the upper band can mean strength or short-term overextension; the bands widening means volatility is rising, squeezing means it\'s calming.' },
      { term: 'Volume', def: 'How many shares changed hands. The confirmation layer: a price move on heavy volume shows real participation; the same move on light volume is weaker, less-trusted.' },
    ],
  },
  {
    group: 'Chart patterns',
    terms: [
      { term: 'Neckline', def: 'The line connecting the dips (for a top pattern) or bounces (for a bottom pattern) between peaks/troughs. A close through it is the classic confirmation a pattern has "triggered."' },
      { term: 'Double/Triple Top', def: 'Two or three peaks at a similar level with dips between — a topping shape where buyers repeatedly failed to clear the same resistance. Read as bearish/exhaustion.' },
      { term: 'Double/Triple Bottom', def: 'The mirror of a top: two or three troughs at a similar level where sellers repeatedly failed to break lower. Read as bullish/basing.' },
      { term: 'Head & Shoulders', def: 'A higher middle peak (the "head") between two lower, similar peaks (the "shoulders") — a classic end-of-uptrend reversal shape. The inverse (a lower middle trough) is the bottoming mirror.' },
      { term: 'Triangle (ascending/descending/symmetrical)', def: 'Converging support and resistance lines. Ascending = flat resistance, rising support (bullish lean). Descending = falling resistance, flat support (bearish lean). Symmetrical = both converging toward a point (direction-neutral until it breaks).' },
      { term: 'Wedge (rising/falling)', def: 'Both lines slope the SAME direction but converge. A rising wedge (support rising faster) is typically read as bearish exhaustion; a falling wedge (resistance falling faster) as bullish.' },
      { term: 'Channel (ascending/descending)', def: 'Parallel (non-converging) support and resistance lines — an orderly trend bouncing between two rails, up or down.' },
      { term: 'Support / Resistance', def: 'A price level where a stock has repeatedly stopped falling (support) or stopped rising (resistance) — traced by connecting swing lows or swing highs.' },
    ],
  },
  {
    group: 'Company / fundamentals',
    terms: [
      { term: 'Beta', def: 'How much a stock\'s price tends to move for a given move in its benchmark index. 1 = moves in step; above 1 = amplified swings; below 1 = muted swings.' },
      { term: 'Market cap', def: 'Share price × total shares outstanding — the total market value of the company, in the listing\'s own currency.' },
      { term: 'P/E ratio (price-to-earnings)', def: 'Share price divided by earnings per share. A rough gauge of how much investors are paying for each dollar of current (trailing) or expected (forward) profit.' },
      { term: 'EPS (earnings per share)', def: 'Net profit divided by shares outstanding — how much of the company\'s earnings is attributable to a single share.' },
      { term: 'Revenue growth', def: 'The percentage change in total sales versus the prior comparable period.' },
      { term: 'Profit margin', def: 'Net profit as a percentage of revenue — how much of every dollar of sales the company actually keeps.' },
      { term: 'Dividend yield', def: 'Annual dividend payments as a percentage of the current share price.' },
      { term: 'Debt/Equity', def: 'Total debt relative to shareholder equity — a measure of how much the company relies on borrowing versus its own capital.' },
      { term: 'Peers / ecosystem', def: 'Other companies the app shows alongside a stock — either same-industry competitors, or (when that data isn\'t available for a listing) companies other investors commonly view alongside it, which is a different, related-but-not-identical signal.' },
    ],
  },
]
