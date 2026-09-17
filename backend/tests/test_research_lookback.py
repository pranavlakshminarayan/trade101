"""GET /research/{ticker} — indicator lookback (user-reported 2026-09-17):
SMA200 needs 200 bars of history before it produces a single point. Fetching
only the DISPLAY window (e.g. exactly 5 days for the "5D" chart tab) left no
room for that lookback, so SMA200 only appeared over whatever trailing
sliver of the window happened to have 200+ bars behind it — cut short on
1Y, gone entirely on 5D/1D. app._fetch_with_lookback fetches more history
than it displays so indicators are fully populated across the ENTIRE
visible window, not just its tail."""
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

import app

client = TestClient(app.app)


def _hist(n, freq="D"):
    idx = pd.date_range("2020-01-01", periods=n, freq=freq)
    close = pd.Series(100 + np.cumsum(np.random.default_rng(11).normal(0, 1, n)), index=idx)
    return pd.DataFrame({
        "Open": close, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": pd.Series([1_000_000] * n, index=idx),
    })


def test_short_display_window_still_gets_a_bigger_fetch_for_lookback(monkeypatch):
    # Simulate exactly the 5D/15m case: the DISPLAY window is only 130 bars
    # (too short for SMA200's 200-bar requirement on its own), but the
    # lookback fetch should request more (here faked as 400 bars) so SMA200
    # is defined across the whole 130-bar display, not just a trailing sliver.
    requested = {}

    def fake_get(ticker, period=None, interval=None):
        requested["period"] = period
        requested["interval"] = interval
        n = 400 if period == "60d" else 130  # the "wrong" (old, buggy) fetch would be too short
        h = _hist(n, freq="15min")
        quote = {"symbol": ticker, "name": "Test Co", "currency": "USD", "price": 100.0}
        return h, quote

    monkeypatch.setattr(app.marketdata, "get", fake_get)
    r = client.get("/research/TEST?period=5d&interval=15m")
    assert r.status_code == 200
    body = r.json()

    # The backend must have requested the LARGER lookback period, not the
    # short display period directly.
    assert requested["period"] == "60d"
    # The display window itself is unchanged (130 bars, matching the
    # original 5D behavior) even though a bigger window was fetched.
    assert len(body["ohlcv"]) == 130
    # SMA200 must now be defined for EVERY displayed bar, not just a tail
    # sliver — this is the actual regression: with only 130 bars fetched
    # (the old behavior), SMA200 would be entirely empty.
    assert len(body["indicatorSeries"]["sma200"]) == 130


def test_indicator_series_points_are_trimmed_to_the_display_window(monkeypatch):
    # The extra lookback bars must never leak into the response — they exist
    # only to make the DISPLAYED bars' indicators correct.
    def fake_get(ticker, period=None, interval=None):
        n = 500 if period == "2y" else 250
        h = _hist(n, freq="D")
        quote = {"symbol": ticker, "name": "Test Co", "currency": "USD", "price": 100.0}
        return h, quote

    monkeypatch.setattr(app.marketdata, "get", fake_get)
    r = client.get("/research/TEST?period=1y&interval=1d")
    body = r.json()
    assert len(body["ohlcv"]) == 251
    ohlcv_times = {b["time"] for b in body["ohlcv"]}
    for pt in body["indicatorSeries"]["sma50"]:
        assert pt["time"] in ohlcv_times, "an indicator point outside the display window leaked through"


def test_unrecognized_period_interval_combo_is_unaffected(monkeypatch):
    # Any (period, interval) pair not in the known short-window map is passed
    # straight through — no surprise fetch-size change for combos this fix
    # wasn't scoped to touch.
    requested = {}

    def fake_get(ticker, period=None, interval=None):
        requested["period"] = period
        h = _hist(180, freq="D")
        quote = {"symbol": ticker, "name": "Test Co", "currency": "USD", "price": 100.0}
        return h, quote

    monkeypatch.setattr(app.marketdata, "get", fake_get)
    r = client.get("/research/TEST?period=6mo&interval=1d")
    assert r.status_code == 200
    assert requested["period"] == "6mo"        # not silently rewritten
    assert len(r.json()["ohlcv"]) == 180        # no trimming applied
