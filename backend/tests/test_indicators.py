"""
Exact-number tests for the indicator engine. These are the guardrail behind
"numbers are exact": if any indicator drifts, CI fails.

Run from the `backend/` directory:  .venv/Scripts/python.exe -m pytest -q
"""
import numpy as np
import pandas as pd
import pytest

from services import indicators as ind


def test_sma_exact():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    assert ind.sma(s, 3).iloc[-1] == pytest.approx(4.0)   # mean(3,4,5)


def test_ema_constant_is_constant():
    s = pd.Series([7.0] * 30)
    assert ind.ema(s, 12).iloc[-1] == pytest.approx(7.0)


def test_rsi_all_gains_is_100():
    s = pd.Series(np.arange(1, 30, dtype=float))          # strictly increasing
    assert ind.rsi(s).iloc[-1] == pytest.approx(100.0)


def test_rsi_all_losses_is_0():
    s = pd.Series(np.arange(30, 1, -1, dtype=float))       # strictly decreasing
    assert ind.rsi(s).iloc[-1] == pytest.approx(0.0)


def test_rsi_within_bounds():
    rng = np.random.default_rng(42)
    s = pd.Series(100 + np.cumsum(rng.normal(0, 1, 200)))
    r = ind.rsi(s).dropna()
    assert r.between(0, 100).all()


def test_macd_constant_is_zero():
    s = pd.Series([50.0] * 60)
    macd_line, signal, hist = ind.macd(s)
    assert macd_line.iloc[-1] == pytest.approx(0.0)
    assert signal.iloc[-1] == pytest.approx(0.0)
    assert hist.iloc[-1] == pytest.approx(0.0)


def test_bollinger_constant_collapses():
    s = pd.Series([20.0] * 40)
    up, mid, low = ind.bollinger(s)
    assert up.iloc[-1] == pytest.approx(20.0)
    assert mid.iloc[-1] == pytest.approx(20.0)
    assert low.iloc[-1] == pytest.approx(20.0)


def _synthetic_ohlcv(n=260):
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    close = pd.Series(100 + np.cumsum(np.random.default_rng(1).normal(0.1, 1, n)), index=idx)
    return pd.DataFrame(
        {"Open": close, "High": close * 1.01, "Low": close * 0.99,
         "Close": close, "Volume": pd.Series([1_000_000] * n, index=idx)}
    )


def test_compute_indicators_shape_and_bounds():
    df = _synthetic_ohlcv()
    out = ind.compute_indicators(df)
    for key in ("price", "rsi14", "macd", "sma50", "sma200", "bollinger", "volume"):
        assert key in out
    assert 0 <= out["rsi14"] <= 100
    assert out["sma200"] is not None          # 260 rows → SMA200 exists
    assert out["price"] == pytest.approx(round(float(df["Close"].iloc[-1]), 4))
    assert isinstance(out["above_sma50"], bool)


def test_short_history_returns_none_not_fabricated():
    df = _synthetic_ohlcv(n=100)              # enough for SMA50, too short for SMA200
    out = ind.compute_indicators(df)
    assert out["sma200"] is None              # honest None, never invented
    # Regression (docs/AUDIT.md finding C2): when the average itself is unknown,
    # "above the average" must ALSO be unknown (None) — not silently False. A
    # bare False here used to reach the analysis agent as an exact fact, letting
    # it assert e.g. "price is below its 200-day average" on a stock that has no
    # 200-day average at all.
    assert out["above_sma200"] is None
    assert out["sma50"] is not None
    assert isinstance(out["above_sma50"], bool)  # SMA50 IS available at 100 rows
