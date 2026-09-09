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
