"""
Ask-Claude chat agent — conversational Q&A over ONE stock's research bundle.

Same north star as the analysis agent: it describes and teaches, never advises;
every claim leans on the exact numbers and the relevance-filtered evidence it is
given; when the data can't answer, it says so instead of guessing. The stock's
data context is rendered into the (cached) system prompt so multi-turn chat reuses
it cheaply; the conversation itself rides in `messages`.
"""
from __future__ import annotations

import json

from agents import llm

GUARDRAILS = """You are Trade101's study companion — a chat tutor for a beginning trader, discussing ONE stock they are researching.

You are given that stock's EXACT figures (deterministic, not to be recomputed or altered) and a set of news/filings that have ALREADY been relevance-filtered to this company. Ground every answer in that data.

Hard rules:
- Use the exact numbers provided; never invent or recompute a figure. If a number you'd need isn't in the data, say it isn't available.
- Cite what you lean on inline, briefly — e.g. "(RSI 62)", "(SMA50 vs SMA200)", or "(per the Reuters headline)". Prefer the provided evidence; don't reference outside facts as if sourced.
- Teach. Explain the *why* so the user learns to read it themselves, at a beginner-friendly level, concise (a few short paragraphs at most).
- You are NOT a financial advisor. NEVER say buy, sell, hold, or give a price target, and never predict profit. If asked "should I buy/sell?", explain that you don't give trading advice, then pivot to what the data shows and what they could learn to weigh.
- If the question is outside what the data can support (e.g. insider intent, guaranteed outcomes), say so plainly rather than speculate.
- Plain text, no markdown headers. Conversational."""


def _render_context(ticker, quote, indicators, news, filings, sourcing) -> str:
    q = {k: quote.get(k) for k in ("name", "price", "changePercent", "currency", "exchange")}
    news_compact = [
        {"headline": n.get("headline"), "source": n.get("source"),
         "date": n.get("datetime"), "category": n.get("category")}
        for n in (news or [])[:8]
    ]
    filings_compact = [{"form": f.get("form"), "date": f.get("date")} for f in (filings or [])[:5]]
    ctx = {
        "ticker": ticker, "quote": q, "indicators": indicators,
        "news": news_compact, "filings": filings_compact,
        "has_company_news": (sourcing or {}).get("has_company_news", bool(news)),
    }
    return (
        "The stock under discussion and its exact data (do not alter the numbers):\n\n"
        + json.dumps(ctx, indent=2)
    )


def answer(ticker, quote, indicators, news, filings, sourcing, history, question) -> dict:
    """Return {answer, sources}. Raises llm.MissingKeyError if no key set."""
    # System = stable guardrails + this ticker's data context. Stable across the
    # conversation, so it's the cached prefix; the Q&A turns vary and come after.
    system = GUARDRAILS + "\n\n" + _render_context(ticker, quote, indicators, news, filings, sourcing)

    messages = []
    for turn in (history or [])[-8:]:  # cap history to keep cost bounded
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question.strip()})

    text = llm.call_chat("TRADE101_ANALYSIS_KEY", system, messages, effort="medium", max_tokens=1200)

    sources = []
    for it in (news or []):
        if it.get("url"):
            sources.append({"label": it.get("headline") or it.get("source") or "News",
                            "source": it.get("source"), "url": it["url"]})
    return {"answer": text, "sources": sources}
