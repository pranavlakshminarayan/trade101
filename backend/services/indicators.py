"""
Technical indicators — pure, deterministic functions over a price series.

Every function takes a pandas Series/DataFrame and returns exact values (no LLM,
no hidden state), so results are reproducible and unit-testable. This is the
"numbers are exact" half of Trade101's anti-hallucination contract.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---- primitives -------------------------------------------------------------

def sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential moving average (adjust=False → recursive/standard form)."""
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder's smoothing)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD line, signal line, histogram."""
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    """Bollinger Bands: upper, middle (SMA), lower."""
    mid = sma(series, window)
    std = series.rolling(window).std(ddof=0)
    return mid + num_std * std, mid, mid - num_std * std


# ---- helpers ----------------------------------------------------------------

def _num(x):
    """Return a rounded float, or None for NaN/inf — never a raw NaN in JSON."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(f):
        return None
    return round(f, 4)


# ---- public API -------------------------------------------------------------

def compute_indicators(df: pd.DataFrame) -> dict:
    """
    Compute the latest indicator snapshot from an OHLCV DataFrame
    (columns: Open/High/Low/Close/Volume). Missing look-backs (e.g. SMA200 on a
    short history) come back as None rather than fabricated.
    """
    close = df["Close"]
    volume = df["Volume"]
    price = _num(close.iloc[-1])

    rsi14 = _num(rsi(close).iloc[-1])
    macd_line, signal_line, hist = macd(close)
    sma50 = _num(sma(close, 50).iloc[-1])
    sma200 = _num(sma(close, 200).iloc[-1])
    up, mid, low = bollinger(close)

    # volume trend: latest vs 20-day average
    vol_avg20 = volume.rolling(20).mean().iloc[-1]
    vol_latest = float(volume.iloc[-1])
    vol_change = _num((vol_latest / vol_avg20 - 1) * 100) if vol_avg20 else None

    return {
        "price": price,
        "rsi14": _num(rsi14),
        "macd": {
            "macd": _num(macd_line.iloc[-1]),
            "signal": _num(signal_line.iloc[-1]),
            "hist": _num(hist.iloc[-1]),
        },
        "sma50": sma50,
        "sma200": sma200,
        "bollinger": {
            "upper": _num(up.iloc[-1]),
            "middle": _num(mid.iloc[-1]),
            "lower": _num(low.iloc[-1]),
        },
        "volume": int(vol_latest),
        "volume_vs_20d_pct": vol_change,
        # convenience flags (deterministic, used by the UI/agents downstream).
        # Tri-state on purpose: None means "the average isn't available" (e.g. under
        # 200 days of history), which is NOT the same claim as "price is below it".
        # A bare False here used to be sent to the analysis agent as an exact fact,
        # so a short-history stock could be told (and could then assert) it was
        # "below its 200-day average" when no such average exists at all.
        "above_sma50": (price > sma50) if (price is not None and sma50 is not None) else None,
        "above_sma200": (price > sma200) if (price is not None and sma200 is not None) else None,
    }
