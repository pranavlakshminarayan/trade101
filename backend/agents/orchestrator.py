"""
Orchestrator — coordinates one AI analysis run.

The shape of a run is deliberately: gather exact data → FILTER the evidence →
one bounded model call → VERIFY every claim against what was actually sent →
assemble. The two deterministic gates around the single call are what make the
sourcing contract checkable; see services/evidence.py.

Everything carries the same as-of timestamp, so the chart, the metrics and the
narrative can never quietly describe different moments in time.
"""
from __future__ import annotations

from agents import analysis, llm
from services import evidence, indicators, marketdata, news, storage


def analyze(ticker: str, period: str = "1y") -> dict | None:
    """Full AI narration bundle for `ticker`, or None if the symbol has no data.
    Raises llm.MissingKeyError if no analysis key is configured."""
    data = marketdata.get(ticker, period=period)
    if data is None:
        return None
    hist, quote = data
    ind = indicators.compute_indicators(hist)
    as_of = hist.index[-1].isoformat() if len(hist) else None

    raw_news, news_note = news.get_news(ticker)
    filings, fil_note = news.get_recent_filings(ticker)

    # GATE 1 — only evidence about this company reaches the model.
    kept_news, filter_report = evidence.select(raw_news, quote["symbol"], quote.get("name"))
    coverage = evidence.coverage(kept_news, filings, filter_report)

    catalog = evidence.build_catalog(ind, kept_news, filings)
    result = analysis.run(quote["symbol"], quote, ind, kept_news, filings,
                          catalog=catalog, as_of=as_of, timeframe=period, coverage=coverage)

    # GATE 2 — drop any claim citing something we never supplied.
    momentum = result.get("momentum") or {}
    inference = result.get("news_inference") or {}
    ev_ok, ev_bad = evidence.verify(momentum.get("evidence"), catalog)
    inf_ok, inf_bad = evidence.verify(inference.get("claims"), catalog)
    momentum["evidence"] = ev_ok
    inference["claims"] = inf_ok

    storage.save_history(quote["symbol"], quote.get("name"), momentum.get("lean"),
                         momentum.get("summary"), as_of)

    return {
        "ticker": quote["symbol"],
        "asOf": as_of,
        "timeframe": period,
        "momentum": momentum,
        "learning_note": result.get("learning_note"),
        "news": {"feed": kept_news, "note": news_note, "inference": inference},
        "filings": filings,
        "coverage": coverage,
        "evidenceFilter": filter_report,
        "sources": catalog,
        "meta": {
            "model": llm.MODEL,
            "parse_error": result.get("_parse_error", False),
            # Claims the model made that we could not trace — shown, not hidden.
            "unsupportedClaims": ev_bad + inf_bad,
            "notes": [n for n in (news_note, fil_note) if n],
        },
    }
