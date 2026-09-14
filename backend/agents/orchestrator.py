"""
Orchestrator — coordinates one AI analysis run.

Gathers exact data (market + indicators) + sourced news/filings, hands them to
the Analysis agent, and assembles the narration bundle. Deterministic glue; the
only judgment is inside the agent.
"""
from __future__ import annotations

from agents import analysis, llm
from services import company, evidence, indicators, marketdata, news


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

    # Deterministic relevance filter BEFORE the model sees anything: drop articles
    # that don't actually relate to the company, so the AI can't build a
    # company-specific claim out of unrelated news. (Phase 1.5 guardrail.)
    profile = company.get_profile(ticker)
    kept_news, sourcing = evidence.filter_news(
        news_items,
        name=quote.get("name"), ticker=quote["symbol"],
        sector=profile.get("sector"), industry=profile.get("industry"),
        peers=profile.get("peers"),
    )

    result = analysis.run(quote["symbol"], quote, ind, kept_news, filings, sourcing)

    # References list = only the evidence actually admitted to the analysis.
    sources = []
    for it in kept_news:
        if it.get("url"):
            sources.append({"label": it.get("headline") or it.get("source") or "News",
                            "source": it.get("source"), "url": it["url"],
                            "category": it.get("category")})
    for f in filings:
        sources.append({"label": f"SEC {f['form']} filing ({f['date']})",
                        "source": "SEC EDGAR", "url": f["url"], "category": "filing"})

    if sourcing["dropped"]:
        note_bits = [news_note] if news_note else []
        note_bits.append(
            f"{sourcing['dropped']} unrelated article(s) were filtered out before analysis."
        )
        news_note = " ".join(note_bits)

    return {
        "ticker": quote["symbol"],
        "momentum": result.get("momentum"),
        "learning_note": result.get("learning_note"),
        "news": {"feed": kept_news, "note": news_note,
                 "inference": result.get("news_inference"), "sourcing": sourcing},
        "filings": filings,
        "sources": sources,
        "meta": {
            "model": llm.MODEL,
            "parse_error": result.get("_parse_error", False),
            "notes": [n for n in (news_note, fil_note) if n],
        },
    }
