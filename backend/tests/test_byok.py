"""BYOK (bring-your-own-key), added 2026-09-17 to replace the shared
TRADE101_ACCESS_TOKEN + daily-cap gate: each visitor supplies their OWN
Anthropic API key (X-Anthropic-Key header), so an open, shared link carries
zero cost risk to the app owner. See agents/llm.py."""
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

import app
from agents import llm

client = TestClient(app.app)


def _fake_hist(n=60):
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    close = pd.Series(100 + np.cumsum(np.random.default_rng(3).normal(0, 1, n)), index=idx)
    return pd.DataFrame({
        "Open": close, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": pd.Series([1_000_000] * n, index=idx),
    })


def _patch_gather(monkeypatch, ticker="BYOKTEST"):
    app.orchestrator.cache.clear()
    quote = {"symbol": ticker, "name": "BYOK Test Co", "currency": "USD"}
    monkeypatch.setattr(app.orchestrator.marketdata, "get", lambda *a, **k: (_fake_hist(), quote))
    monkeypatch.setattr(app.orchestrator.news, "get_news", lambda *a, **k: ([], None))
    monkeypatch.setattr(app.orchestrator.news, "get_recent_filings", lambda *a, **k: ([], None))
    monkeypatch.setattr(app.orchestrator.company, "get_profile", lambda *a, **k: {"peers": []})


def test_no_key_anywhere_raises_missing_key_error(monkeypatch):
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)
    try:
        llm._resolve_key(None)
        assert False, "expected MissingKeyError"
    except llm.MissingKeyError:
        pass


def test_client_key_is_used_when_supplied(monkeypatch):
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)
    assert llm._resolve_key("sk-visitor-key") == "sk-visitor-key"


def test_env_var_is_a_local_dev_fallback_when_no_client_key(monkeypatch):
    monkeypatch.setenv("TRADE101_ANALYSIS_KEY", "sk-dev-key")
    assert llm._resolve_key(None) == "sk-dev-key"
    assert llm._resolve_key("") == "sk-dev-key"


def test_client_key_takes_priority_over_the_env_fallback(monkeypatch):
    monkeypatch.setenv("TRADE101_ANALYSIS_KEY", "sk-dev-key")
    assert llm._resolve_key("sk-visitor-key") == "sk-visitor-key"


def test_analyze_endpoint_passes_the_visitor_header_through_to_the_llm_call(monkeypatch):
    # No TRADE101_ANALYSIS_KEY set - if the header weren't threaded all the way
    # down to llm.call, this would degrade to available:false (MissingKeyError)
    # instead of reaching the (faked) LLM call with the visitor's own key.
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)
    _patch_gather(monkeypatch)
    seen = {}

    def fake_call(client_key, system, user, **kw):
        seen["key"] = client_key
        return ('{"momentum": {"lean": "neutral", "confidence": "low", "summary": "s", '
                '"evidence": []}, "news_inference": {"summary": "", "sources": []}, "learning_note": ""}')

    monkeypatch.setattr(llm, "call", fake_call)
    r = client.get("/analyze/BYOKTEST", headers={"X-Anthropic-Key": "sk-visitor-abc"})
    assert r.status_code == 200
    assert r.json()["available"] is True
    assert seen["key"] == "sk-visitor-abc"  # the VISITOR's key reached the LLM call


def test_analyze_degrades_gracefully_with_no_key_at_all(monkeypatch):
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)
    _patch_gather(monkeypatch, ticker="BYOKTEST2")
    r = client.get("/analyze/BYOKTEST2")  # no X-Anthropic-Key header
    assert r.status_code == 200
    assert r.json()["available"] is False


def test_invalid_visitor_key_gets_a_friendly_reason_not_a_raw_error(monkeypatch):
    # A mistyped/expired key is now the MOST LIKELY failure mode (a visitor's
    # own key, not a server misconfiguration) - it must read as an actionable
    # message, not Anthropic's raw JSON error body.
    import anthropic
    import httpx

    _patch_gather(monkeypatch, ticker="BYOKTEST3")

    def fake_call(*a, **k):
        resp = httpx.Response(401, request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
        raise anthropic.AuthenticationError(
            "invalid x-api-key", response=resp, body={"error": {"message": "invalid x-api-key"}},
        )

    monkeypatch.setattr(app.llm, "call", fake_call)
    r = client.get("/analyze/BYOKTEST3", headers={"X-Anthropic-Key": "sk-ant-wrong"})
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is False
    assert "rejected" in body["reason"].lower()
    assert "invalid x-api-key" not in body["reason"]  # no raw SDK error text leaked


def test_ask_endpoint_has_no_shared_gate_any_more(monkeypatch):
    monkeypatch.setattr(app.orchestrator.marketdata, "get", lambda *a, **k: None)
    r = client.post("/ask/NVDA", json={"question": "What is RSI?"},
                     headers={"X-Anthropic-Key": "sk-visitor-abc"})
    # Previously this class of request could be blocked by the shared-token
    # gate (401) before ever reaching the ticker lookup. Now it reaches the
    # normal not-found path - proof the removed gate isn't blocking it.
    assert r.status_code == 404
