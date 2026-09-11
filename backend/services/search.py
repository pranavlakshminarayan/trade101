"""
Symbol search — resolve a company NAME (or partial ticker) to candidate symbols
via Yahoo's search endpoint. Keyless, multi-market. Deterministic.
"""
from __future__ import annotations

import time

import httpx

from services import cache

YAHOO_SEARCH = "https://query2.finance.yahoo.com/v1/finance/search"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Trade101/0.1"}


def resolve(query: str, limit: int = 6) -> list[dict]:
    """Return candidate symbols for a name/ticker query, best match first."""
    result, _ = cache.get_or_fetch("search", f"{query.strip().lower()}:{limit}",
                                   lambda: _fetch(query, limit))
    return result


def _fetch(query: str, limit: int) -> list[dict]:
    quotes = []
    for attempt in range(2):  # one retry — Yahoo throttles bursts
        try:
            r = httpx.get(
                YAHOO_SEARCH,
                params={"q": query, "quotesCount": limit, "newsCount": 0, "listsCount": 0},
                headers=UA,
                timeout=12,
            )
            r.raise_for_status()
            quotes = r.json().get("quotes", [])
            if quotes:
                break
        except Exception:
            if attempt == 1:
                return []
            time.sleep(0.4)

    out = []
    for q in quotes:
        if q.get("quoteType") not in ("EQUITY", "ETF"):
            continue
        sym = q.get("symbol")
        if not sym:
            continue
        out.append({
            "symbol": sym,
            "name": q.get("shortname") or q.get("longname") or sym,
            "exchange": q.get("exchDisp") or q.get("exchange"),
            "type": q.get("quoteType"),
        })
    return out
