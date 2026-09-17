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
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

import httpx
import yfinance as yf

FINNHUB = "https://finnhub.io/api/v1"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"
SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
# SEC requires a descriptive User-Agent with contact info (fair-access policy).
# Configurable via TRADE101_SEC_CONTACT so a personal email never has to live in
# source — falls back to a generic, no-owner-identifying contact if unset.
SEC_UA = {"User-Agent": f"Trade Craft research app "
                        f"({os.environ.get('TRADE101_SEC_CONTACT', 'contact-not-configured@example.com')})"}

_cik_cache: dict[str, str] = {}

# When the primary provider returns fewer than this many items, supplement
# from a second provider instead of leaving the user with too few headlines
# to actually form a view (user-reported — "decisions aren't made by reading
# 2 or 3 headlines"). _MAX_MERGED caps the combined result.
_SUPPLEMENT_BELOW = 8
_MAX_MERGED = 25


def _merge_news(primary: list[dict], extra: list[dict], cap: int) -> list[dict]:
    """primary + extra, deduped by URL (falling back to headline text when a
    URL is missing), primary items kept first. Order beyond that is whatever
    each provider already returned (both are date-sorted upstream)."""
    seen = {(it.get("url") or it.get("headline") or "").strip().lower() for it in primary}
    out = list(primary)
    for it in extra:
        key = (it.get("url") or it.get("headline") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
        if len(out) >= cap:
            break
    return out


def get_news(ticker: str, days: int = 30, name: str | None = None) -> tuple[list[dict], str | None]:
    """Provider-agnostic news fetch. Swap providers with TRADE101_NEWS_PROVIDER
    (default 'finnhub'); add 'firecrawl' etc. here later with zero agent changes.

    Finnhub's free tier only covers US symbols, so it's tried first (richest
    metadata for the US names it does cover) and then backed up by two keyless,
    genuinely global sources: Google News (searches the open web by company
    name — real coverage for non-US markets, not just a US-tagged feed) and
    Yahoo Finance news as a final fallback. `name` (the company name, when the
    caller has it) makes the Google search meaningfully better than searching
    on the bare ticker, which reads as noise for most non-US symbols."""
    provider = os.environ.get("TRADE101_NEWS_PROVIDER", "finnhub").lower()
    if provider == "finnhub":
        items, note = get_company_news(ticker, days)
        if items:
            # A handful of headlines isn't enough to "connect the dots" on a
            # story (user-reported) — when the primary source is thin,
            # supplement with Google News rather than stopping at whatever
            # Finnhub happened to return, deduped by URL/headline so the same
            # story from two providers doesn't show twice.
            if len(items) < _SUPPLEMENT_BELOW:
                g_items, _ = _google_news(ticker, name, days)
                items = _merge_news(items, g_items, _MAX_MERGED)
            return items, note
        g_items, g_note = _google_news(ticker, name, days)
        if g_items:
            return g_items, None
        yf_items, yf_note = _yahoo_news(ticker, days)
        if yf_items:
            return yf_items, None
        return [], note or g_note or yf_note
    if provider == "yahoo":
        return _yahoo_news(ticker, days)
    if provider == "google":
        return _google_news(ticker, name, days)
    # Future: elif provider == "firecrawl": return _firecrawl_news(ticker, days)
    return [], f"Unknown news provider '{provider}' (set TRADE101_NEWS_PROVIDER)."


def _google_news(ticker: str, name: str | None, days: int = 30) -> tuple[list[dict], str | None]:
    """Keyless, global company news via Google News' public RSS search — real
    web coverage for any market (unlike Finnhub's US-only free tier), including
    local-language outlets for non-US listings. Searching by company name (when
    known) rather than the bare ticker is what makes this actually relevant."""
    query = name or ticker
    try:
        r = httpx.get(
            GOOGLE_NEWS_RSS,
            params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
            timeout=12,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Trade101/0.1"},
        )
        r.raise_for_status()
        root = ElementTree.fromstring(r.content)
    except Exception:
        return [], "Couldn't reach Google News just now — the read continues without it."

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        link = (item.findtext("link") or "").strip() or None
        pub = (item.findtext("pubDate") or "").strip()
        date_iso = None
        if pub:
            try:
                dt = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    continue
                date_iso = dt.date().isoformat()
            except ValueError:
                pass
        source_el = item.find("source")
        source = (source_el.text or "").strip() if source_el is not None else None
        # Google News titles are usually "Headline - Source"; the <source> tag
        # already carries the source cleanly, so trim the suffix when present.
        if source and title.endswith(f" - {source}"):
            title = title[: -(len(source) + 3)]
        items.append({
            "headline": title,
            "summary": None,
            "source": source or "Google News",
            "url": link,
            "datetime": date_iso,
        })
    note = None if items else f"No recent Google News results for {query}."
    return items[:_MAX_MERGED], note


def _yahoo_news(ticker: str, days: int = 30) -> tuple[list[dict], str | None]:
    """Keyless, global company news via Yahoo Finance (yfinance). Works for
    non-US listings where Finnhub's free tier 403s."""
    try:
        raw = yf.Ticker(ticker).news or []
    except Exception:
        return [], "Couldn't reach the news provider just now — the read continues without news."

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items = []
    for a in raw:
        c = a.get("content") or a  # yfinance nests the article under "content"
        title = c.get("title")
        if not title:
            continue
        url = ((c.get("clickThroughUrl") or {}).get("url")
               or (c.get("canonicalUrl") or {}).get("url"))
        pub = c.get("pubDate") or c.get("displayTime")
        date_iso = None
        if pub:
            try:
                dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                if dt < cutoff:
                    continue
                date_iso = dt.date().isoformat()
            except ValueError:
                pass
        items.append({
            "headline": title,
            "summary": c.get("summary") or c.get("description"),
            "source": (c.get("provider") or {}).get("displayName") or "Yahoo Finance",
            "url": url,
            "datetime": date_iso,
        })
    note = None if items else "No recent company news returned for this listing."
    return items[:_MAX_MERGED], note


def get_company_news(ticker: str, days: int = 30) -> tuple[list[dict], str | None]:
    """Recent company news via Finnhub. Returns (items, note)."""
    key = os.environ.get("TRADE101_NEWS_KEY")
    if not key:
        return [], "No Finnhub key set (TRADE101_NEWS_KEY) — news feed unavailable."
    to = datetime.now(timezone.utc).date()
    frm = to - timedelta(days=days)
    try:
        r = httpx.get(
            f"{FINNHUB}/company-news",
            params={"symbol": ticker.upper(), "from": frm.isoformat(), "to": to.isoformat(), "token": key},
            timeout=15,
        )
        if r.status_code in (401, 403):
            # Free-tier Finnhub 403s on non-US symbols; don't leak status URLs.
            return [], ("News for this listing isn't available on the current news plan "
                        "(Finnhub's free tier covers US symbols). The read continues without it.")
        r.raise_for_status()
        raw = r.json()
    except Exception:
        # Never surface the raw exception — its text can contain the request URL
        # (and thus the API key). Log-safe redaction happens server-side only.
        return [], "Couldn't reach the news provider just now — the read continues without news."

    items = []
    for a in raw[:_MAX_MERGED]:
        ts = a.get("datetime")
        items.append({
            "headline": a.get("headline"),
            "summary": a.get("summary"),
            "source": a.get("source"),
            "url": a.get("url"),
            "datetime": datetime.fromtimestamp(ts, timezone.utc).date().isoformat() if ts else None,
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
    except Exception:
        return [], "Couldn't reach SEC EDGAR just now — filings unavailable for this read."

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
