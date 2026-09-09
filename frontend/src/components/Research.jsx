import Logo from './Logo.jsx'
import PriceChart from './PriceChart.jsx'
import Metrics from './Metrics.jsx'

function changeChip(pct) {
  if (pct == null) return <span className="chip flat">—</span>
  const cls = pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat'
  const arrow = pct > 0 ? '▲' : pct < 0 ? '▼' : '■'
  return <span className={'chip ' + cls}>{arrow} {pct > 0 ? '+' : ''}{pct}%</span>
}

// Deterministic, factual technical snapshot (NOT an AI opinion).
function snapshot(ind) {
  const items = []
  if (ind.above_sma50 != null && ind.sma50 != null)
    items.push([`Price is ${ind.above_sma50 ? 'above' : 'below'} the 50-day average`, `${ind.price} vs ${ind.sma50}`])
  if (ind.above_sma200 != null && ind.sma200 != null)
    items.push([`Price is ${ind.above_sma200 ? 'above' : 'below'} the 200-day average`, `${ind.price} vs ${ind.sma200}`])
  if (ind.rsi14 != null) {
    const z = ind.rsi14 >= 70 ? 'overbought' : ind.rsi14 <= 30 ? 'oversold' : 'neutral'
    items.push([`RSI(14) is ${ind.rsi14} — ${z}`, ''])
  }
  if (ind.macd?.hist != null)
    items.push([`MACD histogram is ${ind.macd.hist > 0 ? 'positive' : 'negative'}`, `${ind.macd.hist}`])
  if (ind.volume_vs_20d_pct != null)
    items.push([`Volume ${ind.volume_vs_20d_pct > 0 ? 'above' : 'below'} its 20-day average`, `${ind.volume_vs_20d_pct}%`])
  return items
}

export default function Research({ data, onBack }) {
  const { ticker, quote, indicators, ohlcv, meta } = data

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo"><Logo /> Trade101</div>
          <div className="tabs"><a className="on">Research</a><a>Comparison</a><a>History</a></div>
        </div>
        <button className="backbtn" onClick={onBack}>← New search</button>
      </div>

      <div className="headline">
        <h1>{ticker}</h1>
        <span className="px mono">{quote.currency === 'INR' ? '₹' : quote.currency === 'USD' ? '$' : ''}{quote.price}</span>
        {changeChip(quote.changePercent)}
        <span className="mkt">{quote.name} · {quote.exchange} · {meta.note}</span>
      </div>

      <div className="row cockpit">
        <div className="card">
          <div className="charthead">
            <span className="lbl" style={{ margin: 0 }}>Live chart · {meta.bars} sessions · as of {meta.asOf}</span>
            <button className="patbtn">🔍 Patterns<span className="phase">M4</span></button>
          </div>
          <PriceChart ohlcv={ohlcv} />
        </div>

        <div className="card snap">
          <div className="lbl">Technical snapshot <span className="faint" style={{ textTransform: 'none', letterSpacing: 0 }}>(facts, not advice)</span></div>
          <ul>
            {snapshot(indicators).map(([main, sub], i) => (
              <li key={i}><b>{main}</b>{sub ? <span className="mono" style={{ marginLeft: 8 }}>{sub}</span> : null}</li>
            ))}
          </ul>
          <div className="placeholder" style={{ marginTop: 12 }}>
            The AI <b>momentum read</b> with sourced reasoning arrives in <span className="phase">M3</span>. This snapshot is pure computed fact.
          </div>
        </div>
      </div>

      <div className="row midrow">
        <Metrics indicators={indicators} ticker={ticker} />
        <div className="card">
          <div className="lbl">News &amp; "What it means"<span className="phase">M3</span></div>
          <div className="placeholder">
            Sourced headlines (Feed) and Trade101's inference of how they may affect {ticker} will populate here once the News &amp; Analysis agents are wired in Milestone 3.
          </div>
        </div>
      </div>

      <div className="card">
        <div className="lbl">Ecosystem &amp; index<span className="phase">M4</span></div>
        <div className="placeholder">Supply-chain chain + the index {ticker} lives in (S&amp;P/NASDAQ) with beta — Milestone 4.</div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <div className="lbl">📎 References</div>
        <div className="refs">Source: <b>Yahoo Finance</b> — live price &amp; indicators. (News/filing sources added in M3.)</div>
      </div>
    </div>
  )
}
