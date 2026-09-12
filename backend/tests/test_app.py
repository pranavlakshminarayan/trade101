"""Endpoint smoke tests (TestClient, no network / no API keys required)."""
from fastapi.testclient import TestClient

import app

client = TestClient(app.app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_degrades_without_key(monkeypatch):
    # With no analysis key, /analyze must degrade gracefully (never 500).
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)
    # patch marketdata so we don't hit the network
    monkeypatch.setattr(app.orchestrator.marketdata, "get", lambda *a, **k: None)
    r = client.get("/analyze/NVDA")
    # unknown-data path → 404 handled; key path → available:false. Either way, no 500.
    assert r.status_code in (200, 404)


def test_provider_error_note_never_leaks_the_api_key(monkeypatch):
    """Provider error notes are surfaced in the UI — they must not carry the key."""
    from services import news

    monkeypatch.setenv("TRADE101_NEWS_KEY", "secretkey123456")
    err = Exception(
        "Client error '403 Forbidden' for url "
        "'https://finnhub.io/api/v1/company-news?symbol=7974.T&token=secretkey123456'"
    )
    safe = news._safe_err(err)
    assert "secretkey123456" not in safe
    assert "token=***" in safe


def test_non_us_news_403_explains_instead_of_leaking(monkeypatch):
    """A 403 from the free tier gets a plain explanation, no URL and no key."""
    import httpx
    from services import news

    monkeypatch.setenv("TRADE101_NEWS_KEY", "secretkey123456")

    def boom(*a, **k):
        raise httpx.HTTPStatusError(
            "Client error '403 Forbidden' for url "
            "'https://finnhub.io/api/v1/company-news?token=secretkey123456'",
            request=None,
            response=None,
        )

    monkeypatch.setattr(news.httpx, "get", boom)
    items, note = news.get_company_news("7974.T")
    assert items == []
    assert "secretkey123456" not in note
    assert "free tier" in note
