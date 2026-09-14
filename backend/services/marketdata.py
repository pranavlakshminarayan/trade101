"""
Market data service — live prices, OHLCV, and quote via Yahoo Finance.

Deterministic (no LLM). Ticker-agnostic: works for ANY symbol Yahoo covers,
across US and the other target markets via exchange suffixes
(.SS/.SZ China, .T Japan, .KS Korea, .HK Hong Kong, .SI Singapore, .NS India).
Designed as a provider so other feeds (Stooq, Alpha Vantage, Finnhub) can be
added later behind the same interface.
"""
from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd
import yfinance as yf


def get(ticker: str, period: str = "1y", interval: str = "1d") -> Optional[Tuple[pd.DataFrame, dict]]:
    """
    Fetch (OHLCV DataFrame, quote dict) for `ticker`, or None if the symbol
    has no data (unknown/delisted). Prices are split/dividend-adjusted.
    """
    t = yf.Ticker(ticker)
    hist = t.history(period=period, interval=interval, auto_adjust=True)
    if hist is None or hist.empty:
        return None
    # Drop rows with a NaN OHLC value (some markets return holiday/partial bars,
    # e.g. 005930.KS) — a raw NaN can't be JSON-serialized and breaks /research.
    hist = hist.dropna(subset=["Open", "High", "Low", "Close"])
    if hist.empty:
        return None
    hist["Volume"] = hist["Volume"].fillna(0)
    return hist, _quote(t, hist, ticker)


def _name_from_search(ticker: str) -> str | None:
    """Last-resort company name via Yahoo's search endpoint, when yfinance.info
    has no name (occasionally the case for non-US symbols under rate limiting)."""
    try:
        from services import search
        for c in search.resolve(ticker, limit=5):
            if c.get("symbol", "").upper() == ticker.upper() and c.get("name"):
                return c["name"]
    except Exception:
        pass
    return None


def _quote(t: "yf.Ticker", hist: pd.DataFrame, ticker: str) -> dict:
    """Build a resilient quote dict; every field degrades gracefully to None."""
    last = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else None

    fi = {}
    try:
        fi = dict(t.fast_info)
    except Exception:
        fi = {}

    def g(*keys):
        for k in keys:
            v = fi.get(k)
            if v is not None:
                return v
        return None

    name, exchange, currency = None, None, None
    try:
        info = t.info
        # Prefer the properly-cased full name (longName) over the ALL-CAPS
        # shortName; this is what makes non-US listings show "Nintendo Co., Ltd."
        # instead of the bare ticker.
        name = info.get("longName") or info.get("shortName") or info.get("displayName")
        exchange = info.get("fullExchangeName") or info.get("exchange")
        currency = info.get("currency")
    except Exception:
        pass

    if not name:
        name = _name_from_search(ticker)

    price = float(g("last_price", "lastPrice") or last)
    change = (price - prev) if prev is not None else None
    change_pct = (change / prev * 100) if (prev and change is not None) else None

    return {
        "symbol": ticker.upper(),
        "name": name,
        "price": round(price, 2),
        "previousClose": round(prev, 2) if prev is not None else None,
        "change": round(change, 2) if change is not None else None,
        "changePercent": round(change_pct, 2) if change_pct is not None else None,
        "currency": currency or g("currency"),
        "marketCap": g("market_cap", "marketCap"),
        "exchange": exchange,
    }
