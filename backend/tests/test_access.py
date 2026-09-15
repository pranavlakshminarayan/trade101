"""Pre-share fix: the access-token gate + daily cap on /analyze and /ask
(services/access.py). These guard the two Claude-spending endpoints only —
/research, /ecosystem, /patterns stay open and free."""
from fastapi.testclient import TestClient

import app
from services import access

client = TestClient(app.app)


def _reset_usage():
    access._usage["day"] = None
    access._usage["count"] = 0


def test_gate_is_a_noop_when_no_token_configured(monkeypatch):
    monkeypatch.delenv("TRADE101_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)
    monkeypatch.setattr(app.orchestrator.marketdata, "get", lambda *a, **k: None)
    _reset_usage()
    r = client.get("/analyze/NVDA")
    assert r.status_code in (200, 404)  # never 401 — no token means no gate


def test_missing_or_wrong_token_is_rejected(monkeypatch):
    monkeypatch.setenv("TRADE101_ACCESS_TOKEN", "correct-horse")
    _reset_usage()
    r = client.get("/analyze/NVDA")
    assert r.status_code == 401
    r2 = client.get("/analyze/NVDA", headers={"X-Access-Token": "wrong"})
    assert r2.status_code == 401


def test_correct_token_passes_the_gate(monkeypatch):
    monkeypatch.setenv("TRADE101_ACCESS_TOKEN", "correct-horse")
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)
    monkeypatch.setattr(app.orchestrator.marketdata, "get", lambda *a, **k: None)
    _reset_usage()
    r = client.get("/analyze/NVDA", headers={"X-Access-Token": "correct-horse"})
    assert r.status_code in (200, 404)  # past the gate; normal degrade path


def test_daily_cap_blocks_once_exhausted(monkeypatch):
    monkeypatch.delenv("TRADE101_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("TRADE101_DAILY_CAP", "1")
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)
    monkeypatch.setattr(app.orchestrator.marketdata, "get", lambda *a, **k: None)
    _reset_usage()
    r1 = client.get("/analyze/NVDA")
    assert r1.status_code in (200, 404)
    r2 = client.get("/analyze/NVDA")
    assert r2.status_code == 429


def test_ask_is_gated_too(monkeypatch):
    monkeypatch.setenv("TRADE101_ACCESS_TOKEN", "correct-horse")
    _reset_usage()
    r = client.post("/ask/NVDA", json={"question": "What is RSI?"})
    assert r.status_code == 401
