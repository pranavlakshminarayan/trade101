import { useEffect, useState } from 'react'
import Logo from './Logo.jsx'
import ComparisonChart from './ComparisonChart.jsx'
import { research, ecosystem, search } from '../api.js'
import { METRICS, metricLabel, metricValue } from '../lessons.js'

const TF = { '1Y': { period: '1y', interval: '1d' }, '1M': { period: '1mo', interval: '1d' } }
const TF_ORDER = ['1Y', '1M']

function marketCap(v) {
  if (v == null) return '—'
  if (v >= 1e12) return '$' + (v / 1e12).toFixed(2) + 'T'
  if (v >= 1e9) return '$' + (v / 1e9).toFixed(1) + 'B'
  if (v >= 1e6) return '$' + (v / 1e6).toFixed(0) + 'M'
  return '$' + v
}
function pct(v) {
  if (v == null) return '—'
  return (v > 0 ? '+' : '') + v + '%'
}

// One stock's loaded data for a comparison slot.
function useSlot() {
  const [state, setState] = useState({ ticker: null, data: null, eco: null, loading: false, error: null })
  async function load(query, tf) {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const { candidates = [] } = await search(query)
      const sym = candidates.length ? candidates[0].symbol : query
      const [data, eco] = await Promise.all([research(sym, TF[tf]), ecosystem(sym)])
      setState({ ticker: data.ticker, data, eco, loading: false, error: null })
      return data.ticker
    } catch (e) {
      setState((s) => ({ ...s, loading: false, error: e.message || 'Could not load' }))
    }
  }
  async function reloadTf(tf) {
    setState((s) => {
      if (!s.ticker) return s
      research(s.ticker, TF[tf]).then((d) => setState((cur) => ({ ...cur, data: d }))).catch(() => {})
      return s
    })
  }
  return [state, load, reloadTf]
}

