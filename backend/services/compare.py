"""
Comparison — several companies on the same axes. Deterministic, no LLM.

Two design rules, both load-bearing:

1. **Normalise before comparing.** Two stocks at $12 and $1,400 cannot be read
   on one price axis; rebasing both to 100 at the window's start turns the chart
   into a question about relative performance, which is the only thing a
   side-by-side chart can honestly answer.

2. **Never rank.** This module computes no score, no winner, no "better". A
   comparison shows how two businesses differ; deciding which one you want is a
   judgement about your own goals that no number here contains. Where two
   companies differ in kind rather than degree — a different sector, a different
   currency, wildly different size — that is surfaced as a reason the comparison
   is weaker, not smoothed over.
"""
from __future__ import annotations

import pandas as pd

from services import company as company_svc
from services import fundamentals as fund_svc
from services import indicators, marketdata

MAX_TICKERS = 4


def _rebase(hist: pd.DataFrame) -> list[dict]:
    """Rebase closes to 100 at the first bar — relative performance, not price."""
    closes = hist["Close"]
    base = float(closes.iloc[0])
    if not base:
        return []
    return [{"time": int(idx.timestamp()), "value": round(float(c) / base * 100, 2)}
            for idx, c in closes.items()]


def _perf(hist: pd.DataFrame) -> dict:
    closes = hist["Close"]
    first, last = float(closes.iloc[0]), float(closes.iloc[-1])
    peak, trough = float(closes.max()), float(closes.min())
    # Daily-return volatility, annualised — a comparability measure, not a forecast.
    rets = closes.pct_change().dropna()
    vol = float(rets.std() * (252 ** 0.5) * 100) if len(rets) > 1 else None
    # Worst peak-to-trough fall inside the window.
    running_max = closes.cummax()
    drawdown = float(((closes - running_max) / running_max).min() * 100)
    return {
        "changePercent": round((last - first) / first * 100, 2) if first else None,
        "high": round(peak, 2),
        "low": round(trough, 2),
        "annualisedVolatilityPercent": round(vol, 2) if vol is not None else None,
        "maxDrawdownPercent": round(drawdown, 2),
    }


def _comparability(entries: list[dict]) -> dict:
    """Say plainly where a side-by-side reading is weak.

    Comparing a US mega-cap to a small non-US listing on one chart is easy to do
    and easy to over-read; the differences that make it misleading are named
    here rather than left for the learner to notice.
    """
    warnings = []
    sectors = {e["profile"].get("sector") for e in entries if e["profile"].get("sector")}
    currencies = {e["quote"].get("currency") for e in entries if e["quote"].get("currency")}
    caps = [e["profile"].get("marketCap") for e in entries if e["profile"].get("marketCap")]
    bars = {e["bars"] for e in entries}

    if len(sectors) > 1:
        warnings.append(
            f"Different sectors ({', '.join(sorted(sectors))}). Sectors move on different "
            f"drivers and carry different normal valuations, so a like-for-like reading of "
            f"these multiples does not hold.")
    if len(currencies) > 1:
        warnings.append(
            f"Different currencies ({', '.join(sorted(currencies))}). The rebased chart "
            f"compares each stock in its OWN currency — part of any gap is the exchange "
            f"rate moving, not the business.")
    if caps and max(caps) and min(caps) and max(caps) / min(caps) > 20:
        warnings.append(
            "Market caps differ by more than 20x. Large and small companies have different "
            "volatility, liquidity and disclosure — a shared axis flatters neither.")
    if len(bars) > 1:
        warnings.append(
            "The companies have different amounts of history in this window (one may have "
            "listed later, or trade on a market with different holidays). The rebased lines "
            "do not start from the same number of sessions.")
    return {
        "level": "weak" if len(warnings) >= 2 else "partial" if warnings else "ok",
        "warnings": warnings,
    }


def compare(tickers: list[str], period: str = "1y", interval: str = "1d") -> dict:
    """Side-by-side bundle for 2–4 symbols. Unreachable symbols are reported,
    not silently dropped — a missing company would otherwise look like a
    deliberate exclusion."""
    clean, seen = [], set()
    for t in tickers:
        t = (t or "").strip().upper()
        if t and t not in seen:
            seen.add(t)
            clean.append(t)
    clean = clean[:MAX_TICKERS]

    entries, failed = [], []
    for t in clean:
        try:
            data = marketdata.get(t, period=period, interval=interval)
        except marketdata.ProviderError as e:
            failed.append({"ticker": t, "reason": str(e), "retryable": True})
            continue
        if data is None:
            failed.append({"ticker": t, "reason": f"No market data found for '{t}'.",
                           "retryable": False})
            continue
        hist, quote = data
        fund = fund_svc.get_fundamentals(t)
        # Sector/industry/beta live in the company profile; a failure there must
        # not lose the whole entry, so it degrades to an empty profile.
        try:
            prof = company_svc.get_profile(t)
        except Exception:
            prof = {}
        entries.append({
            "ticker": quote["symbol"],
            "name": quote.get("name"),
            "quote": quote,
            "series": _rebase(hist),
            "performance": _perf(hist),
            "indicators": indicators.compute_indicators(hist),
            "fundamentals": {
                "revenueChangePercent": (fund.get("revenue") or {}).get("changePercent"),
                "netIncomeChangePercent": (fund.get("netIncome") or {}).get("changePercent"),
                "cashFlowChangePercent": (fund.get("cashFlow") or {}).get("changePercent"),
                "valuation": fund.get("valuation"),
                "nextEarnings": (fund.get("earnings") or {}).get("nextDate"),
                "coverage": (fund.get("coverage") or {}).get("level"),
            },
            "profile": {
                "sector": prof.get("sector"),
                "industry": prof.get("industry"),
                "beta": prof.get("beta"),
                "marketCap": prof.get("marketCap") or (fund.get("valuation") or {}).get("marketCap"),
            },
            "bars": len(hist),
            "asOfMeta": marketdata.freshness(hist, interval),
        })

    return {
        "tickers": [e["ticker"] for e in entries],
        "period": period,
        "interval": interval,
        "entries": entries,
        "failed": failed,
        "comparability": _comparability(entries) if len(entries) > 1 else
                         {"level": "n/a", "warnings": []},
        "basis": "Each line is rebased to 100 at the start of the window, so the chart shows "
                 "relative performance over this period — not price, and not value.",
        "note": "This comparison deliberately produces no ranking and no score. It shows how "
                "these companies differ; which of those differences matter is a judgement "
                "about your own goals, and nothing here can make it for you.",
    }
