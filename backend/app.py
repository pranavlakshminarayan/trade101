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
from services import (cache, company, compare as compare_svc, evidence, fundamentals,
                      indicators, lenses, marketdata, news as news_svc, patterns,
                      replay, search, storage, usage, watchlist)

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


# ---- Phase 2: the learning engine ----------------------------------------

@app.get("/fundamentals/{ticker}")
def company_fundamentals(ticker: str):
    """Earnings, revenue, margins, cash flow and valuation context — the business
    behind the ticker, reported as filed and never inferred."""
    return fundamentals.get_fundamentals(ticker)


@app.get("/replay/{ticker}")
def replay_setup(ticker: str, horizon: int = 30, variant: int = 0):
    """The VISIBLE half of a retrospective replay: history up to a hidden cut
    point. Contains no information about what followed — that is /replay/reveal,
    which the learner should only call after committing a read."""
    result = replay.setup(ticker, horizon=horizon, variant=variant)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No market data found for '{ticker}'.")
    return result


@app.get("/replay/{ticker}/reveal")
def replay_reveal(ticker: str, horizon: int = 30, variant: int = 0):
    """What actually followed. One sample — never evidence that a setup predicts."""
    result = replay.reveal(ticker, horizon=horizon, variant=variant)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No market data found for '{ticker}'.")
    return result


@app.get("/journal")
def journal_list(ticker: str | None = None, limit: int = 100):
    """The learner's own saved reads — hypotheses and evidence, not trades."""
    return {"entries": storage.get_journal(ticker, limit)}


@app.post("/journal")
def journal_add(entry: dict):
    """Save one read. `hypothesis` is required — a lean with no reasoning behind
    it is exactly the habit this app exists to discourage."""
    if not (entry.get("hypothesis") or "").strip():
        raise HTTPException(status_code=400,
                            detail="Write what you think is happening and why — a saved "
                                   "lean with no reasoning teaches nothing on revisit.")
    if not (entry.get("ticker") or "").strip():
        raise HTTPException(status_code=400, detail="A journal entry needs a ticker.")
    saved = storage.add_journal_entry(entry)
    if saved is None:
        raise HTTPException(status_code=503,
                            detail="Could not save — the local journal database is "
                                   "unavailable. Your research is unaffected.")
    return saved


@app.patch("/journal/{entry_id}")
def journal_reflect(entry_id: int, body: dict):
    """Attach a revisit reflection — the 'revisit' step of Guided Study."""
    ok = storage.update_journal_reflection(entry_id, (body or {}).get("reflection", ""))
    if not ok:
        raise HTTPException(status_code=404, detail=f"No journal entry {entry_id}.")
    return {"updated": entry_id}


@app.delete("/journal/{entry_id}")
def journal_delete(entry_id: int):
    ok = storage.delete_journal_entry(entry_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"No journal entry {entry_id}.")
    return {"deleted": entry_id}


# ---- Phase 2.5: style lenses ---------------------------------------------

@app.get("/lenses/{ticker}")
def style_lenses(ticker: str, period: str = "1y"):
    """
    The same data read five ways: trend, swing, mean-reversion, long-term and
    event-driven. Each declares what it considers, what it IGNORES, evidence in
    this data that argues against it, and how it fails.

    Entirely deterministic — computed from the exact numbers, so it costs
    nothing to run and has nothing to hallucinate. There is no day-trading lens:
    on ~15-minute delayed data it would look precise and be wrong.
    """
    data = marketdata.get(ticker, period=period)
    if data is None:
        raise HTTPException(status_code=404, detail=f"No market data found for '{ticker}'.")
    hist, quote = data
    ind = indicators.compute_indicators(hist)

    fund = fundamentals.get_fundamentals(ticker)
    raw_news, _ = news_svc.get_news(ticker)
    kept, _report = evidence.select(raw_news, quote["symbol"], quote.get("name"))
    filings, _ = news_svc.get_recent_filings(ticker)

    return {
        "ticker": quote["symbol"],
        "period": period,
        **marketdata.freshness(hist, "1d"),
        **lenses.build(ind, fund, kept, filings),
    }


# ---- Phase 3: the research workspace --------------------------------------

