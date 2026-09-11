// Evidence coverage — how well-sourced this read actually is.
//
// The review's point: a learner must "see uncertainty when source coverage is
// poor." A confident-sounding paragraph built on one stale headline is the
// failure mode this component exists to prevent.

const LEVEL = {
  ok:   { cls: 'cov-ok',   icon: '●', word: 'Sourced' },
  thin: { cls: 'cov-thin', icon: '◐', word: 'Thin evidence' },
  none: { cls: 'cov-none', icon: '○', word: 'No company sources' },
}

export default function Coverage({ coverage, filter }) {
  if (!coverage) return null
  const l = LEVEL[coverage.level] || LEVEL.thin
  return (
    <div className={'coverage ' + l.cls}>
      <div className="cov-head">
        <span className="cov-icon" aria-hidden="true">{l.icon}</span>
        <b>{l.word}</b>
        <span className="faint">
          {coverage.news} article{coverage.news === 1 ? '' : 's'} · {coverage.filings} filing{coverage.filings === 1 ? '' : 's'}
        </span>
      </div>
      <p className="cov-note">{coverage.note}</p>
      {filter?.considered > 0 && (
        <details className="cov-filter">
          <summary>
            Screened {filter.considered} headline{filter.considered === 1 ? '' : 's'}, kept {filter.kept}
          </summary>
          <p className="faint">
            Only articles actually about this company are used. Dropped because they:
          </p>
          <ul>
            {filter.droppedExamples?.map((d, i) => (
              <li key={i}>
                <span className="faint">{d.why}</span>
                {d.headline ? <> — “{d.headline}”</> : null}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}
