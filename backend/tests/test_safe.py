"""Regression tests for the Phase-1 API-key leak (services/safe + news error paths)."""
import httpx
import pytest

from services import news
from services.safe import redact_secrets


def test_redact_strips_token_query_param(monkeypatch):
    monkeypatch.setenv("TRADE101_NEWS_KEY", "SECRET_FINNHUB_KEY_123")
    leaked = ("Client error '403 Forbidden' for url "
              "'https://finnhub.io/api/v1/company-news?symbol=7974.T&token=SECRET_FINNHUB_KEY_123'")
    out = redact_secrets(leaked)
    assert "SECRET_FINNHUB_KEY_123" not in out
    assert "token=<redacted>" in out


def test_redact_strips_apikey_and_key_variants():
    for text in ("...apikey=abc123def...", "...api_key=abc123def...", "...key=abc123def..."):
        assert "abc123def" not in redact_secrets(text)


def test_news_error_never_contains_key(monkeypatch):
    """Even when the provider raises with the URL in its message, no key escapes."""
    monkeypatch.setenv("TRADE101_NEWS_KEY", "SECRET_FINNHUB_KEY_123")

    def boom(*a, **k):
        raise httpx.HTTPError(
            "Client error for url "
            "'https://finnhub.io/api/v1/company-news?symbol=X&token=SECRET_FINNHUB_KEY_123'"
        )

    monkeypatch.setattr(news.httpx, "get", boom)
    items, note = news.get_company_news("7974.T")
    assert items == []
    assert "SECRET_FINNHUB_KEY_123" not in (note or "")
    assert "token=" not in (note or "")


def test_news_403_is_friendly_and_keyless(monkeypatch):
    monkeypatch.setenv("TRADE101_NEWS_KEY", "SECRET_FINNHUB_KEY_123")

    class Resp:
        status_code = 403

        def raise_for_status(self):
            raise httpx.HTTPStatusError("403", request=None, response=None)

        def json(self):
            return []

    monkeypatch.setattr(news.httpx, "get", lambda *a, **k: Resp())
    items, note = news.get_company_news("7974.T")
    assert items == []
    assert "SECRET_FINNHUB_KEY_123" not in (note or "")
    assert note  # a friendly explanation, not empty