@app.get("/compare")
def compare_tickers(tickers: str, period: str = "1y", interval: str = "1d"):
    """
    Two to four companies on the same axes, each rebased to 100 at the start of
    the window. Produces no ranking and no score: it shows how the companies
    differ, and names where a side-by-side reading is weak.
    """
    symbols = [t for t in (tickers or "").split(",") if t.strip()]
    if len(symbols) < 2:
        raise HTTPException(status_code=400,
                            detail="Give at least two comma-separated tickers to compare.")
    return compare_svc.compare(symbols, period=period, interval=interval)


@app.get("/watchlist")
def watchlist_status(refresh: bool = True):
    """Watched companies + what changed since you last looked, as information
    events — never prompts to act."""
    return watchlist.status(refresh=refresh)


@app.post("/watchlist")
def watchlist_add(body: dict):
    ticker = (body or {}).get("ticker", "").strip()
    if not ticker:
        raise HTTPException(status_code=400, detail="A watchlist entry needs a ticker.")
    level = body.get("level")
    saved = storage.watch_add(ticker, body.get("name"), body.get("note"),
                              float(level) if level not in (None, "") else None)
    if saved is None:
        raise HTTPException(status_code=503, detail="Watchlist database unavailable.")
    return saved


@app.delete("/watchlist/{ticker}")
def watchlist_remove(ticker: str):
    if not storage.watch_remove(ticker):
        raise HTTPException(status_code=404, detail=f"{ticker.upper()} is not on the watchlist.")
    return {"removed": ticker.upper()}


@app.get("/practice")
def practice_list():
    """The practice lab: hypothetical positions, marked to delayed prices.

    Explicitly separate from research. Every figure returned is hypothetical and
    is labelled as such by the caller.
    """
    entries = storage.practice_list()
    out = []
    for e in entries:
        mark, note = None, None
        if e.get("closed_at"):
            mark = e["close_price"]
        else:
            try:
                data = marketdata.get(e["ticker"], period="5d")
                mark = data[1].get("price") if data else None
            except marketdata.ProviderError as ex:
                note = str(ex)
        pnl = None
        if mark is not None:
            diff = (mark - e["open_price"]) * (1 if e["direction"] == "long" else -1)
            pnl = {
                "hypotheticalChangePercent": round(diff / e["open_price"] * 100, 2),
                "hypotheticalAmount": round(diff * e["quantity"], 2),
            }
        out.append({**e, "mark": mark, "hypothetical": pnl, "note": note})
    return {
        "entries": out,
        "disclaimer": "Every figure here is HYPOTHETICAL and marked to data delayed by "
                      "roughly 15 minutes. No order was placed, no costs, spread, slippage "
                      "or tax are modelled, and a hypothetical result that assumes you could "
                      "transact at a delayed price is optimistic by construction.",
        "purpose": "This lab exists to test reasoning, not to keep score. The reflection on "
                   "each closed entry is the part worth reading.",
    }


@app.post("/practice")
def practice_open(body: dict):
    b = body or {}
    if not (b.get("ticker") or "").strip():
        raise HTTPException(status_code=400, detail="A practice entry needs a ticker.")
    if not (b.get("reason") or "").strip():
        raise HTTPException(status_code=400,
                            detail="Write why you are opening this hypothetical position. "
                                   "A position with no reasoning behind it teaches nothing "
                                   "when you close it.")
    try:
        price = float(b.get("price"))
        quantity = float(b.get("quantity", 1))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Price and quantity must be numbers.")
    direction = b.get("direction", "long")
    if direction not in ("long", "short"):
        raise HTTPException(status_code=400, detail="Direction must be 'long' or 'short'.")

    saved = storage.practice_open(b["ticker"], price, quantity, direction, b["reason"].strip())
    if saved is None:
        raise HTTPException(status_code=503, detail="Practice database unavailable.")
    return saved


@app.patch("/practice/{entry_id}")
def practice_close(entry_id: int, body: dict):
    b = body or {}
    try:
        price = float(b.get("price"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="A closing price is required.")
    if not storage.practice_close(entry_id, price, b.get("reflection")):
        raise HTTPException(status_code=404,
                            detail=f"No open practice entry {entry_id}.")
    return {"closed": entry_id}


@app.delete("/practice/{entry_id}")
def practice_delete(entry_id: int):
    if not storage.practice_delete(entry_id):
        raise HTTPException(status_code=404, detail=f"No practice entry {entry_id}.")
    return {"deleted": entry_id}
