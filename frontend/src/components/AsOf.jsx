// The shared timestamp line. Every panel that states something about the stock
// renders this, from the SAME meta object, so the chart, the metrics, the
// patterns and the AI read can never quietly describe different moments.
//
// A stale feed and a closed market look identical on a chart — so they are
// labelled differently here.

function fmt(iso) {
  if (!iso) return 'unknown'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function asOfText(meta) {
  if (!meta?.asOf) return 'Data timestamp unavailable'
  return `as of ${fmt(meta.asOf)}`
}

export default function AsOf({ meta, timeframe, label }) {
  if (!meta) return null
  const stale = meta.stale
  return (
    <div className={'asof' + (stale ? ' asof-stale' : '')} title={meta.note || ''}>
      <span className="asof-dot" aria-hidden="true" />
      <span>
        {label ? <b>{label} </b> : null}
        {timeframe ? <>{timeframe} window · </> : null}
        {asOfText(meta)}
        {meta.delayed ? ' · delayed ~15m' : ''}
      </span>
      {stale && <span className="asof-flag">stale</span>}
    </div>
  )
}

// Provider + cache badge: which source answered, and how old that answer is.
export function ProviderBadge({ meta }) {
  if (!meta) return null
  const c = meta.cache
  const age = c?.ageSeconds
  return (
    <span className="provbadge" title={c ? `Fetched ${fmt(c.fetchedAt)} · ${c.backend} cache` : ''}>
      {meta.source || meta.provider || 'source'}
      {c?.cached ? ` · cached ${age < 60 ? `${age}s` : `${Math.round(age / 60)}m`} ago` : ' · live fetch'}
    </span>
  )
}
