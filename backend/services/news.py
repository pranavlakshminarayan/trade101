"""
News + filings fetch — deterministic providers (no LLM).

- Finnhub free tier: ticker-tagged company news (headline, source, url, date).
- SEC EDGAR: recent official filings (10-K/10-Q/8-K) — keyless, US symbols.

The Research agent decides relevance/what to use; THIS module just fetches clean,
sourced items. Everything degrades gracefully: no key / provider down → empty
list + a note, never fabricated news.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta

import httpx

FINNHUB = "https://finnhub.io/api/v1"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
# SEC requires a descriptive User-Agent with contact info.
SEC_UA = {"User-Agent": "Trade101 research app (workspace.sonic@gmail.com)"}

_cik_cache: dict[str, str] = {}


def get_news(ticker: str, days: int = 30) -> tuple[list[dict], str | None]:
    """Provider-agnostic news fetch. Swap providers with TRADE101_NEWS_PROVIDER
    (default 'finnhub'); add 'firecrawl' etc. here later with zero agent changes."""
    provider = os.environ.get("TRADE101_NEWS_PROVIDER", "finnhub").lower()
    if provider == "finnhub":
        return get_company_news(ticker, days)
    # Future: elif provider == "firecrawl": return _firecrawl_news(ticker, days)
    return [], f"Unknown news provider '{provider}' (set TRADE101_NEWS_PROVIDER)."


def get_company_news(ticker: str, days: int = 30) -> tuple[list[dict], str | None]:
    """Recent company news via Finnhub. Returns (items, note)."""
    key = os.environ.get("TRADE101_NEWS_KEY")
    if not key:
        return [], "No Finnhub key set (TRADE101_NEWS_KEY) — news feed unavailable."
    to = datetime.utcnow().date()
    frm = to - timedelta(days=days)
    try:
        r = httpx.get(
            f"{FINNHUB}/company-news",
            params={"symbol": ticker.upper(), "from": frm.isoformat(), "to": to.isoformat(), "token": key},
            timeout=15,
        )
        r.raise_for_status()
        raw = r.json()
    except Exception as e:
        return [], f"News provider error: {e}"

    items = []
    for a in raw[:15]:
        items.append({
            "headline": a.get("headline"),
            "summary": a.get("summary"),
            "source": a.get("source"),
            "url": a.get("url"),
            "datetime": datetime.utcfromtimestamp(a["datetime"]).date().isoformat() if a.get("datetime") else None,
        })
    note = None if items else "No recent company news returned (Finnhub coverage is strongest for US symbols)."
    return items, note


def _cik_for(ticker: str) -> str | None:
    if ticker.upper() in _cik_cache:
        return _cik_cache[ticker.upper()]
    try:
        r = httpx.get(SEC_TICKERS, headers=SEC_UA, timeout=15)
        r.raise_for_status()
        for row in r.json().values():
            _cik_cache[row["ticker"].upper()] = str(row["cik_str"]).zfill(10)
    except Exception:
        return None
    return _cik_cache.get(ticker.upper())


def get_recent_filings(ticker: str, limit: int = 5) -> tuple[list[dict], str | None]:
    """Recent SEC filings (10-K/10-Q/8-K) via EDGAR. US symbols only. (items, note)."""
    cik = _cik_for(ticker)
    if not cik:
        return [], "No SEC filings (EDGAR covers US-listed companies only)."
    try:
        r = httpx.get(SEC_SUBMISSIONS.format(cik=cik), headers=SEC_UA, timeout=15)
        r.raise_for_status()
        recent = r.json()["filings"]["recent"]
    except Exception as e:
        return [], f"EDGAR error: {e}"

    wanted = {"10-K", "10-Q", "8-K"}
    out = []
    for form, date, acc, doc in zip(
        recent["form"], recent["filingDate"], recent["accessionNumber"], recent["primaryDocument"]
    ):
        if form in wanted:
            acc_nodash = acc.replace("-", "")
            out.append({
                "form": form,
                "date": date,
                "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{doc}",
            })
        if len(out) >= limit:
            break
    return out, (None if out else "No recent 10-K/10-Q/8-K filings found.")
