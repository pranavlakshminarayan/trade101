"""Staleness tests — a closed market and a broken feed must not look alike."""
import pandas as pd

from services import marketdata


def _hist(last: pd.Timestamp, n: int = 3) -> pd.DataFrame:
    idx = pd.date_range(end=last, periods=n, freq="D")
    return pd.DataFrame({"Close": [1.0] * n}, index=idx)


def test_recent_daily_bar_is_not_stale():
    f = marketdata.freshness(_hist(pd.Timestamp.now()), "1d")
    assert f["stale"] is False and f["asOf"] is not None
    assert f["ageSeconds"] < 60


def test_long_gap_is_flagged_stale_with_an_explanation():
    f = marketdata.freshness(_hist(pd.Timestamp.now() - pd.Timedelta(days=20)), "1d")
    assert f["stale"] is True
    assert "market may be closed" in f["note"] and "feed may be behind" in f["note"]


def test_weekend_gap_on_daily_bars_is_not_stale():
    """A normal long weekend must not be reported as a broken feed."""
    f = marketdata.freshness(_hist(pd.Timestamp.now() - pd.Timedelta(days=3)), "1d")
    assert f["stale"] is False


def test_intraday_uses_a_tighter_bound_than_daily():
    hist = _hist(pd.Timestamp.now() - pd.Timedelta(hours=8))
    assert marketdata.freshness(hist, "5m")["stale"] is True
    assert marketdata.freshness(hist, "1d")["stale"] is False


def test_empty_history_is_dated_honestly():
    f = marketdata.freshness(pd.DataFrame(), "1d")
    assert f["asOf"] is None and f["stale"] is True
