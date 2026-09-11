import { useState } from 'react'
import Coverage from './Coverage.jsx'

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

      {loading && (
        <div className="scraping">
          <div className="spinner" />
          <div className="faint" style={{ fontSize: 13 }}>Gathering the news feed…</div>
        </div>
      )}

      {!loading && !ai?.available && (
        <div className="placeholder">{ai?.reason || 'News analysis unavailable.'}</div>
      )}

      {!loading && ai?.available && tab === 'feed' && (
        feed.length ? (
          feed.slice(0, 8).map((n, i) => (
            <a className="newsbox" key={i} href={n.url || '#'} target="_blank" rel="noreferrer">
              <div className="newsbox-head">
                <span className="newsbox-src">{n.source || 'source'}</span>
                <span className="when">{n.datetime || ''}</span>
              </div>
              {n.relevanceWhy && (
                <div className="relwhy faint" title="Why this article was kept">
                  kept: {n.relevanceWhy}
                </div>
              )}
              <div className="newsbox-title">{n.headline}</div>
              {n.summary && <div className="newsbox-sum">{n.summary}</div>}
            </a>
          ))
        ) : (
          <div className="placeholder">
            {ai?.evidenceFilter?.considered > 0
              ? `Screened ${ai.evidenceFilter.considered} recent headline(s); none were specifically about ${ticker}, so none are used as evidence.`
              : (news.note || `No recent news returned for ${ticker}.`)}
          </div>
        )
      )}

      {!loading && ai?.available && tab === 'means' && (
        <div className="infer">
          <span className="tagline">Trade101's inference · evidence-based, not advice</span>
          <Coverage coverage={ai.coverage} filter={ai.evidenceFilter} />
          <p style={{ marginTop: 8 }}>{inference.summary || news.note || 'No news to interpret yet.'}</p>
          {inference.claims?.length > 0 && (
            <ul className="why">
              {inference.claims.map((c, i) => (
                <li key={i}>
                  <b>{c.point}</b>{' '}
                  {c.citations?.map((s, j) => (
                    s.url
                      ? <a key={j} className="cite" href={s.url} target="_blank" rel="noreferrer" title={s.label}>source ↗</a>
                      : <span key={j} className="cite cite-num" title={s.label}>{s.detail || s.label}</span>
                  ))}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
