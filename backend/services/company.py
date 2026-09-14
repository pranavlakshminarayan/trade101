"""
Company profile / ecosystem — deterministic.

Sector, industry, beta, market cap from Yahoo; peer companies from Finnhub's
free peers endpoint. Beta is the "how it lives in the index/market" signal;
peers are the ecosystem. All real data, degrades gracefully.
"""
from __future__ import annotations

import os

import httpx
import yfinance as yf

FINNHUB = "https://finnhub.io/api/v1"


def _peers(ticker: str) -> list[str]:
    key = os.environ.get("TRADE101_NEWS_KEY")  # same Finnhub key as news
    if not key:
        return []
    try:
        r = httpx.get(f"{FINNHUB}/stock/peers", params={"symbol": ticker.upper(), "token": key}, timeout=12)
        r.raise_for_status()
        return [p for p in r.json() if p and p.upper() != ticker.upper()][:8]
    except Exception:
        return []


def get_profile(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = {}
    try:
        info = t.info
    except Exception:
        info = {}

    beta = info.get("beta")
    peers = _peers(ticker)
    is_us = "." not in ticker  # US symbols have no exchange suffix (e.g. AAPL vs 7974.T)

    # Explain the gaps rather than showing a blank panel. Coverage outside the US
    # is thinner: yfinance often has no beta, and Finnhub's peers endpoint is US-only.
    coverage = {}
    if beta is None:
        coverage["beta"] = (
            "Beta isn't published for this listing"
            + (" (common for non-US symbols)." if not is_us else ".")
        )
    if not peers:
        coverage["peers"] = (
            "Peer companies aren't available for this listing"
            + (" — the peers source currently covers US-listed symbols." if not is_us
               else ".")
        )

    return {
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "beta": beta,
        "marketCap": info.get("marketCap"),
        "exchange": info.get("fullExchangeName") or info.get("exchange"),
        "country": info.get("country"),
        "peers": peers,
        "summary": (info.get("longBusinessSummary") or "")[:360] or None,
        "coverage": coverage,
    }