export default function Compare({ onNavigate, onOpen, initial }) {
  const [timeframe, setTimeframe] = useState('1Y')
  const [qa, setQa] = useState('')
  const [qb, setQb] = useState('')
  const [A, loadA, reloadTfA] = useSlot()
  const [B, loadB, reloadTfB] = useSlot()

  // Seed slot A with the stock the user came from.
  useEffect(() => {
    if (initial && !A.ticker) { setQa(initial); loadA(initial, timeframe) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => { reloadTfA(timeframe); reloadTfB(timeframe) /* eslint-disable-next-line */ }, [timeframe])

  const bothLoaded = A.data && B.data
  const sym = (q) => (q === 'INR' ? '₹' : q === 'USD' ? '$' : '')

  const slotHeader = (S) => {
    if (S.loading) return <div className="faint">Loading…</div>
    if (S.error) return <div className="neg" style={{ fontSize: 13 }}>{S.error}</div>
    if (!S.data) return <div className="faint" style={{ fontSize: 13 }}>Pick a company above.</div>
    const q = S.data.quote
    return (
      <div>
        <div className="cmp-name">{q.name || S.ticker}</div>
        <div className="faint mono" style={{ fontSize: 12 }}>{S.ticker} · {q.exchange || ''}</div>
        <div style={{ marginTop: 4 }}>
          <span className="mono" style={{ fontSize: 18 }}>{sym(q.currency)}{q.price}</span>{' '}
          <span className={q.changePercent > 0 ? 'pos' : q.changePercent < 0 ? 'neg' : 'faint'}>{pct(q.changePercent)}</span>
        </div>
      </div>
    )
  }

  const rows = [
    ['Price', (S) => S.data ? `${sym(S.data.quote.currency)}${S.data.quote.price}` : '—'],
    ['Change %', (S) => S.data ? pct(S.data.quote.changePercent) : '—'],
    ...METRICS.map((m) => [metricLabel(m), (S) => S.data ? metricValue(m, S.data.indicators) : '—']),
    ['Beta', (S) => S.eco?.beta ?? '—'],
    ['Sector', (S) => S.eco?.sector || '—'],
    ['Market cap', (S) => marketCap(S.eco?.marketCap)],
  ]

  return (
    <div className="research">
      <div className="top">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo"><Logo /> Trade101</div>
          <div className="tabs">
            <a onClick={() => onNavigate('home')} style={{ cursor: 'pointer' }}>Research</a>
            <a className="on">Comparison</a>
            <a onClick={() => onNavigate('history')} style={{ cursor: 'pointer' }}>History</a>
          </div>
        </div>
        <button className="backbtn" onClick={() => onNavigate('home')}>← Back</button>
      </div>

      <div className="headline"><h1>Compare</h1>
        <span className="faint" style={{ fontSize: 13, alignSelf: 'center' }}>side by side · describes differences, never which to buy</span>
      </div>

      <div className="cmp-pickers">
        <div className="cmp-pick">
          <span className="cmp-dot" style={{ background: '#34A9BE' }} />
          <input placeholder="First company or ticker…" value={qa}
                 onChange={(e) => setQa(e.target.value)}
                 onKeyDown={(e) => { if (e.key === 'Enter' && qa.trim()) loadA(qa.trim(), timeframe) }} />
          <button className="go" onClick={() => qa.trim() && loadA(qa.trim(), timeframe)}>Load</button>
        </div>
        <div className="cmp-pick">
          <span className="cmp-dot" style={{ background: '#F2A93B' }} />
          <input placeholder="Second company or ticker…" value={qb}
                 onChange={(e) => setQb(e.target.value)}
                 onKeyDown={(e) => { if (e.key === 'Enter' && qb.trim()) loadB(qb.trim(), timeframe) }} />
          <button className="go" onClick={() => qb.trim() && loadB(qb.trim(), timeframe)}>Load</button>
        </div>
      </div>

      <div className="cmp-heads">
        <div className="card cmp-head cmp-a">{slotHeader(A)}</div>
        <div className="card cmp-head cmp-b">{slotHeader(B)}</div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="charthead">
          <div className="lbl" style={{ marginBottom: 0 }}>Normalized price — both rebased to 100 at the window start (% moves, not absolute prices)</div>
          <div className="chart-toggle">
            {TF_ORDER.map((t) => <button key={t} className={timeframe === t ? 'on' : ''} onClick={() => setTimeframe(t)}>{t}</button>)}
          </div>
        </div>
        {bothLoaded
          ? <ComparisonChart aOhlcv={A.data.ohlcv} bOhlcv={B.data.ohlcv} />
          : <div className="chartwrap placeholder" style={{ display: 'grid', placeItems: 'center' }}>Load two companies to compare.</div>}
        {bothLoaded && (
          <div className="cmp-legend">
            <span><span className="cmp-dot" style={{ background: '#34A9BE' }} /> {A.data.quote.name || A.ticker}</span>
            <span><span className="cmp-dot" style={{ background: '#F2A93B' }} /> {B.data.quote.name || B.ticker}</span>
          </div>
        )}
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="lbl">Metrics side by side</div>
        <table className="cmp-table">
          <thead>
            <tr><th></th>
              <th>{A.data ? (A.data.quote.name || A.ticker) : 'A'}</th>
              <th>{B.data ? (B.data.quote.name || B.ticker) : 'B'}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([label, get]) => (
              <tr key={label}>
                <td className="faint">{label}</td>
                <td className="mono">{get(A)}</td>
                <td className="mono">{get(B)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {bothLoaded && (
          <div className="faint" style={{ fontSize: 12, marginTop: 10 }}>
            Tap a company to open its full research: {' '}
            <button className="chipx" onClick={() => onOpen(A.ticker)}>{A.ticker}</button>{' '}
            <button className="chipx" onClick={() => onOpen(B.ticker)}>{B.ticker}</button>
          </div>
        )}
        <div className="note">Comparison describes differences in the data — it is not a recommendation of one over the other. Numbers are exact; data delayed ~15m.</div>
      </div>
    </div>
  )
}
