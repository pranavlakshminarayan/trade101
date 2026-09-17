"""
Orchestrator — coordinates one AI analysis run.

Gathers exact data (market + indicators) + sourced news/filings, hands them to
the Analysis agent, and assembles the narration bundle. Deterministic glue; the
only judgment is inside the agent.
"""
from __future__ import annotations

from agents import analysis, chat, llm
from services import cache, company, evidence, indicators, marketdata, news

# How long a finished /analyze result is reused before spending the Claude key
# again for the same ticker. Previously unbounded — every page reload, every
# new tab, every friend opening the shared link ran a fresh effort="high" call
# (docs/AUDIT.md finding M2), even though the frontend's OWN cache already
# proves a stock's read doesn't need to change minute-to-minute. 20 min is
# long enough that a normal research session (reload, tab close/reopen,
# revisiting a stock) doesn't re-spend, short enough that a genuinely fresh
# read is available again soon after.
ANALYZE_CACHE_TTL = 1200.0


def gather(ticker: str) -> dict | None:
    """Deterministic data bundle for a ticker — exact numbers + relevance-filtered
    evidence. No LLM. Shared by the analysis run and the Ask-Claude chat so both
    reason over the SAME sourced data (and we never fetch it twice). None if the
    symbol has no market data. Cached briefly (TTL) so chat turns reuse one
    identical bundle — stable numbers + a warm Claude prompt cache."""
    return cache.get_or_set(f"gather:{ticker.upper()}", lambda: _gather(ticker))


def _gather(ticker: str) -> dict | None:
    data = marketdata.get(ticker)
    if data is None:
        return None
    hist, quote = data
    ind = indicators.compute_indicators(hist)

    news_items, news_note = news.get_news(ticker, name=quote.get("name"))
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
    return {
        "quote": quote, "indicators": ind, "profile": profile,
        "news": kept_news, "news_note": news_note, "filings": filings,
        "fil_note": fil_note, "sourcing": sourcing,
    }


def news_bundle(ticker: str) -> dict | None:
    """Deterministic news bundle for a ticker — the SAME relevance-filtered
    feed `analyze()` uses, but with no LLM call at all. None if the symbol has
    no market data. Lets the News panel show real headlines immediately and
    independently of the paid AI call: previously the feed only ever reached
    the UI through /analyze's response, so no Claude key, an AI error, or the
    daily cap being hit meant NO headlines at all — deterministic data held
    hostage by the judgment layer (docs/AUDIT.md finding H3). Reuses the same
    cached `gather()` bundle, so calling this first doesn't cost a second
    fetch when /analyze runs afterward for the same ticker."""
    b = gather(ticker)
    if b is None:
        return None
    kept_news, sourcing = b["news"], b["sourcing"]
    news_note = b["news_note"]
    if sourcing["dropped"]:
        note_bits = [news_note] if news_note else []
        note_bits.append(
            f"{sourcing['dropped']} unrelated article(s) were filtered out."
        )
        news_note = " ".join(note_bits)
    return {
        "ticker": b["quote"]["symbol"],
        "feed": kept_news,
        "note": news_note,
        "sourcing": sourcing,
        "filings": b["filings"],
        "filings_note": b["fil_note"],
    }


def analyze(ticker: str) -> dict | None:
    """Full AI narration bundle for `ticker`, or None if the symbol has no data.
    Raises llm.MissingKeyError if no analysis key is configured. Cached for
    ANALYZE_CACHE_TTL — a raised exception is never cached (get_or_set only
    stores a value fn() actually returns), so a missing key or a transient AI
    error is retried on the very next call rather than sticking around."""
    return cache.get_or_set(f"analyze:{ticker.upper()}", lambda: _analyze(ticker),
                             ttl=ANALYZE_CACHE_TTL)


def _analyze(ticker: str) -> dict | None:
    b = gather(ticker)
    if b is None:
        return None
    quote, ind = b["quote"], b["indicators"]
    kept_news, filings, sourcing = b["news"], b["filings"], b["sourcing"]
    news_note, fil_note = b["news_note"], b["fil_note"]

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


def ask(ticker: str, question: str, history: list[dict] | None = None) -> dict | None:
    """Answer a user question about `ticker`, grounded in the same exact data +
    filtered evidence the analysis uses. None if the symbol has no data. Raises
    llm.MissingKeyError if no key is configured."""
    b = gather(ticker)
    if b is None:
        return None
    return chat.answer(
        ticker=b["quote"]["symbol"], quote=b["quote"], indicators=b["indicators"],
        news=b["news"], filings=b["filings"], sourcing=b["sourcing"],
        history=history or [], question=question,
    )
