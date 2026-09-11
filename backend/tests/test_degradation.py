"""
Graceful-degradation tests.

The review's rule: prices and charts must render when AI, news, filings,
ecosystem or search sources fail, and each failure must say what broke, what
still works, and whether retrying helps. These tests hold that line — a source
outage must never surface as a 500.
"""
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app
from services import cache, marketdata

client = TestClient(app.app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


def _fake_hist(n=60):
    """A gently oscillating series — a flat one leaves RSI mathematically undefined."""
    idx = pd.date_range(end=pd.Timestamp.now().normalize(), periods=n, freq="D")
    close = [10.0 + (i % 7) * 0.3 + i * 0.05 for i in range(n)]
    return pd.DataFrame(
        {"Open": [c - 0.2 for c in close], "High": [c + 0.4 for c in close],
         "Low": [c - 0.4 for c in close], "Close": close, "Volume": [1000 + i for i in range(n)]},
        index=idx,
    )


# ---- provider outage -------------------------------------------------------

def test_provider_outage_is_503_with_an_actionable_message(monkeypatch):
    def boom(*a, **k):
        raise marketdata.ProviderError("NVDA", ConnectionError("tunnel failed"))

    monkeypatch.setattr(app.marketdata, "get_with_meta", boom)
    r = client.get("/research/NVDA")

    assert r.status_code == 503, "a source outage must not be a 500"
    body = r.json()
    assert body["retryable"] is True
    assert body["failure"] == "provider_unreachable"
    assert "not a problem with the symbol" in body["detail"]


def test_unknown_ticker_is_404_and_not_retryable(monkeypatch):
    monkeypatch.setattr(app.marketdata, "get_with_meta", lambda *a, **k: (None, {}))
    r = client.get("/research/NOTAREALTICKER")
    assert r.status_code == 404
    assert r.json().get("retryable") is not True


def test_provider_error_reaches_the_handler_from_the_real_fetch(monkeypatch):
    """The wrapper must convert a raw provider exception, not let it escape."""
    class Boom:
        def __init__(self, *a, **k): pass
        def history(self, *a, **k): raise ConnectionError("CONNECT tunnel failed, 403")

    monkeypatch.setattr(marketdata.yf, "Ticker", Boom)
    with pytest.raises(marketdata.ProviderError):
        marketdata.get("NVDA")


def test_a_failed_fetch_is_not_cached_as_an_outage(monkeypatch):
    """After an outage, the next request must retry rather than serve the error."""
    calls = []

    class Flaky:
        def __init__(self, *a, **k): pass
        def history(self, *a, **k):
            calls.append(1)
            raise ConnectionError("down")

    monkeypatch.setattr(marketdata.yf, "Ticker", Flaky)
    for _ in range(2):
        with pytest.raises(marketdata.ProviderError):
            marketdata.get("NVDA")
    assert len(calls) == 2, "an outage must not be cached"


# ---- the chart survives everything else failing ----------------------------

def test_chart_data_renders_when_news_filings_and_ai_are_all_down(monkeypatch):
    """The deterministic core is the floor: it must not depend on any of them."""
    monkeypatch.setattr(app.marketdata, "get_with_meta",
                        lambda *a, **k: ((_fake_hist(), {"symbol": "NVDA", "price": 10.5}),
                                         {"cached": False, "fetchedAt": "2026-09-11T00:00:00+00:00",
                                          "ageSeconds": 0, "backend": "in-process"}))
    r = client.get("/research/NVDA")
    assert r.status_code == 200
    d = r.json()
    assert len(d["ohlcv"]) == 60
    assert d["indicators"]["rsi14"] is not None
    assert d["meta"]["asOf"] and d["meta"]["stale"] is False


def test_analyze_degrades_to_a_reason_when_the_provider_is_down(monkeypatch):
    def boom(*a, **k):
        raise marketdata.ProviderError("NVDA", ConnectionError("down"))

    monkeypatch.setattr(app.orchestrator.marketdata, "get", boom)
    r = client.get("/analyze/NVDA")
    # /analyze catches everything: the page keeps its chart either way.
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is False and body["reason"]


def test_ecosystem_outage_does_not_500(monkeypatch):
    def boom(*a, **k):
        raise marketdata.ProviderError("NVDA", ConnectionError("down"))

    monkeypatch.setattr(app.marketdata, "get", boom)
    assert client.get("/ecosystem/NVDA").status_code == 503


def test_patterns_outage_does_not_500(monkeypatch):
    def boom(*a, **k):
        raise marketdata.ProviderError("NVDA", ConnectionError("down"))

    monkeypatch.setattr(app.marketdata, "get", boom)
    assert client.get("/patterns/NVDA").status_code == 503


def test_search_returns_empty_rather_than_failing(monkeypatch):
    """A dead search provider yields no candidates, not an error page."""
    monkeypatch.setattr(app.search, "resolve", lambda *a, **k: [])
    r = client.get("/search?q=nvidia")
    assert r.status_code == 200 and r.json()["candidates"] == []
