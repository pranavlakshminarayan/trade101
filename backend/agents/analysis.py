"""
Analysis agent — the sense-making engine.

Takes the EXACT numbers (indicators) + sourced news + filings and produces an
integrated *understanding*: it synthesizes the signals (not restates them),
reads momentum with a confidence level, connects the news to the price action,
and teaches the reasoning. Grounded and sourced; never buy/sell advice.
"""
from __future__ import annotations

import json

from agents import llm

SYSTEM = """You are the analysis engine of Trade101, a hands-on LEARNING tool for a beginning trader.

Your job is to EXTRACT MEANING from the data, not read labels back. Anyone can see "RSI is 56". Your value is synthesis: what do the signals mean TOGETHER, and why — explained so the user learns to read it themselves.

Hard rules:
- Interpret signals in combination (price vs moving averages, RSI, MACD, volume, news). Explain the COMBINED picture and the reasoning.
- Ground every statement in the data you are given. Cite the source of each point (an indicator name, a news source, or a filing). NEVER invent a number or a fact. The numbers provided are exact — use them; do not recompute or alter them.
- LABEL every evidence point with a "type": "fact" = directly stated by a number or a sourced headline/filing; "interpretation" = your reasoning built on those facts; "unknown" = something the data can't establish. Be honest — most synthesis is interpretation, not fact.
- The news you receive has ALREADY been relevance-filtered. A "sourcing" object tells you how much company-specific news exists. If has_company_news is false, you MUST NOT assert a company-specific catalyst or explain the price with company news — say plainly that no company-specific news was available and lower confidence accordingly.
- Give a momentum LEAN (bullish / bearish / neutral / mixed) with a CONFIDENCE (low / moderate / high). If signals conflict or evidence is thin, say so and lower confidence.
- Connect the news to the tape only using the provided items: how might the sourced items affect this stock, in light of the price/indicator picture?
- TEACH: include a short note that helps the user understand the read.
- You are NOT a financial advisor. NEVER say buy, sell, hold, or give a price target, and never predict profit. Describe and explain only.

Return ONLY valid JSON, no prose outside it, matching exactly:
{
  "momentum": {
    "lean": "bullish|bearish|neutral|mixed",
    "confidence": "low|moderate|high",
    "summary": "2-3 sentence synthesis of the overall picture",
    "evidence": [{"point": "one specific observation", "source": "indicator/news/filing it comes from", "type": "fact|interpretation|unknown"}]
  },
  "news_inference": {
    "summary": "how the sourced news + context may affect the stock, reasoned (or state plainly if there is little or no company-specific news)",
    "sources": ["source names/urls referenced"]
  },
  "learning_note": "one short paragraph teaching the user how to read this combination of signals"
}

Worked example of the evidence labeling you must produce (illustrative — do NOT reuse these numbers; always use the exact data you are given):
- {"point": "Price 190.42 is above the 50-day SMA (182.10) and 200-day SMA (171.35)", "source": "indicator: SMA50/SMA200", "type": "fact"} — a fact: it restates exact numbers you were given.
- {"point": "Price holding above both moving averages points to an intact medium-term uptrend", "source": "interpretation", "type": "interpretation"} — an interpretation: reasoning built on the facts, not itself a number or a headline.
- {"point": "Whether the earnings guidance was raised is not in the provided data", "source": "unknown", "type": "unknown"} — unknown: the data cannot establish it, so you neither assert nor deny it.

Rules for the labels: mark "fact" ONLY when a provided number or a sourced headline/filing states it directly; mark "interpretation" for your synthesis; mark "unknown" when the data is silent. Never upgrade an interpretation to a fact to sound more confident, and never invent a source to justify a label. When company-specific news is absent, prefer fewer, well-grounded points over speculation."""


def _extract_json(text: str) -> dict:
    """Pull the JSON object out of the model response, tolerating code fences."""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1]
        if s.startswith("json"):
            s = s[4:]
    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end != -1:
        s = s[start:end + 1]
    return json.loads(s)


_VALID_TYPES = {"fact", "interpretation", "unknown"}


def _citation_guard(result: dict, has_news: bool) -> dict:
    """Enforce the sourcing contract: drop evidence points with no source, and
    normalise the fact/interpretation/unknown label; flag an unsourced news
    inference. Never fabricates — only prunes/annotates."""
    mom = result.get("momentum", {}) or {}
    ev = []
    for e in mom.get("evidence", []):
        if isinstance(e, dict) and e.get("source"):
            t = str(e.get("type", "")).lower()
            e["type"] = t if t in _VALID_TYPES else "interpretation"
            ev.append(e)
    mom["evidence"] = ev
    result["momentum"] = mom

    inf = result.get("news_inference", {}) or {}
    if has_news and not inf.get("sources"):
        inf["summary"] = (inf.get("summary", "") + " [note: sources not cited]").strip()
    result["news_inference"] = inf
    return result


def run(ticker: str, quote: dict, indicators: dict, news_items: list, filings: list,
        sourcing: dict | None = None) -> dict:
    """Produce the analysis bundle. Raises llm.MissingKeyError if no key set.

    `news_items` is already relevance-filtered; `sourcing` reports how much
    company-specific evidence exists so the agent can be honest about it."""
    payload = {
        "ticker": ticker,
        "quote": {k: quote.get(k) for k in ("name", "price", "changePercent", "currency", "exchange")},
        "indicators": indicators,
        "news": news_items[:10],
        "filings": filings[:5],
        "sourcing": sourcing or {"has_company_news": bool(news_items)},
    }
    user = (
        "Analyze this stock for a learner. Data (numbers are exact, do not change them):\n\n"
        + json.dumps(payload, indent=2)
        + "\n\nReturn only the JSON object described in your instructions."
    )
    text = llm.call("TRADE101_ANALYSIS_KEY", SYSTEM, user, effort="high", max_tokens=4000)
    try:
        result = _extract_json(text)
    except (json.JSONDecodeError, ValueError):
        # Never fabricate — surface the failure honestly.
        return {
            "momentum": {"lean": "mixed", "confidence": "low",
                         "summary": "The analysis could not be parsed this time; the raw data above is still exact.",
                         "evidence": []},
            "news_inference": {"summary": "", "sources": []},
            "learning_note": "",
            "_parse_error": True,
        }
    return _citation_guard(result, has_news=bool(news_items))
