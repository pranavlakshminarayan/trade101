import { useEffect, useState } from 'react'
import { graph as fetchGraph } from '../api.js'

// Ecosystem graph — typed, sourced relationships.
//
// This replaces the old flat peer list, which read as a supply chain without
// ever claiming to be one. Here each edge shows its type, where it came from,
// and how confident that source is; and the types we have NO source for are
// listed explicitly, because an empty section and a missing section look the
// same to a reader and mean opposite things.

const TYPE_ORDER = ['index_constituent', 'competitor', 'supplier', 'customer', 'partner', 'investor']
const TYPE_LABEL = {
  supplier: 'Suppliers', customer: 'Customers', partner: 'Partners',
  competitor: 'Competitors / peers', investor: 'Investors',
  index_constituent: 'Fund holdings',
}
const CONF_CLASS = { high: 'conf-high', moderate: 'conf-mod', low: 'conf-low' }

function Edge({ e, onOpen }) {
  return (
    <div className="edge">
      <div className="edge-main">
        {e.targetIsPublic ? (
          <button className="jticker" onClick={() => onOpen(e.to)}>{e.to}</button>
        ) : (
          <span className="edge-private">{e.to} <span className="faint">(private)</span></span>
        )}
        {e.toName && <span className="faint edge-name">{e.toName}</span>}
        <span className={'edge-conf ' + (CONF_CLASS[e.confidence] || '')}
              title={e.confidenceMeaning}>
          {e.confidence} confidence
        </span>
        {e.materiality && e.materiality !== 'unknown' && (
          <span className="edge-mat">{e.materiality}</span>
        )}
      </div>
      <div className="edge-src faint">
        source: {e.sourceUrl
          ? <a href={e.sourceUrl} target="_blank" rel="noreferrer">{e.source}</a>
          : e.source}
        {e.date ? ` · ${e.date}` : ''}
      </div>
      {e.note && <div className="edge-note faint">{e.note}</div>}
    </div>
  )
}

export default function Graph({ ticker, onOpen }) {
  const [g, setG] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    setLoading(true); setG(null)
    fetchGraph(ticker).then((r) => { if (alive) { setG(r); setLoading(false) } })
    return () => { alive = false }
  }, [ticker])

  if (loading) {
    return (
      <div className="card">
        <div className="lbl">Ecosystem — who this company is connected to</div>
        <div className="scraping"><div className="spinner" />
          <div className="faint" style={{ fontSize: 13 }}>Building the relationship graph…</div></div>
      </div>
    )
  }

  if (!g) {
    return (
      <div className="card">
        <div className="lbl">Ecosystem</div>
        <div className="placeholder">
          Relationship data unavailable for {ticker}. The rest of the page is unaffected.
        </div>
      </div>
    )
  }

  const present = TYPE_ORDER.filter((t) => (g.byType[t] || []).length > 0)

  return (
    <div className="card">
      <div className="lbl">
        Ecosystem — {g.isFund ? 'what this fund holds' : 'who this company is connected to'}
      </div>

      <div className="notadvice">{g.caveat}</div>
      {g.fundCaveat && <div className="verdict differ">{g.fundCaveat}</div>}

      {present.map((t) => (
        <div key={t} className="edgegroup">
          <div className="edgegroup-head">
            {TYPE_LABEL[t]}
            <span className="faint">{g.legend.types[t]}</span>
          </div>
          {g.byType[t].map((e, i) => <Edge key={i} e={e} onOpen={onOpen} />)}
        </div>
      ))}

      {present.length === 0 && (
        <div className="placeholder">No relationships could be sourced for {ticker}.</div>
      )}

      {/* The absences, stated. This block is the point of the component. */}
      {g.unsourced?.types?.length > 0 && (
        <div className="unsourced-block">
          <div className="edgegroup-head">
            Not shown: {g.unsourced.types.map((t) => TYPE_LABEL[t]).join(', ')}
          </div>
          <p className="faint">{g.unsourced.reason}</p>
        </div>
      )}

      <div className="note faint">{g.meta?.note}</div>
    </div>
  )
}
