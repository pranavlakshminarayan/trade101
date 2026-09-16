"""GET /news/{ticker} — the free, deterministic news endpoint added for
docs/AUDIT.md finding H3: news must reach the UI without going through the
paid /analyze call, and without needing a Claude key at all."""
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

import app

client = TestClient(app.app)


def _fake_hist(n=60):
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    close = pd.Series(100 + np.cumsum(np.random.default_rng(3).normal(0, 1, n)), index=idx)
    return pd.DataFrame({
        "Open": close, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": pd.Series([1_000_000] * n, index=idx),
    })


def _patch_gather(monkeypatch, news_items=None):
    app.orchestrator.cache.clear()  # tests must not see another test's cached bundle
    quote = {"symbol": "NEWSTEST", "name": "News Test Co", "currency": "USD"}
    monkeypatch.setattr(app.orchestrator.marketdata, "get", lambda *a, **k: (_fake_hist(), quote))
    monkeypatch.setattr(app.orchestrator.news, "get_news", lambda *a, **k: (news_items or [], None))
    monkeypatch.setattr(app.orchestrator.news, "get_recent_filings", lambda *a, **k: ([], None))
    monkeypatch.setattr(app.orchestrator.company, "get_profile",
                         lambda *a, **k: {"sector": "Technology", "industry": "Software", "peers": []})


def test_news_404_when_no_market_data(monkeypatch):
    monkeypatch.setattr(app.orchestrator.marketdata, "get", lambda *a, **k: None)
    r = client.get("/news/NOPE")
    assert r.status_code == 404


def test_news_returns_feed_with_no_claude_key_at_all(monkeypatch):
    # The entire point of this endpoint: it must work with ZERO analysis key
    # configured — unlike /analyze, which degrades to available:false.
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)
    _patch_gather(monkeypatch, news_items=[
        {"headline": "News Test Co posts results", "summary": "Coverage of NEWSTEST."},
    ])
    r = client.get("/news/NEWSTEST")
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert body["ticker"] == "NEWSTEST"
    assert len(body["feed"]) == 1
    assert "sourcing" in body and "filings" in body


def test_news_is_not_gated_by_the_access_token(monkeypatch):
    # Contrast with /analyze and /ask: /news is deterministic and must stay
    # free/open even when the pre-share access guard is configured.
    monkeypatch.setenv("TRADE101_ACCESS_TOKEN", "secret123")
    _patch_gather(monkeypatch)
    r = client.get("/news/NEWSTEST")  # no X-Access-Token header sent
    assert r.status_code == 200
    assert r.json()["available"] is True


def test_news_and_analyze_share_one_gather_call(monkeypatch):
    # orchestrator.gather() is TTL-cached; hitting /news first must not force
    # a second fetch when /analyze runs afterward for the same ticker.
    calls = {"n": 0}
    quote = {"symbol": "SHARE", "name": "Share Co", "currency": "USD"}

    def counting_get(*a, **k):
        calls["n"] += 1
        return (_fake_hist(), quote)

    app.orchestrator.cache.clear()
    monkeypatch.setattr(app.orchestrator.marketdata, "get", counting_get)
    monkeypatch.setattr(app.orchestrator.news, "get_news", lambda *a, **k: ([], None))
    monkeypatch.setattr(app.orchestrator.news, "get_recent_filings", lambda *a, **k: ([], None))
    monkeypatch.setattr(app.orchestrator.company, "get_profile", lambda *a, **k: {"peers": []})
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)

    client.get("/news/SHARE")
    client.get("/analyze/SHARE")
    assert calls["n"] == 1
