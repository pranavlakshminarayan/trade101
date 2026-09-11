"""
Retrospective replay — practise reading a chart without knowing the answer.

Pick a point in this stock's own history. The learner sees ONLY the bars up to
that point, writes down what they think was happening and why, and only then is
the outcome revealed.

The single most important property of this module: `setup()` must never leak a
bar after the cut. If the future is visible — even as a max, a count, or an axis
range — the exercise teaches nothing. So the split happens here, server-side,
and the outcome is fetched by a separate call the frontend makes only after the
learner has committed.

The honesty rule this must carry everywhere: seeing what followed one setup is
NOT evidence that the pattern predicts anything. Hindsight on a single sample is
the most reliable way to learn a false lesson, so every reveal says so.
"""
from __future__ import annotations

import hashlib
import random

import pandas as pd

from services import cache, indicators, marketdata

# Enough history behind the cut to read a trend, enough ahead to have an outcome.
MIN_LOOKBACK = 60
DEFAULT_HORIZON = 30


def _series(hist: pd.DataFrame) -> list[dict]:
    return [
        {"time": int(idx.timestamp()), "open": round(float(r.Open), 2),
         "high": round(float(r.High), 2), "low": round(float(r.Low), 2),
         "close": round(float(r.Close), 2), "volume": int(r.Volume)}
        for idx, r in hist.iterrows()
    ]


def _pick_cut(n: int, horizon: int, seed_key: str) -> int:
    """Choose a reproducible cut point with room on both sides.

    Seeded by ticker so the same stock gives the same exercise until the learner
    asks for another — a different chart on every render would make it
    impossible to discuss what you saw.
    """
    lo, hi = MIN_LOOKBACK, n - horizon - 1
    if hi <= lo:
        return -1
    seed = int(hashlib.sha256(seed_key.encode()).hexdigest()[:8], 16)
    return random.Random(seed).randint(lo, hi)


def setup(ticker: str, horizon: int = DEFAULT_HORIZON, variant: int = 0,
          period: str = "5y") -> dict | None:
    """The visible half: bars up to the cut, and nothing whatsoever after it.

    Returns None if the symbol has no data, or a dict with `available: False`
    when its history is too short for a fair exercise.
    """
    data, _ = cache.get_or_fetch("replay", f"{ticker.upper()}:{period}",
                                 lambda: marketdata.get(ticker, period=period))
    if data is None:
        return None
    hist, quote = data
    n = len(hist)

    cut = _pick_cut(n, horizon, f"{ticker.upper()}:{variant}")
    if cut < 0:
        return {"available": False, "ticker": quote["symbol"],
                "reason": f"Only {n} bars of history — a replay needs at least "
                          f"{MIN_LOOKBACK + horizon + 1}. Try a company with a longer "
                          f"listing history."}

    visible = hist.iloc[:cut + 1]
    cut_date = visible.index[-1]

    return {
        "available": True,
        "ticker": quote["symbol"],
        "name": quote.get("name"),
        "variant": variant,
        "horizon": horizon,
        # Everything below describes ONLY the visible window.
        "asOf": cut_date.isoformat(),
        "ohlcv": _series(visible),
        "indicators": indicators.compute_indicators(visible),
        "bars": len(visible),
        "prompt": (
            f"This is {quote['symbol']} up to {cut_date.date().isoformat()}. "
            f"What do you think was happening here, and which evidence tells you that? "
            f"Commit your read before revealing what followed."
        ),
        "caveat": "You are reading one historical window of one company. Whatever "
                  "happened next is what happened once — not what the setup predicts.",
    }


def reveal(ticker: str, horizon: int = DEFAULT_HORIZON, variant: int = 0,
           period: str = "5y") -> dict | None:
    """The hidden half — fetched only after the learner has committed a read."""
    data, _ = cache.get_or_fetch("replay", f"{ticker.upper()}:{period}",
                                 lambda: marketdata.get(ticker, period=period))
    if data is None:
        return None
    hist, quote = data
    n = len(hist)

    cut = _pick_cut(n, horizon, f"{ticker.upper()}:{variant}")
    if cut < 0:
        return {"available": False, "ticker": quote["symbol"],
                "reason": "Not enough history for a replay."}

    after = hist.iloc[cut + 1: cut + 1 + horizon]
    if after.empty:
        return {"available": False, "ticker": quote["symbol"],
                "reason": "No bars after the cut point."}

    start = float(hist["Close"].iloc[cut])
    closes = after["Close"]
    end = float(closes.iloc[-1])
    peak_i, trough_i = int(closes.argmax()), int(closes.argmin())

    def pct(v):
        return round((v - start) / start * 100, 2)

    return {
        "available": True,
        "ticker": quote["symbol"],
        "horizon": horizon,
        "variant": variant,
        "cutClose": round(start, 2),
        "ohlcv": _series(after),
        "outcome": {
            "changePercent": pct(end),
            "endClose": round(end, 2),
            "peak": {"percent": pct(float(closes.iloc[peak_i])),
                     "bars": peak_i + 1,
                     "date": after.index[peak_i].date().isoformat()},
            "trough": {"percent": pct(float(closes.iloc[trough_i])),
                       "bars": trough_i + 1,
                       "date": after.index[trough_i].date().isoformat()},
            "maxDrawdownPercent": round((float(closes.min()) - start) / start * 100, 2),
            "barsRevealed": len(after),
        },
        "caveat": (
            "This is one sample. A single outcome cannot confirm or refute a way of "
            "reading a chart — plenty of sound reads lose and plenty of poor ones win. "
            "Judge your reasoning against the evidence you had at the cut, not against "
            "what the price did next."
        ),
    }
