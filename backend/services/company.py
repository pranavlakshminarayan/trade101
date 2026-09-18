"""
Company profile / ecosystem — deterministic.

Sector, industry, beta, market cap from Yahoo; peer companies from Finnhub's
free peers endpoint. Beta is the "how it lives in the index/market" signal;
peers are the ecosystem. All real data, degrades gracefully.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import httpx
import numpy as np
import yfinance as yf

from services import cache
from services.net import with_timeout, with_retry

FINNHUB = "https://finnhub.io/api/v1"

# Exchange suffix → the market index a stock's beta is measured against. This is
# what lets us compute beta for non-US listings, where yfinance/Finnhub give none.
# Keyed by the ".XX" suffix; US symbols (no suffix) fall through to the S&P 500.
_INDEX_BY_SUFFIX = {
    "T": ("^N225", "Nikkei 225"), "KS": ("^KS11", "KOSPI"), "KQ": ("^KQ11", "KOSDAQ"),
    "HK": ("^HSI", "Hang Seng"), "SS": ("000001.SS", "SSE Composite"),
    "SZ": ("399001.SZ", "SZSE Component"), "SI": ("^STI", "Straits Times"),
    "NS": ("^NSEI", "Nifty 50"), "BO": ("^BSESN", "BSE Sensex"),
    "DE": ("^GDAXI", "DAX"), "L": ("^FTSE", "FTSE 100"), "PA": ("^FCHI", "CAC 40"),
    "TO": ("^GSPTSE", "S&P/TSX"), "AX": ("^AXJO", "S&P/ASX 200"),
    "SW": ("^SSMI", "SMI"), "AS": ("^AEX", "AEX"), "MI": ("FTSEMIB.MI", "FTSE MIB"),
}
_US_INDEX = ("^GSPC", "S&P 500")


def _index_for(ticker: str) -> tuple[str, str]:
    parts = ticker.upper().rsplit(".", 1)
    if len(parts) == 2 and parts[1] in _INDEX_BY_SUFFIX:
        return _INDEX_BY_SUFFIX[parts[1]]
    return _US_INDEX


def _computed_beta(ticker: str) -> tuple[float | None, str | None]:
    """Beta from ~1y of daily returns vs the stock's regional market index —
    deterministic, so non-US listings get a real beta instead of null.
    Returns (beta, index_name) or (None, None) if the data is insufficient."""
    idx_sym, idx_name = _index_for(ticker)
    try:
        stock = with_timeout(
            lambda: yf.Ticker(ticker).history(period="1y", interval="1d", auto_adjust=True)["Close"], timeout=12)
        index = with_timeout(
            lambda: yf.Ticker(idx_sym).history(period="1y", interval="1d", auto_adjust=True)["Close"], timeout=12)
    except Exception:
        return None, None
    sr = stock.pct_change().dropna()
    ir = index.pct_change().dropna()
    df = np.stack([sr.align(ir, join="inner")[0].to_numpy(),
                   sr.align(ir, join="inner")[1].to_numpy()])
    if df.shape[1] < 60:  # need a meaningful sample
        return None, None
    var = np.var(df[1])
    if var == 0:
        return None, None
    beta = float(np.cov(df[0], df[1])[0][1] / var)
    return round(beta, 3), idx_name


def _truncate_summary(text: str, limit: int = 360) -> str | None:
    """Cut at the last word boundary within `limit`, never mid-word/mid-sentence,
    and only append '…' when the text was actually cut — a hard character-count
    slice used to lop a business summary off mid-word (e.g. "solutions an…")
    and the frontend appended '…' unconditionally, even to a summary that
    already ended cleanly on its own."""
    text = (text or "").strip()
    if not text:
        return None
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(".,;: ")
    return cut + "…"


def _peer_names(symbols: list[str]) -> dict[str, str]:
    """Company name for each peer symbol, fetched in parallel (yfinance has no
    keyless batch-quote endpoint left — Yahoo's v7/finance/quote now 401s
    without a session/crumb — so this is one .info lookup per symbol, run
    concurrently rather than sequentially so 8 peers costs ~1 request's worth
    of wall-clock time, not 8x). `peers` itself stays a plain list of ticker
    strings (services/evidence.py matches news against those directly) — this
    is an ADDITIONAL lookup, only used so the ecosystem graph can show a real
    name on hover instead of just the bare ticker."""
    if not symbols:
        return {}

    def _one(sym: str) -> tuple[str, str | None]:
        try:
            info = with_retry(lambda: yf.Ticker(sym).info, timeout=10)
            return sym, (info.get("shortName") or info.get("longName"))
        except Exception:
            return sym, None

    with ThreadPoolExecutor(max_workers=min(8, len(symbols))) as ex:
        results = list(ex.map(_one, symbols))
    return {sym: name for sym, name in results if name}


def _dedupe(ticker: str, symbols: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for p in symbols:
        if not p or p.upper() == ticker.upper() or p.upper() in seen:
            continue
        seen.add(p.upper())
        out.append(p)
    return out[:8]


def _finnhub_peers(ticker: str) -> list[str]:
    key = os.environ.get("TRADE101_NEWS_KEY")  # same Finnhub key as news
    if not key:
        return []
    try:
        r = httpx.get(f"{FINNHUB}/stock/peers", params={"symbol": ticker.upper(), "token": key}, timeout=12)
        r.raise_for_status()
        # Finnhub's own peers list can contain duplicates (confirmed live on
        # QCOM: "MRVL" appears twice) — dedupe case-insensitively, preserving
        # order, or the ecosystem graph renders the same company as two nodes.
        return _dedupe(ticker, r.json())
    except Exception:
        return []


def _yahoo_related(ticker: str) -> list[str]:
    """Fallback for when Finnhub has nothing — its free peers endpoint is
    US-listed-only, which left every non-US stock (Reliance, Toshiba, ...)
    with an empty ecosystem panel (user-reported). Yahoo Finance's own public
    "people also watch" endpoint is keyless and genuinely global. It's a
    DIFFERENT signal from Finnhub's peers — co-viewed by other investors,
    not necessarily same-industry competitors (verified: RELIANCE.NS returns
    HDFCBANK/TCS/ICICIBANK — major Indian large-caps investors also track,
    not oil & gas competitors) — so callers must track which source was used
    (see `peersSource`) and the UI should label it differently, not present
    it as if it were the same kind of "peer" Finnhub returns."""
    try:
        r = httpx.get(
            f"https://query1.finance.yahoo.com/v6/finance/recommendationsbysymbol/{ticker.upper()}",
            timeout=12, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Trade101/0.1"},
        )
        r.raise_for_status()
        result = (r.json().get("finance", {}).get("result") or [{}])[0]
        symbols = [s.get("symbol") for s in (result.get("recommendedSymbols") or [])]
        return _dedupe(ticker, symbols)
    except Exception:
        return []


def _peers(ticker: str) -> tuple[list[str], str | None]:
    """Returns (symbols, source) — source is "finnhub" | "yahoo" | None."""
    finnhub = _finnhub_peers(ticker)
    if finnhub:
        return finnhub, "finnhub"
    yahoo = _yahoo_related(ticker)
    if yahoo:
        return yahoo, "yahoo"
    return [], None


def _fundamentals(ticker: str, info: dict) -> dict:
    """Fundamentals — the biggest content gap the app had (docs/AUDIT.md M5):
    technical analysis only teaches half the picture for a beginning investor.
    All values come straight from the provider's own `.info`/`.calendar`
    fields — nothing computed or estimated here, matching the "numbers are
    exact" guardrail. `dividendYield` is already a percentage figure in
    yfinance's own convention (unlike `profitMargins`/`revenueGrowth`, which
    are fractions) — verified empirically (AAPL: 0.33 == 0.33%, not 33%).
    `debtToEquity` is likewise already a percentage in yfinance's convention.
    Degrades field-by-field: a missing figure is `None`, never fabricated or
    interpolated, and a genuinely thin listing simply has more `None`s."""
    next_earnings = None
    try:
        cal = with_retry(lambda: yf.Ticker(ticker).calendar, timeout=10)
        dates = (cal or {}).get("Earnings Date")
        if dates:
            d = dates[0] if isinstance(dates, list) else dates
            next_earnings = d.isoformat() if hasattr(d, "isoformat") else str(d)
    except Exception:
        pass

    fields = {
        "pe": info.get("trailingPE"),
        "forwardPe": info.get("forwardPE"),
        "eps": info.get("trailingEps"),
        "revenueGrowth": info.get("revenueGrowth"),   # fraction, e.g. 0.164 = 16.4%
        "profitMargin": info.get("profitMargins"),    # fraction
        "dividendYield": info.get("dividendYield"),   # already a percent figure
        "debtToEquity": info.get("debtToEquity"),     # already a percent figure
        "nextEarningsDate": next_earnings,
    }
    coverage = None if any(v is not None for v in fields.values()) else (
        "Fundamentals aren't available for this listing."
    )
    return {**fields, "coverage": coverage}


def get_profile(ticker: str) -> dict:
    """Assembles the ecosystem panel from several independent yfinance/Finnhub
    round trips. These used to run one after another — harmless when Yahoo is
    fast, but on a shared host (or just an ordinary slow moment) 4-5 sequential
    provider calls stack into 15-20+ seconds for one panel (user-reported
    2026-09-17: AAPL, a perfectly normal ticker, took ~19s in the Comparison
    tab). `info` and `peers` don't depend on each other, so they run
    concurrently; `fundamentals` (needs `info`), `peer_names` (needs `peers`),
    and a computed beta (needs to know `info` had none) then also run
    concurrently in a second round — critical path is roughly the length of
    the two SLOWEST calls, not the sum of all of them."""
    t = yf.Ticker(ticker)
    info_error = None  # temporary diagnostic (2026-09-18) — see get_profile_cached's docstring

    with ThreadPoolExecutor(max_workers=2) as ex:
        info_fut = ex.submit(lambda: with_retry(lambda: t.info, timeout=12))
        peers_fut = ex.submit(_peers, ticker)
        try:
            info = info_fut.result()
        except Exception as e:
            info = {}
            info_error = f"{type(e).__name__}: {e}"[:300]
        peers, peers_source = peers_fut.result()

    beta = info.get("beta")
    is_us = "." not in ticker  # US symbols have no exchange suffix (e.g. AAPL vs 7974.T)
    beta_source = "provider" if beta is not None else None
    beta_index = None
    needs_computed_beta = beta is None

    with ThreadPoolExecutor(max_workers=3) as ex:
        fundamentals_fut = ex.submit(_fundamentals, ticker, info)
        peer_names_fut = ex.submit(_peer_names, peers)
        beta_fut = ex.submit(_computed_beta, ticker) if needs_computed_beta else None

        fundamentals = fundamentals_fut.result()
        peer_names = peer_names_fut.result()
        if beta_fut is not None:
            # If no published beta (the usual non-US case), compute it ourselves
            # against the regional index — deterministic, exact, no external key.
            beta, beta_index = beta_fut.result()
            if beta is not None:
                beta_source = "computed"
        elif beta_index is None:
            # Provider betas (the common case) don't come with a named benchmark,
            # but Yahoo/most providers measure US beta against the S&P 500 and
            # non-US beta against the local index — the same map _computed_beta
            # uses. Naming it (rather than just saying "the market") is what lets
            # the UI actually explain "vs the S&P 500" instead of something vague.
            _, beta_index = _index_for(ticker)

    # Explain the gaps rather than showing a blank panel. Coverage outside the US
    # is thinner: yfinance often has no beta, and Finnhub's peers endpoint is US-only.
    coverage = {}
    if beta is None:
        coverage["beta"] = (
            "Beta isn't available for this listing"
            + (" (no regional index data)." if not is_us else ".")
        )
    if not peers:
        coverage["peers"] = "Peer/related companies aren't available for this listing."

    if fundamentals["coverage"]:
        coverage["fundamentals"] = fundamentals["coverage"]

    return {
        "fundamentals": {k: v for k, v in fundamentals.items() if k != "coverage"},
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "beta": beta,
        "betaSource": beta_source,   # "provider" | "computed" | None
        "betaIndex": beta_index,     # index name when computed (e.g. "Nikkei 225")
        "marketCap": info.get("marketCap"),
        # marketCap is denominated in the LISTING'S OWN currency (yfinance convention,
        # same as the quote) — never assume USD. The frontend must format it accordingly.
        "marketCapCurrency": info.get("currency"),
        "exchange": info.get("fullExchangeName") or info.get("exchange"),
        "country": info.get("country"),
        "peers": peers,
        # "finnhub" (same-industry peers) | "yahoo" (co-viewed by other
        # investors — a related-but-different signal, see _yahoo_related) |
        # None. The UI must label these differently, not present a Yahoo
        # fallback as if it were an industry-peer list.
        "peersSource": peers_source,
        # Full company name per peer ticker, for the ecosystem graph's hover
        # tooltip — kept separate from `peers` (a plain ticker list) because
        # services/evidence.py matches news relevance against `peers` directly
        # and expects strings, not {symbol, name} objects.
        "peerNames": peer_names,
        "summary": _truncate_summary(info.get("longBusinessSummary")),
        "coverage": coverage,
        # TEMPORARY diagnostic (2026-09-18, remove once the underlying Yahoo
        # .info reliability question is settled) — the raw exception from a
        # failed .info call. Never a secret (yfinance/.info is a keyless
        # public endpoint), only present on a genuine failure, and only
        # meant to answer "what is Yahoo actually saying from Render's IP"
        # without needing dashboard log access.
        "_infoError": info_error,
    }


def _looks_like_a_failed_fetch(profile: dict) -> bool:
    """`get_profile()` never raises — a failed `.info` call degrades internally
    to `None`s rather than an exception (by design, so a genuinely thin
    listing degrades gracefully instead of 500ing). That's the right behavior
    for a caller, but the WRONG thing to cache for 5 minutes: caching a
    transient failure as if it were a real, thin-coverage result means every
    request for that ticker in the next 5 min replays the one bad attempt
    instead of getting its own fresh try (confirmed live 2026-09-18: three
    separate `/ecosystem` calls, 3s apart, all returned the byte-identical
    empty profile). `sector`/`industry`/`summary` all come ONLY from the main
    ticker's `.info` call with no fallback, so all-`None` together is a clean
    signal that call failed outright, distinct from a listing that
    legitimately has no peers/fundamentals but DOES have a sector."""
    return profile.get("sector") is None and profile.get("industry") is None \
        and profile.get("summary") is None


def get_profile_cached(ticker: str) -> dict:
    """`get_profile()`, shared across BOTH `/ecosystem` and `/analyze`'s
    `orchestrator._gather()` (which needs the profile for news relevance
    filtering) via the same 5-min TTL cache `gather()` itself uses. These two
    endpoints used to each call `get_profile()` independently — the frontend
    fires both requests within milliseconds of each other, so a SECOND
    concurrent, redundant ~11-call yfinance blitz was firing for the same
    ticker at the same moment, doubling the load on Yahoo's already-flaky
    `.info` endpoint right when it's most likely to fail. `cache.get_or_set`'s
    per-key lock means only the first caller actually fetches; the other
    reuses that one result instead of racing it. A result that looks like a
    failed fetch (see `_looks_like_a_failed_fetch`) is never cached, so the
    next request gets a genuinely fresh attempt instead of the poisoned one."""
    return cache.get_or_set(
        f"profile:{ticker.upper()}", lambda: get_profile(ticker),
        should_cache=lambda p: not _looks_like_a_failed_fetch(p),
    )
