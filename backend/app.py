"""
Trade101 backend — FastAPI.

Milestone 1: real-time, ticker-agnostic research endpoint returning exact
market data + indicators. No AI yet (that arrives in Milestone 3); this is the
deterministic foundation everything else stands on.
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load .env from the project root (one level up from backend/) so the named
# API keys are available as environment variables.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from agents import llm, orchestrator
from services import company, indicators, marketdata, patterns, search
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
    closes = hist["Close"].tolist()
    times = [int(idx.timestamp()) for idx in hist.index]
    return {"ticker": ticker.upper(), "period": period, "interval": interval,
            "patterns": patterns.detect(closes, times)}


class AskBody(BaseModel):
    question: str
    history: list[dict] = []


@app.post("/ask/{ticker}")
def ask(ticker: str, body: AskBody):
    """Ask-Claude chat: answer a question about a stock, grounded in the same exact
    data + filtered evidence as /analyze. Degrades gracefully (no key / error →
    available:false) so the rest of the app is unaffected. Spends the Claude key."""
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
        # redact_secrets: an exception's text can carry a request URL with a key.
        return {"available": False, "reason": redact_secrets(f"AI narration error: {e}")}
    if result is None:
        raise HTTPException(status_code=404, detail=f"No market data found for '{ticker}'.")
    return {"available": True, **result}
