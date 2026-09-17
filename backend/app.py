"""
Trade101 backend — FastAPI.

Milestone 1: real-time, ticker-agnostic research endpoint returning exact
market data + indicators. No AI yet (that arrives in Milestone 3); this is the
deterministic foundation everything else stands on.
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load .env from the project root (one level up from backend/) so the named
# API keys are available as environment variables.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from agents import llm, orchestrator
from services import company, indicators, marketdata, patterns, search
from services.access import guard_paid_endpoint
from services.safe import redact_secrets

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


@app.get("/research/{ticker}")
def research(ticker: str, period: str = "1y", interval: str = "1d"):
    """
    Live research bundle for ANY ticker: quote + indicators + OHLCV (for the
    chart). Ticker-agnostic — nothing is hardcoded to a specific symbol.
    """
    data = marketdata.get(ticker, period=period, interval=interval)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No market data found for '{ticker}'. Try the company name instead — "
                   f"search resolves any market and lets you pick from the matches.",
        )
    hist, quote = data
    ind = indicators.compute_indicators(hist)

    # UNIX seconds so both daily and intraday intervals render correctly.
    times = [int(idx.timestamp()) for idx in hist.index]
    ohlcv = [
        {
            "time": t,
            "open": round(float(row.Open), 2),
            "high": round(float(row.High), 2),
            "low": round(float(row.Low), 2),
            "close": round(float(row.Close), 2),
            "volume": int(row.Volume),
        }
        for t, (_, row) in zip(times, hist.iterrows())
    ]
    # Full time-aligned series (not just the latest snapshot in `indicators`)
    # so the chart can actually PLOT SMA/Bollinger/RSI/MACD instead of only
    # explaining them in prose next to a chart that never shows them
    # (docs/AUDIT.md finding H5).
    ind_series = indicators.compute_indicator_series(hist, times)

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
            "asOf": hist.index[-1].date().isoformat() if len(hist) else None,
            "bars": len(ohlcv),
            "interval": interval,
        },
    }


@app.get("/ecosystem/{ticker}")
def ecosystem(ticker: str):
    """Company profile + peers: sector, industry, beta, market cap, peer symbols."""
    data = marketdata.get(ticker, period="5d")  # confirm the symbol exists
    if data is None:
        raise HTTPException(status_code=404, detail=f"No data for '{ticker}'.")
    return {"ticker": ticker.upper(), **company.get_profile(ticker)}


@app.get("/patterns/{ticker}")
def detect_patterns(ticker: str, period: str = "1y", interval: str = "1d"):
    """Detect chart patterns on the given timeframe — works for any period/interval,
    so the magnifier applies across all chart tabs."""
    data = marketdata.get(ticker, period=period, interval=interval)
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


@app.post("/ask/{ticker}", dependencies=[Depends(guard_paid_endpoint)])
def ask(ticker: str, body: AskBody):
    """Ask-Claude chat: answer a question about a stock, grounded in the same exact
    data + filtered evidence as /analyze. Degrades gracefully (no key / error →
    available:false) so the rest of the app is unaffected. Spends the Claude key.
    Gated by services.access (pre-share fix): an access token (if configured) and
    a shared daily cap, so a public visitor can't run up the owner's Claude bill."""
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Ask a question first.")
    try:
        result = orchestrator.ask(ticker, q, body.history)
    except llm.MissingKeyError as e:
        return {"available": False, "reason": str(e)}
    except Exception as e:
        return {"available": False, "reason": redact_secrets(f"Ask-Claude error: {e}")}
    if result is None:
        raise HTTPException(status_code=404, detail=f"No market data found for '{ticker}'.")
    return {"available": True, **result}


@app.get("/analyze/{ticker}", dependencies=[Depends(guard_paid_endpoint)])
def analyze(ticker: str):
    """
    AI narration for a ticker: momentum read (sourced), news Feed + "What it
    means" inference. Separate from /research so the chart renders instantly and
    never blocks on the AI. Degrades gracefully: missing key / AI error →
    available:false with a reason, not a crash. Gated by services.access
    (pre-share fix): an access token (if configured) and a shared daily cap.
    """
    try:
        result = orchestrator.analyze(ticker)
    except llm.MissingKeyError as e:
        return {"available": False, "reason": str(e)}
    except Exception as e:  # network/API/parse — chart still works without this
        # redact_secrets: an exception's text can carry a request URL with a key.
        return {"available": False, "reason": redact_secrets(f"AI narration error: {e}")}
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
