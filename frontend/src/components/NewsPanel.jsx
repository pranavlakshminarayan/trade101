import { useState } from 'react'

// News block with two tabs: Feed (raw sourced headlines) and
// "What it means" (Trade101's reasoned inference — the sense-making).
export default function NewsPanel({ ai, loading, ticker }) {
  const [tab, setTab] = useState('means')

  const news = ai?.news || {}
  const feed = news.feed || []
  const inference = news.inference || {}

  return (
    <div className="card">
      <div className="lbl">News &amp; financial signals</div>
      <div className="newstabs">
        <button className={'ntab' + (tab === 'feed' ? ' on' : '')} onClick={() => setTab('feed')}>Feed</button>
        <button className={'ntab' + (tab === 'means' ? ' on' : '')} onClick={() => setTab('means')}>What it means ✦</button>
      </div>

      {loading && <div className="placeholder">Gathering and reading the news…</div>}

      {!loading && !ai?.available && (
        <div className="placeholder">{ai?.reason || 'News analysis unavailable.'}</div>
      )}

      {!loading && ai?.available && tab === 'feed' && (
        feed.length ? (
          feed.slice(0, 8).map((n, i) => (
            <div className="newsitem" key={i}>
              <span className="when">{n.datetime || ''}</span>
              <div>
                <b>{n.headline}</b>
                {n.url && <a className="src" href={n.url} target="_blank" rel="noreferrer"> {n.source || 'source'} ↗</a>}
              </div>
            </div>
          ))
        ) : (
          <div className="placeholder">{news.note || `No recent news returned for ${ticker}.`}</div>
        )
      )}

      {!loading && ai?.available && tab === 'means' && (
        <div className="infer">
          <span className="tagline">Trade101's inference · evidence-based, not advice</span>
          <p style={{ marginTop: 8 }}>{inference.summary || news.note || 'No news to interpret yet.'}</p>
          {inference.sources?.length > 0 && (
            <div className="faint" style={{ fontSize: 12, marginTop: 6 }}>Sources: {inference.sources.join(' · ')}</div>
          )}
        </div>
      )}
    </div>
  )
}
