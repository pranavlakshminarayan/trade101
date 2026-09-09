"""
Orchestrator — coordinates one AI analysis run.

Gathers exact data (market + indicators) + sourced news/filings, hands them to
the Analysis agent, and assembles the narration bundle. Deterministic glue; the
only judgment is inside the agent.
"""
from __future__ import annotations

from agents import analysis, llm
from services import indicators, marketdata, news


def analyze(ticker: str) -> dict | None:
    """Full AI narration bundle for `ticker`, or None if the symbol has no data.
    Raises llm.MissingKeyError if no analysis key is configured."""
    data = marketdata.get(ticker)
    if data is None:
        return None
    hist, quote = data
    ind = indicators.compute_indicators(hist)

    news_items, news_note = news.get_news(ticker)
    filings, fil_note = news.get_recent_filings(ticker)

    result = analysis.run(quote["symbol"], quote, ind, news_items, filings)

    sources = []
    for it in news_items:
        if it.get("url"):
            sources.append({"label": it.get("source") or "News", "url": it["url"]})
    for f in filings:
        sources.append({"label": f"SEC {f['form']} · {f['date']}", "url": f["url"]})

    return {
        "ticker": quote["symbol"],
        "momentum": result.get("momentum"),
        "learning_note": result.get("learning_note"),
        "news": {"feed": news_items, "note": news_note, "inference": result.get("news_inference")},
        "filings": filings,
        "sources": sources,
        "meta": {
            "model": llm.MODEL,
            "parse_error": result.get("_parse_error", False),
            "notes": [n for n in (news_note, fil_note) if n],
        },
    }
