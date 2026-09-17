"""
Evidence relevance filter — deterministic, no LLM.

The problem this solves: ticker-tagged news feeds still return stories that have
nothing to do with the company (a live NVDA run pulled unrelated articles that
then coloured the AI narrative). The north star is "every AI claim is sourced"
and "make sense of data, not read labels" — so we must not hand the analysis
agent evidence it can't legitimately tie to the company.

This module classifies each fetched article by how it relates to the company and
drops the ones that relate not at all, BEFORE anything reaches the model. It is
plain string/keyword matching on purpose: the recommendation review was explicit
that relevance is a data-validation job, not a reason to add more AI calls.

Categories (most to least direct):
  company      — names the company or its ticker
  related      — names a known peer/competitor
  sector       — names the company's sector or industry
  irrelevant   — none of the above (excluded from the AI payload)
"""
from __future__ import annotations

import re

# Corporate-form and filler tokens that don't identify a company on their own.
_STOP = {
    "inc", "incorporated", "corp", "corporation", "co", "company", "companies",
    "ltd", "limited", "plc", "sa", "ag", "nv", "group", "holdings", "holding",
    "the", "and", "class", "common", "stock", "shares", "adr", "se", "spa",
    "technologies", "technology", "international", "industries", "enterprises",
}

_WORD_RE = re.compile(r"[a-z0-9]+")

# Company names that are also ordinary English words/common nouns — a bare
# token match on these is weak evidence (docs/AUDIT.md M3: "Apple cider"
# would match AAPL on the word "apple" alone). Not exhaustive; extend as new
# false positives are found. Multi-word or invented/rare-word names (Nvidia,
# Qualcomm, Reliance...) don't need this — the ambiguity is specific to
# single common-word names.
_AMBIGUOUS_NAME_WORDS = {
    "apple", "target", "block", "chime", "square", "shell", "oracle", "meta",
    "match", "gap", "chase", "duke", "constellation", "generac",
}
# A secondary signal that corroborates an otherwise-ambiguous common-word
# match: ordinary market/business vocabulary that a fruit-cider article
# wouldn't plausibly contain alongside "apple".
_FINANCE_CONTEXT = {
    "stock", "stocks", "shares", "nasdaq", "nyse", "ticker", "earnings",
    "ceo", "ipo", "investor", "investors", "market", "markets", "quarterly",
    "revenue", "profit", "dividend", "analyst", "analysts", "trading",
    "trade", "sec", "filing", "guidance", "forecast",
}


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall((text or "").lower()))


def _name_terms(name: str | None) -> set[str]:
    """Distinctive lowercased words from a company name (drops corporate filler)."""
    if not name:
        return set()
    terms = {w for w in _WORD_RE.findall(name.lower()) if w not in _STOP and len(w) > 2}
    return terms


def _base_ticker(ticker: str) -> str:
    """Strip an exchange suffix: '7974.T' -> '7974', 'AAPL' -> 'AAPL'."""
    return (ticker or "").split(".")[0].lower()


def classify(article: dict, *, name: str | None, ticker: str,
             sector: str | None = None, industry: str | None = None,
             peers: list[str] | None = None) -> str:
    """Return the relevance category for one article."""
    hay = _tokens(f"{article.get('headline', '')} {article.get('summary', '')}")
    if not hay:
        return "irrelevant"

    name_terms = _name_terms(name)
    tkr = _base_ticker(ticker)
    matched_name_terms = name_terms & hay
    ticker_hit = bool(tkr and len(tkr) > 1 and tkr in hay)
    # Company: any distinctive name word, or the ticker, appears — UNLESS
    # every matched name word is also an ordinary English word the company
    # name happens to share (docs/AUDIT.md M3: "Apple cider" would otherwise
    # match Apple Inc. on the bare word "apple"). In that case, require a
    # secondary corroborating signal — the ticker itself, or ordinary
    # market/business vocabulary nearby — before trusting the match. This
    # keeps recall intact for the common case (most company names aren't
    # dictionary words) while fixing the specific false-positive class.
    if matched_name_terms or ticker_hit:
        ambiguous_only = bool(matched_name_terms) and matched_name_terms <= _AMBIGUOUS_NAME_WORDS
        if not ambiguous_only or ticker_hit or (hay & _FINANCE_CONTEXT):
            return "company"

    peer_terms: set[str] = set()
    for p in peers or []:
        peer_terms |= _name_terms(p)
        peer_terms.add(_base_ticker(p))
    if peer_terms & hay:
        return "related"

    sector_terms = _name_terms(sector) | _name_terms(industry)
    if sector_terms & hay:
        return "sector"

    return "irrelevant"


def filter_news(articles: list[dict], *, name: str | None, ticker: str,
                sector: str | None = None, industry: str | None = None,
                peers: list[str] | None = None) -> tuple[list[dict], dict]:
    """
    Tag each article with `category` and return (kept, report).

    `kept` excludes irrelevant articles and is ordered company → related → sector.
    `report` summarises what happened so the UI/agent can be honest about sourcing:
      {kept, dropped, has_company_news, counts:{company,related,sector,irrelevant}}
    """
    order = {"company": 0, "related": 1, "sector": 2, "irrelevant": 3}
    counts = {"company": 0, "related": 0, "sector": 0, "irrelevant": 0}

    tagged = []
    for a in articles or []:
        cat = classify(a, name=name, ticker=ticker, sector=sector,
                       industry=industry, peers=peers)
        counts[cat] += 1
        tagged.append({**a, "category": cat})

    kept = sorted((a for a in tagged if a["category"] != "irrelevant"),
                  key=lambda a: order[a["category"]])
    report = {
        "kept": len(kept),
        "dropped": counts["irrelevant"],
        "has_company_news": counts["company"] > 0,
        "counts": counts,
    }
    return kept, report
