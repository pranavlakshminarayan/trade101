"""
Analysis agent — the sense-making engine.

Takes the EXACT numbers, the FILTERED evidence, and the as-of timestamp they all
share, and produces an integrated understanding: what the signals mean together,
and why, explained so the learner can do the read themselves next time.

Two things are enforced outside this file and are not left to the prompt:
services/evidence.py decides what evidence the model may see, and checks
afterwards that every claim cites something we actually supplied. The prompt
asks for citation IDs precisely so that check can be mechanical.
"""
from __future__ import annotations

import json

from agents import llm

SYSTEM = """You are the analysis engine of Trade101, a hands-on LEARNING tool for a beginning trader.

Your job is to EXTRACT MEANING from the data, not read labels back. Anyone can see "RSI is 56". Your value is synthesis: what do the signals mean TOGETHER, and why — explained so the user learns to read it themselves.

Hard rules:
- Interpret signals in combination (price vs moving averages, RSI, MACD, volume, news). Explain the COMBINED picture and the reasoning.
- Every claim must cite an id from the EVIDENCE CATALOG you are given, in the "source" field (e.g. "ind:rsi14", "news:2", "filing:0"). Use the id EXACTLY as written. A claim you cannot attribute to a catalog id must not be made at all.
- NEVER invent a number or a fact. The numbers provided are exact — use them; do not recompute or alter them.
- Everything you say describes the data AS OF the timestamp given. Do not imply knowledge of anything after it, and do not speak about "today" or "now".
- Give a momentum LEAN (bullish / bearish / neutral / mixed) with a CONFIDENCE (low / moderate / high). Judge confidence on the EVIDENCE COVERAGE as well as the signals: thin or absent news coverage means low confidence about anything news-related, and you should say so plainly.
- If the signals conflict, say so — a mixed read that explains the conflict is more useful than a false clean answer.
- TEACH: include a short note that helps the user understand the read.
- You are NOT a financial advisor. NEVER say buy, sell, hold, or give a price target, and never predict profit. Describe and explain only.

Return ONLY valid JSON, no prose outside it, matching exactly:
{
  "momentum": {
    "lean": "bullish|bearish|neutral|mixed",
    "confidence": "low|moderate|high",
    "summary": "2-3 sentence synthesis of the overall picture",
    "evidence": [{"point": "one specific observation", "source": "catalog id, e.g. ind:rsi14"}]
  },
  "news_inference": {
    "summary": "how the sourced news + context may affect this stock, reasoned (or state plainly if there is little or no relevant news)",
    "claims": [{"point": "one specific inference", "source": "catalog id, e.g. news:1"}]
  },
  "learning_note": "one short paragraph teaching the user how to read this combination of signals"
}"""


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


def run(ticker: str, quote: dict, indicators: dict, news_items: list, filings: list,
        catalog: list[dict], as_of: str | None = None, timeframe: str = "1y",
        coverage: dict | None = None) -> dict:
    """Produce the analysis bundle. Raises llm.MissingKeyError if no key is set."""
    payload = {
        "ticker": ticker,
        "asOf": as_of,
        "timeframe": timeframe,
        "quote": {k: quote.get(k) for k in ("name", "price", "changePercent", "currency", "exchange")},
        "indicators": indicators,
        "evidenceCoverage": coverage,
        "evidenceCatalog": catalog,
    }
    user = (
        f"Analyze this stock for a learner, as of {as_of or 'the latest available bar'} "
        f"over the {timeframe} window. The numbers are exact — do not change them. "
        f"Cite only ids from evidenceCatalog.\n\n"
        + json.dumps(payload, indent=2)
        + "\n\nReturn only the JSON object described in your instructions."
    )
    text = llm.call("analysis", SYSTEM, user, ticker=ticker, effort="high", max_tokens=4000)
    try:
        return _extract_json(text)
    except (json.JSONDecodeError, ValueError):
        # Never fabricate — surface the failure honestly.
        return {
            "momentum": {"lean": "mixed", "confidence": "low",
                         "summary": "The analysis could not be parsed this time; the market data "
                                    "and indicators shown are still exact.",
                         "evidence": []},
            "news_inference": {"summary": "", "claims": []},
            "learning_note": "",
            "_parse_error": True,
        }
