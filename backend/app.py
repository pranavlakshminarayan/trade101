"""
Trade101 backend — FastAPI.

Milestone 1: real-time, ticker-agnostic research endpoint returning exact
market data + indicators. No AI yet (that arrives in Milestone 3); this is the
deterministic foundation everything else stands on.
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load .env from the project root (one level up from backend/) so the named
# API keys are available as environment variables.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import anthropic

from agents import llm, orchestrator
from services import company, indicators, marketdata, patterns, search
from services.safe import redact_secrets


def _ai_error_reason(prefix: str, e: Exception) -> str:
    """A friendly, actionable reason string for the AI-unavailable degrade
    path. BYOK (2026-09-17): the most common failure now is a VISITOR's own
    key being invalid/expired/out of credits, not a server misconfiguration —
    give that its own plain message instead of Anthropic's raw JSON error
    body. redact_secrets still runs on the generic fallback: an exception's
    text can otherwise carry a request URL with a key in it."""
    if isinstance(e, anthropic.AuthenticationError):
        return "That Anthropic API key was rejected — double-check you pasted it correctly."
    if isinstance(e, anthropic.PermissionDeniedError):
        return "That Anthropic API key doesn't have permission for this — check its plan/scope."
    if isinstance(e, anthropic.RateLimitError):
        return "Your Anthropic account hit a rate limit — wait a moment and try again."
    return redact_secrets(f"{prefix}: {e}")

app = FastAPI(title="Trade101 API", version="0.1.0")

# Allow the local React dev server to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "trade101", "version": app.version}


@app.get("/search")
def search_symbols(q: str):
    """Resolve a company name or partial ticker to candidate symbols."""
    return {"query": q, "candidates": search.resolve(q)}


# SMA200 needs 200 bars of lookback before it can produce a single point.
# Fetching only the DISPLAY window (e.g. exactly 5 days for the "5D" chart
# tab) leaves no room for that lookback, so SMA200 only ever appeared over
# whatever trailing sliver of the window happened to have 200+ bars behind
# it — cut short on 1Y, gone entirely on 5D/1D (user-reported 2026-09-17).
# Fix: fetch MORE history than we intend to display, compute indicators on
# the full fetch (so the lookback is actually satisfied), then trim back to
# the original display width. `display_bars` mirrors the bar count the
# ORIGINAL (undersized) fetch used to return, so the visible chart window is
# unchanged — only the indicators drawn on it are now fully populated.
# Periods empirically verified against yfinance (see docs/DEVELOPMENT-LOG.md):
# "3mo" is REJECTED for 30m/15m/5m intervals (0 bars back) — intraday history
# is capped at 60 days regardless of which valid period token requests it.
_LOOKBACK_FETCH = {
    ("1y", "1d"): ("2y", 251),
    ("1mo", "1d"): ("1y", 22),
    ("1mo", "30m"): ("60d", 286),
    ("5d", "15m"): ("60d", 130),
    ("1d", "5m"): ("60d", 78),
}


def _fetch_with_lookback(ticker: str, period: str, interval: str):
    """marketdata.get(), but fetching extra history first when the requested
    (period, interval) is a known short display window — see _LOOKBACK_FETCH.
    Returns (hist, quote, display_bars) — display_bars is None when no
    trimming is needed (either an unrecognized combo, passed straight
    through unchanged, or the fetch was already exactly what's wanted).

    Bug (user-reported 2026-09-17, live on the Render deploy): the lookback
    substitution assumes fetching a WIDER window is always a safe superset of
    the original request — false for SK hynix's SKHY listing, which had
    genuinely months of daily history (1Y worked fine) but returned ZERO rows
    for "60d"/30m (the substitute for the "10D" tab's "1mo"/30m) while the
    ORIGINAL, narrower "1mo"/30m request had 287 real bars all along —
    verified directly against yfinance. Something about this ticker's
    intraday data window rejects the wider ask outright rather than just
    returning fewer bars. Falling back to the original (period, interval)
    when the extended fetch comes back empty recovers the real data instead
    of reporting "no data" (or, before the timeout/loading-state fixes,
    hanging) for a ticker that plainly has data to show."""
    fetch_period, display_bars = _LOOKBACK_FETCH.get((period, interval), (period, None))
    data = marketdata.get(ticker, period=fetch_period, interval=interval)
    if data is None and fetch_period != period:
        data = marketdata.get(ticker, period=period, interval=interval)
        display_bars = None  # the original fetch IS the display window — no trimming needed
    if data is None:
        return None
    hist, quote = data
    return hist, quote, display_bars


@app.get("/research/{ticker}")
def research(ticker: str, period: str = "1y", interval: str = "1d"):
    """
    Live research bundle for ANY ticker: quote + indicators + OHLCV (for the
    chart). Ticker-agnostic — nothing is hardcoded to a specific symbol.
    """
    try:
        data = _fetch_with_lookback(ticker, period, interval)
    except TimeoutError:
        # Yahoo is responding slowly/being rate-limited (services/net.py) —
        # an honest "try again" beats a misleading "no data for this ticker"
        # (user-reported 2026-09-17: this used to hang the UI forever instead).
        raise HTTPException(
            status_code=504,
            detail="Yahoo Finance is responding slowly for this ticker right now. Try again in a moment.",
        )
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No market data found for '{ticker}'. Try the company name instead — "
                   f"search resolves any market and lets you pick from the matches.",
        )
    hist, quote, display_bars = data
    # Indicators are computed on the FULL fetched history (the lookback
    # buffer above) so SMA200 etc. are actually defined; only the display
    # window is trimmed afterward, for the chart and for the Metrics snapshot.
    ind = indicators.compute_indicators(hist)
    times_full = [int(idx.timestamp()) for idx in hist.index]
    ind_series = indicators.compute_indicator_series(hist, times_full)

    display_hist = hist.tail(display_bars) if display_bars else hist
    times = times_full[-display_bars:] if display_bars else times_full
    cutoff = times[0] if times else None
    if cutoff is not None:
        # Trim the indicator series to the same display window — the extra
        # lookback bars did their job (populating SMA200 etc.) and are never
        # shown, so there's no reason to ship their indicator points either.
        def _trim(pts):
            return [p for p in pts if p["time"] >= cutoff]
        ind_series = {
            "sma50": _trim(ind_series["sma50"]), "sma200": _trim(ind_series["sma200"]),
            "bollinger": {k: _trim(v) for k, v in ind_series["bollinger"].items()},
            "rsi14": _trim(ind_series["rsi14"]),
            "macd": {k: _trim(v) for k, v in ind_series["macd"].items()},
        }

    # UNIX seconds so both daily and intraday intervals render correctly.
    ohlcv = [
        {
            "time": t,
            "open": round(float(row.Open), 2),
            "high": round(float(row.High), 2),
            "low": round(float(row.Low), 2),
            "close": round(float(row.Close), 2),
            "volume": int(row.Volume),
        }
        for t, (_, row) in zip(times, display_hist.iterrows())
    ]

    return {
        "ticker": quote["symbol"],
        "quote": quote,
        "indicators": ind,
        "indicatorSeries": ind_series,
        "ohlcv": ohlcv,
        "meta": {
            "source": "Yahoo Finance",
            "delayed": True,
            "note": "Data delayed ~15m; not real-time trading data.",
            "asOf": display_hist.index[-1].date().isoformat() if len(display_hist) else None,
            "bars": len(ohlcv),
            "interval": interval,
        },
    }


@app.get("/ecosystem/{ticker}")
def ecosystem(ticker: str):
    """Company profile + peers: sector, industry, beta, market cap, peer symbols."""
    try:
        data = marketdata.get(ticker, period="5d")  # confirm the symbol exists
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Yahoo Finance is responding slowly for this ticker right now. Try again in a moment.",
        )
    if data is None:
        raise HTTPException(status_code=404, detail=f"No data for '{ticker}'.")
    return {"ticker": ticker.upper(), **company.get_profile(ticker)}


@app.get("/patterns/{ticker}")
def detect_patterns(ticker: str, period: str = "1y", interval: str = "1d"):
    """Detect chart patterns on the given timeframe — works for any period/interval,
    so the magnifier applies across all chart tabs. Scans the WHOLE fetched window
    (not just a recent slice): a brief attempt to restrict intraday scans to the
    trailing 2 hours (user-reported "3-4 hours ago is stale") backfired — it also
    excluded genuinely recent patterns that need more than 2 hours of bars to
    form, and older-but-real ones the user still wanted visible. `patterns.detect`
    already sorts most-recent-first (docs/AUDIT.md H6), so recency is handled by
    ranking, not by hiding data from the scan."""
    try:
        data = marketdata.get(ticker, period=period, interval=interval)
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Yahoo Finance is responding slowly for this ticker right now. Try again in a moment.",
        )
    if data is None:
        raise HTTPException(status_code=404, detail=f"No data for '{ticker}'.")
    hist, _ = data
    # High/Low, not Close — real support/resistance touches the wicks, and
    # detecting on Close alone under-detects and misplaces marked points
    # relative to what the chart actually shows (docs/AUDIT.md finding H6).
    highs = hist["High"].tolist()
    lows = hist["Low"].tolist()
    times = [int(idx.timestamp()) for idx in hist.index]
    return {"ticker": ticker.upper(), "period": period, "interval": interval,
            "patterns": patterns.detect(highs, lows, times)}


@app.get("/news/{ticker}")
def news(ticker: str):
    """Deterministic news feed for a ticker — NO Claude call, so it's free and
    never depends on an AI key, an AI error, or the /analyze daily cap. The
    frontend loads this immediately; the AI-derived "what it means" inference
    layers on top separately once /analyze completes (docs/AUDIT.md H3 — news
    used to reach the UI ONLY through /analyze, so deterministic headlines
    were unavailable whenever the judgment layer was)."""
    try:
        result = orchestrator.news_bundle(ticker)
    except Exception as e:  # keep this endpoint's own contract: never 500 the feed
        return {"available": False, "reason": redact_secrets(f"News fetch error: {e}")}
    if result is None:
        raise HTTPException(status_code=404, detail=f"No market data found for '{ticker}'.")
    return {"available": True, **result}


class AskBody(BaseModel):
    question: str
    history: list[dict] = []


@app.post("/ask/{ticker}")
def ask(response: Response, ticker: str, body: AskBody, x_anthropic_key: str | None = Header(default=None)):
    """Ask-Claude chat: answer a question about a stock, grounded in the same exact
    data + filtered evidence as /analyze. Degrades gracefully (no key / error →
    available:false) so the rest of the app is unaffected. BYOK (2026-09-17):
    spends the VISITOR's own Anthropic key, sent as X-Anthropic-Key — never the
    app owner's, so an open shared link carries no cost risk. See agents/llm.py.
    `Cache-Control: no-store` for the same reason as /analyze — see its docstring."""
    response.headers["Cache-Control"] = "no-store"
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Ask a question first.")
    try:
        result = orchestrator.ask(ticker, q, body.history, client_key=x_anthropic_key)
    except llm.MissingKeyError as e:
        return {"available": False, "reason": str(e)}
    except Exception as e:
        return {"available": False, "reason": _ai_error_reason("Ask-Claude error", e)}
    if result is None:
        raise HTTPException(status_code=404, detail=f"No market data found for '{ticker}'.")
    return {"available": True, **result}


@app.get("/analyze/{ticker}")
def analyze(response: Response, ticker: str, x_anthropic_key: str | None = Header(default=None)):
    """
    AI narration for a ticker: momentum read (sourced), news Feed + "What it
    means" inference. Separate from /research so the chart renders instantly and
    never blocks on the AI. Degrades gracefully: missing key / AI error →
    available:false with a reason, not a crash. BYOK (2026-09-17): spends the
    VISITOR's own Anthropic key, sent as X-Anthropic-Key — never the app
    owner's. See agents/llm.py.

    `Cache-Control: no-store` (2026-09-17, user-reported): this is a GET
    endpoint whose result depends on the X-ANTHROPIC-KEY HEADER, which browser
    HTTP caching does not key on by default (only the URL/method, unless the
    response sets `Vary`). Without this, a request to `/analyze/AAPL` that
    failed (e.g. during testing with an invalid key) could get cached and
    silently served back to a LATER request for the same ticker with a
    genuinely valid key — the visitor would see a stale "key rejected" error
    even though their real key works, with no way to tell it was ever cached.
    """
    response.headers["Cache-Control"] = "no-store"
    try:
        result = orchestrator.analyze(ticker, client_key=x_anthropic_key)
    except llm.MissingKeyError as e:
        return {"available": False, "reason": str(e)}
    except Exception as e:  # network/API/parse — chart still works without this
        return {"available": False, "reason": _ai_error_reason("AI narration error", e)}
    if result is None:
        raise HTTPException(status_code=404, detail=f"No market data found for '{ticker}'.")
    return {"available": True, **result}


# --- serve the built frontend (single-service deploy) --------------------------
# When frontend/dist exists (i.e. after `npm run build`), serve it from the same
# origin as the API. Mounted LAST so every API route above takes precedence; the
# static mount is the catch-all (html=True → SPA index fallback). In dev the dist
# folder is absent and Vite serves the UI separately, so this is a no-op then.
from fastapi.staticfiles import StaticFiles  # noqa: E402

_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="spa")
