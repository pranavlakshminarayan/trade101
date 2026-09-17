import { useState } from 'react'
import { SparkleIcon } from './Icons.jsx'

// News block with two tabs: Feed (raw sourced headlines, DETERMINISTIC — loads
// from the free /news endpoint, independent of the AI) and "What it means"
// (Trade Craft's reasoned inference — genuinely needs the AI call).
//
// Previously the Feed tab was sourced from the /analyze response too, so no
// Claude key / an AI error / the daily cap meant NO headlines at all —
// deterministic data held hostage by the judgment layer (docs/AUDIT.md H3).
// Feed now renders as soon as `newsData` arrives, whether or not `ai` ever
// becomes available; only "What it means" still depends on it.
export default function NewsPanel({ newsData, newsLoading, ai, aiLoading, ticker }) {
  // Defaults to Feed: it's the deterministic, always-available data and now
  // loads independently of the AI call — no reason to make the user wait on
  // (or lose access to) headlines while "What it means" is still thinking.
  const [tab, setTab] = useState('feed')

  const feed = newsData?.feed || []
  const feedNote = newsData?.reason || newsData?.note
  const inference = ai?.news?.inference || {}
  const inferenceNote = ai?.news?.note

  return (
    <div className="card">
      <div className="lbl">News &amp; financial signals</div>
      <div className="newstabs">
        <button className={'ntab' + (tab === 'feed' ? ' on' : '')} onClick={() => setTab('feed')}>Feed</button>
        <button className={'ntab' + (tab === 'means' ? ' on' : '')} onClick={() => setTab('means')}>What it means <SparkleIcon className="icon" /></button>
      </div>

      {tab === 'feed' && (
        newsLoading ? (
          <div className="scraping">
            <div className="spinner" />
            <div className="faint" style={{ fontSize: 13 }}>Gathering the news feed…</div>
          </div>
        ) : !newsData?.available ? (
          <div className="placeholder">{newsData?.reason || 'News feed unavailable.'}</div>
        ) : feed.length ? (
          feed.slice(0, 20).map((n, i) => {
            // A source URL isn't always available. Render those as a plain (non-link)
            // block instead of href="#" — a "#" link both goes nowhere useful and
            // mutates the URL hash, which doubles as this app's ticker route and would
            // otherwise silently kick the user back to the home screen.
            const Tag = n.url ? 'a' : 'div'
            const linkProps = n.url ? { href: n.url, target: '_blank', rel: 'noreferrer' } : {}
            return (
              <Tag className={'newsbox' + (n.url ? '' : ' newsbox-nolink')} key={i} {...linkProps}>
                <div className="newsbox-head">
                  <span className="newsbox-src">{n.source || 'source'}</span>
                  <span className="when">{n.datetime || ''}</span>
                </div>
                <div className="newsbox-title">{n.headline}</div>
                {n.summary && <div className="newsbox-sum">{n.summary}</div>}
              </Tag>
            )
          })
        ) : (
          <div className="placeholder">{feedNote || `No recent news returned for ${ticker}.`}</div>
        )
      )}

      {tab === 'means' && (
        aiLoading ? (
          <div className="scraping">
            <div className="spinner" />
            <div className="faint" style={{ fontSize: 13 }}>Reading the signals…</div>
          </div>
        ) : !ai?.available ? (
          <div className="placeholder">{ai?.reason || 'AI narration unavailable.'}</div>
        ) : (
          <div className="infer">
            <span className="tagline">Trade Craft's inference · evidence-based, not advice</span>
            <p style={{ marginTop: 8 }}>{inference.summary || inferenceNote || 'No news to interpret yet.'}</p>
            {inference.sources?.length > 0 && (
              <div className="faint" style={{ fontSize: 12, marginTop: 6 }}>Sources: {inference.sources.join(' · ')}</div>
            )}
          </div>
        )
      )}
    </div>
  )
}
