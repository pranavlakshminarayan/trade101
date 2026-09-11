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

PROVIDER = "yahoo"  # TRADE101_MARKET_DATA_PROVIDER selects this adapter

import pandas as pd
import yfinance as yf

from services import cache


def get(ticker: str, period: str = "1y", interval: str = "1d") -> Optional[Tuple[pd.DataFrame, dict]]:
    """
    Fetch (OHLCV DataFrame, quote dict) for `ticker`, or None if the symbol
    has no data (unknown/delisted). Prices are split/dividend-adjusted.
    Served from the TTL cache when fresh — see get_with_meta for the fetch time.
    """
    result, _ = get_with_meta(ticker, period, interval)
    return result


def get_with_meta(ticker: str, period: str = "1y", interval: str = "1d"):
    """As get(), plus cache metadata saying when this data was actually fetched."""
    def fetch():
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval, auto_adjust=True)
        if hist is None or hist.empty:
            return None
        return hist, _quote(t, hist, ticker)

    return cache.get_or_fetch("history", f"{ticker.upper()}:{period}:{interval}", fetch)


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
        name = info.get("shortName") or info.get("longName")
        exchange = info.get("fullExchangeName") or info.get("exchange")
        currency = info.get("currency")
    except Exception:
        pass

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


# Roughly how long a bar of each interval should be the newest one before the
# feed looks stale rather than merely closed. Generous: a long weekend plus a
# public holiday is normal, not a fault.
_STALE_AFTER_SECONDS = {
    "1m": 30 * 60, "2m": 60 * 60, "5m": 2 * 3600, "15m": 4 * 3600,
    "30m": 6 * 3600, "60m": 12 * 3600, "1h": 12 * 3600,
    "1d": 5 * 86400, "1wk": 14 * 86400, "1mo": 45 * 86400,
}


def freshness(hist: pd.DataFrame, interval: str = "1d") -> dict:
    """Describe how current the data is, in words the UI can show verbatim.

    Trade101 must always be able to say WHEN a number was true; a closed market
    and a broken feed look identical on a chart, so they are named differently
    here.
    """
    if hist is None or hist.empty:
        return {"asOf": None, "ageSeconds": None, "stale": True,
                "note": "No bars returned — nothing to date."}

    last = hist.index[-1]
    now = pd.Timestamp.now(tz=last.tz) if last.tz is not None else pd.Timestamp.now()
    age = max(0, int((now - last).total_seconds()))
    limit = _STALE_AFTER_SECONDS.get(interval, 5 * 86400)
    stale = age > limit

    if stale:
        note = (f"Newest bar is {age // 3600}h old, beyond the ~{limit // 3600}h expected for "
                f"{interval} bars. The market may be closed for an extended period, or the "
                f"feed may be behind — treat this as a snapshot, not a live price.")
    else:
        note = f"Newest {interval} bar is from {last.isoformat()}."
    return {"asOf": last.isoformat(), "ageSeconds": age, "stale": stale, "note": note}
