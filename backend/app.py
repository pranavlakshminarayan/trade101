"""
Trade101 backend — FastAPI.

Deterministic services own the numbers (market data, indicators, patterns,
company profile); the agents own the judgment (the sourced momentum read and
news inference). The two are split across endpoints on purpose: /research never
waits on — or fails because of — the AI.
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load .env from the project root (one level up from backend/) so the named
# API keys are available as environment variables.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from agents import llm, orchestrator
from services import cache, company, indicators, marketdata, patterns, search, storage, usage

app = FastAPI(title="Trade101 API", version="0.1.0")

# Allow the local React dev server to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(marketdata.ProviderError)
def provider_unreachable(request: Request, exc: marketdata.ProviderError):
    """A source outage is a 503 with an explanation, never a 500 stack trace.

    The frontend shows `detail` verbatim, so it has to say what failed, what
    still works, and whether retrying is worth it.
    """
    return JSONResponse(
        status_code=503,
        content={
            "detail": str(exc),
            "failure": "provider_unreachable",
            "provider": marketdata.PROVIDER,
            "retryable": True,
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "trade101", "version": app.version}


@app.get("/search")
def search_symbols(q: str):
    """Resolve a company name or partial ticker to candidate symbols."""
    return {"query": q, "candidates": search.resolve(q)}


@app.get("/research/{ticker}")
def research(ticker: str, period: str = "1y", interval: str = "1d"):
    """
    Live research bundle for ANY ticker: quote + indicators + OHLCV (for the
    chart). Ticker-agnostic — nothing is hardcoded to a specific symbol.
    """
    data, cache_meta = marketdata.get_with_meta(ticker, period=period, interval=interval)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No market data found for '{ticker}'. Try the company name instead — "
                   f"search resolves any market and lets you pick from the matches.",
        )
    hist, quote = data
    ind = indicators.compute_indicators(hist)

    # UNIX seconds so both daily and intraday intervals render correctly.
    ohlcv = [
        {
            "time": int(idx.timestamp()),
            "open": round(float(row.Open), 2),
            "high": round(float(row.High), 2),
            "low": round(float(row.Low), 2),
            "close": round(float(row.Close), 2),
            "volume": int(row.Volume),
        }
        for idx, row in hist.iterrows()
    ]

    return {
        "ticker": quote["symbol"],
        "quote": quote,
        "indicators": ind,
        "ohlcv": ohlcv,
        "meta": {
            "provider": marketdata.PROVIDER,
            "source": "Yahoo Finance",
            "delayed": True,
            "note": "Data delayed ~15m; not real-time trading data.",
            "period": period,
            "interval": interval,
            "bars": len(ohlcv),
            # The as-of every panel on the page must agree with.
            **marketdata.freshness(hist, interval),
            "cache": cache_meta,
        },
    }


@app.get("/ecosystem/{ticker}")
def ecosystem(ticker: str):
    """Company profile + peers: sector, industry, beta, market cap, peer symbols."""
    data = marketdata.get(ticker, period="5d")  # confirm the symbol exists
    if data is None:
        raise HTTPException(status_code=404, detail=f"No data for '{ticker}'.")
    return {"ticker": ticker.upper(), **company.get_profile(ticker),
            "meta": {"provider": "Yahoo Finance + Finnhub peers",
                     "note": "Company profile is cached for up to 24h; sector, industry and "
                             "beta change rarely."}}


@app.get("/patterns/{ticker}")
def detect_patterns(ticker: str, period: str = "1y", interval: str = "1d"):
    """Detect chart patterns on the given timeframe — works for any period/interval,
    so the magnifier applies across all chart tabs."""
    data = marketdata.get(ticker, period=period, interval=interval)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No data for '{ticker}'.")
    hist, _ = data
    closes = hist["Close"].tolist()
    times = [int(idx.timestamp()) for idx in hist.index]
    return {"ticker": ticker.upper(), "period": period, "interval": interval,
            "patterns": patterns.detect(closes, times),
            "meta": {**marketdata.freshness(hist, interval), "bars": len(closes)}}


@app.get("/analyze/{ticker}")
def analyze(ticker: str):
    """
    AI narration for a ticker: momentum read (sourced), news Feed + "What it
    means" inference. Separate from /research so the chart renders instantly and
    never blocks on the AI. Degrades gracefully: missing key / AI error →
    available:false with a reason, not a crash.
    """
    try:
        result = orchestrator.analyze(ticker)
    except llm.MissingKeyError as e:
        return {"available": False, "reason": str(e)}
    except Exception as e:  # network/API/parse — chart still works without this
        return {"available": False, "reason": f"AI narration error: {e}"}
    if result is None:
        raise HTTPException(status_code=404, detail=f"No market data found for '{ticker}'.")
    return {"available": True, **result}


@app.get("/usage")
def llm_usage(since: str | None = None):
    """
    What the AI has cost, broken down by PURPOSE (which feature spent it), by
    key, and by model. Purpose is recorded independently of the key, so the
    breakdown is the same whether you run one named key or several.

    `since` is an ISO-8601 UTC timestamp (e.g. 2026-09-01T00:00:00+00:00);
    omit for all-time.
    """
    return usage.summary(since)


@app.get("/history")
def history(limit: int = 50):
    """Server-side record of researched stocks + their AI takeaway."""
    return {"history": storage.get_history(limit)}


@app.delete("/history")
def history_clear():
    """Clear the saved research history."""
    return {"cleared": storage.clear_history()}


@app.get("/cache")
def cache_stats():
    """What the response cache is holding — useful when a number looks stale."""
    return cache.stats()
