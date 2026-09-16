"""
Symbol search — resolve a company NAME (or partial ticker) to candidate symbols
via Yahoo's search endpoint. Keyless, multi-market. Deterministic.

Yahoo returns every listing that matches a name — the company's real primary
listing AND its OTC pink-sheet ADR, Canadian CDR, and secondary European dealer
lines, all mixed together with no indication of which is "the" stock. Left as
Yahoo orders them, the picker regularly puts a thin OTC ADR or a preferred-share
line ABOVE the actual company (docs/AUDIT.md finding H2 — e.g. "nintendo" put
the OTC line NTDOY above the real Tokyo listing 7974.T). `resolve()` scores and
sorts candidates by listing quality using signals Yahoo's response does carry
(exchange code, name suffixes) so the primary/major listing comes first and
thin secondary lines are pushed down and labeled, never silently promoted.
"""
from __future__ import annotations

import re
import time

import httpx

YAHOO_SEARCH = "https://query2.finance.yahoo.com/v1/finance/search"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Trade101/0.1"}

# Yahoo's exchange code for US pink-sheet / grey-market OTC listings — thin,
# wide-spread ADRs of foreign companies. Real, but never the listing you want
# by default.
_OTC_EXCHANGES = {"PNK", "OTC", "PINK", "GREY", "OOTC"}
# A lone "R" suffix (heavily space-padded in Yahoo's data) marks a German
# regulated-market dealer line — a secondary quote for a listing whose primary
# market is elsewhere, not a distinct company.
_SECONDARY_SUFFIX_RE = re.compile(r"\s{2,}R$")
_PREF_RE = re.compile(r"\(\s*1P\s*\)|\bPFD\b|\bPREF(?:ERRED)?\b", re.IGNORECASE)


def _listing_tier(symbol: str, name: str, exchange_code: str) -> tuple[int, str | None]:
    """Score a candidate's listing quality. Lower tier = better/more primary.
    Returns (tier, badge) — badge is a short label for non-primary lines, or
    None for an ordinary primary/major listing (no badge needed)."""
    exch = (exchange_code or "").upper()
    sym_u = (symbol or "").upper()
    name_u = (name or "").upper()

    if exch in _OTC_EXCHANGES:
        return 3, "OTC"
    if "CDR" in name_u or sym_u.endswith(".NE"):
        return 3, "CDR"
    if _PREF_RE.search(name_u):
        return 2, "Pref"
    if _SECONDARY_SUFFIX_RE.search(name or ""):
        return 2, "Secondary"
    return 0, None


def resolve(query: str, limit: int = 6) -> list[dict]:
    """Return candidate symbols for a name/ticker query, best (most primary)
    listing first — never just Yahoo's raw, unranked order."""
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
    for i, q in enumerate(quotes):
        if q.get("quoteType") not in ("EQUITY", "ETF"):
            continue
        sym = q.get("symbol")
        if not sym:
            continue
        name = q.get("shortname") or q.get("longname") or sym
        exch = q.get("exchDisp") or q.get("exchange")
        tier, badge = _listing_tier(sym, name, q.get("exchange"))
        out.append({
            "symbol": sym,
            "name": name.strip(),
            "exchange": exch,
            "type": q.get("quoteType"),
            "listingBadge": badge,   # "OTC" | "CDR" | "Pref" | "Secondary" | None
            "_tier": tier, "_i": i,  # sort keys only, stripped below
        })

    # Stable within a tier (Yahoo's own relevance order), primary listings first.
    out.sort(key=lambda c: (c["_tier"], c["_i"]))
    for c in out:
        del c["_tier"], c["_i"]
    return out
