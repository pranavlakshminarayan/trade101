"""
End-to-end integration — one learner's whole journey through the app.

Every other test file checks a part in isolation. This one walks the path a
person actually takes, in order, against a single stubbed market, and asserts
the properties that must hold ACROSS features rather than inside any one of
them:

  * every panel that asserts something agrees on the same as-of timestamp
  * nothing anywhere tells the user to buy, sell or hold
  * the deterministic core survives every optional source failing at once
"""
import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app
from services import cache, storage

client = TestClient(app.app, raise_server_exceptions=False)

# Words the app has promised never to say to a user.
ADVICE_WORDS = ("you should buy", "you should sell", "we recommend", "price target",
                "guaranteed", "will rise", "will fall", "sure thing")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("TRADE101_DB", str(tmp_path / "t.db"))
    monkeypatch.delenv("TRADE101_ANALYSIS_KEY", raising=False)
    monkeypatch.delenv("TRADE101_NEWS_KEY", raising=False)
    storage.reset_for_tests()
    cache.clear()
    yield
    storage.reset_for_tests()
    cache.clear()


def _hist(n=400):
    idx = pd.date_range(end=pd.Timestamp.now().normalize(), periods=n, freq="D")
    close = [80 + i * 0.15 + (i % 13) * 0.4 for i in range(n)]
    return pd.DataFrame(
        {"Open": [c - 0.3 for c in close], "High": [c + 0.6 for c in close],
         "Low": [c - 0.6 for c in close], "Close": close,
         "Volume": [50_000 + (i % 7) * 1000 for i in range(n)]}, index=idx)


@pytest.fixture
def market(monkeypatch):
    """One stubbed stock, wired into every module that reaches for market data."""
    hist = _hist()
    quote = {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": 139.75,
             "changePercent": 1.24, "currency": "USD", "exchange": "NasdaqGS",
             "previousClose": 138.04, "change": 1.71, "marketCap": 3.4e12}

    def get(ticker, period="1y", interval="1d"):
        return (hist, quote)

    for mod in (app.marketdata, app.replay.marketdata, app.watchlist.marketdata,
                app.compare_svc.marketdata, app.orchestrator.marketdata,
                app.lenses and app.marketdata):
        monkeypatch.setattr(mod, "get", get, raising=False)
    monkeypatch.setattr(app.marketdata, "get_with_meta",
                        lambda *a, **k: ((hist, quote),
                                         {"cached": False, "fetchedAt": "2026-09-11T00:00:00+00:00",
                                          "ageSeconds": 0, "backend": "in-process"}))

    # Keep the suite hermetic: without these, SEC EDGAR and Yahoo's fundamentals
    # endpoint are contacted for real and the tests wait on network timeouts.
    monkeypatch.setattr(app.news_svc, "get_recent_filings", lambda *a, **k: ([], None))
    monkeypatch.setattr(app.fundamentals, "get_fundamentals",
                        lambda t: {"coverage": {"level": "ok"},
                                   "revenue": {"changePercent": 12.0, "series": []},
                                   "netIncome": {"changePercent": 9.0}, "cashFlow": {},
                                   "valuation": {"trailingPE": 40.0}, "margins": {},
                                   "earnings": {"nextDate": "2026-11-19T00:00:00"},
                                   "meta": {"notes": []}})
    monkeypatch.setattr(app.compare_svc.fund_svc, "get_fundamentals",
                        app.fundamentals.get_fundamentals)
    monkeypatch.setattr(app.compare_svc.company_svc, "get_profile",
                        lambda t: {"sector": "Technology", "beta": 1.6, "marketCap": 3.4e12})
    monkeypatch.setattr(app.relationships.company, "get_profile",
                        lambda t: {"peers": ["AMD", "INTC"], "sector": "Technology"})
    return hist, quote


# ---- the journey -----------------------------------------------------------

def test_the_whole_research_page_agrees_on_one_as_of(market):
    """The coherence promise: chart, patterns and lenses cannot describe
    different moments in time."""
    research = client.get("/research/NVDA").json()
    patterns = client.get("/patterns/NVDA").json()
    lens = client.get("/lenses/NVDA").json()

    as_of = research["meta"]["asOf"]
    assert as_of
    assert patterns["meta"]["asOf"] == as_of
    assert lens["asOf"] == as_of


def test_research_renders_with_no_api_keys_at_all(market):
    """No Claude key, no Finnhub key — the deterministic core must still work."""
    r = client.get("/research/NVDA")
    assert r.status_code == 200
    d = r.json()
    assert d["quote"]["price"] == 139.75
    assert d["indicators"]["rsi14"] is not None
    assert len(d["ohlcv"]) == 400

    # ...and the AI degrades to a reason rather than an error.
    a = client.get("/analyze/NVDA").json()
    assert a["available"] is False and a["reason"]


def test_every_learner_facing_endpoint_avoids_advice_language(market):
    """A single scan across everything a learner reads on a normal visit."""
    bodies = []
    for path in ("/research/NVDA", "/patterns/NVDA", "/lenses/NVDA", "/graph/NVDA",
                 "/fundamentals/NVDA", "/replay/NVDA", "/replay/NVDA/reveal",
                 "/practice", "/watchlist?refresh=false"):
        r = client.get(path)
        assert r.status_code in (200, 404), f"{path} returned {r.status_code}"
        if r.status_code == 200:
            bodies.append((path, json.dumps(r.json()).lower()))

    for path, blob in bodies:
        for phrase in ADVICE_WORDS:
            assert phrase not in blob, f"{path} contained advice language: {phrase!r}"


def test_a_learner_can_study_then_replay_then_find_both_in_the_journal(market):
    # 1. Study the live chart — commit a read.
    study = client.post("/journal", json={
        "ticker": "NVDA", "kind": "study", "lean": "bullish", "confidence": "moderate",
        "hypothesis": "Price is above both averages and momentum is not yet stretched.",
        "evidence": ["ind:sma50", "ind:rsi14"], "asOf": "2026-09-11T00:00:00",
    })
    assert study.status_code == 200

    # 2. A replay on a hidden window — commit a second read before revealing.
    setup = client.get("/replay/NVDA").json()
    assert setup["available"] is True and "outcome" not in setup
    client.post("/journal", json={
        "ticker": "NVDA", "kind": "replay", "lean": "bearish",
        "hypothesis": "Volume was thinning into the highs, so the push looked tired.",
        "asOf": setup["asOf"],
    })
    reveal = client.get("/replay/NVDA/reveal").json()
    assert "outcome" in reveal and "one sample" in reveal["caveat"].lower()

    # 3. Both reads are in the journal, newest first, with their own leans intact.
    entries = client.get("/journal?ticker=NVDA").json()["entries"]
    assert len(entries) == 2
    assert {e["kind"] for e in entries} == {"study", "replay"}
    assert {e["lean"] for e in entries} == {"bullish", "bearish"}


def test_a_learner_can_watch_compare_and_practise_in_one_session(market):
    assert client.post("/watchlist", json={"ticker": "NVDA", "level": 150,
                                           "note": "watching the capex cycle"}).status_code == 200
    wl = client.get("/watchlist").json()
    assert wl["items"][0]["ticker"] == "NVDA" and wl["items"][0]["price"] == 139.75

    cmp_body = client.get("/compare?tickers=NVDA,AMD").json()
    assert len(cmp_body["entries"]) == 2
    assert all(e["series"][0]["value"] == 100.0 for e in cmp_body["entries"])

    opened = client.post("/practice", json={
        "ticker": "NVDA", "price": 130, "quantity": 5,
        "reason": "Testing whether the trend read survives the next earnings date."}).json()
    lab = client.get("/practice").json()
    assert lab["entries"][0]["id"] == opened["id"]
    assert "HYPOTHETICAL" in lab["disclaimer"]


def test_the_page_survives_every_optional_source_failing_at_once(market, monkeypatch):
    """News down, filings down, fundamentals down, AI keyless — chart still exact."""
    monkeypatch.setattr(app.news_svc, "get_news",
                        lambda *a, **k: ([], "News provider error: down"))
    monkeypatch.setattr(app.news_svc, "get_recent_filings",
                        lambda *a, **k: ([], "EDGAR error: down"))
    monkeypatch.setattr(app.fundamentals, "get_fundamentals",
                        lambda t: {"coverage": {"level": "none"}, "revenue": {}, "netIncome": {},
                                   "cashFlow": {}, "valuation": {}, "earnings": {},
                                   "margins": {}, "meta": {"notes": ["all sources down"]}})

    research = client.get("/research/NVDA")
    assert research.status_code == 200
    assert research.json()["indicators"]["rsi14"] is not None

    lens = client.get("/lenses/NVDA")
    assert lens.status_code == 200
    by_id = {l["id"]: l for l in lens.json()["lenses"]}
    # The lenses that need the missing sources say so instead of guessing.
    assert by_id["long-term"]["lean"] == "unknown"
    assert by_id["event-driven"]["conflicts"]
    # The lens that needs only price still works.
    assert by_id["trend"]["lean"] in ("bullish", "bearish", "mixed")


def test_usage_ledger_records_nothing_when_no_ai_call_was_made(market):
    client.get("/research/NVDA")
    client.get("/lenses/NVDA")
    summary = client.get("/usage").json()
    assert summary["available"] is True
    assert summary["total"]["calls"] == 0, "deterministic endpoints must cost nothing"


def test_cache_prevents_a_repeat_visit_from_refetching(market, monkeypatch):
    calls = []
    real = app.marketdata.get_with_meta

    def counting(*a, **k):
        calls.append(1)
        return real(*a, **k)

    # /lenses and /patterns share the market-data cache with /research.
    client.get("/research/NVDA")
    first = client.get("/cache").json()["entries"]
    client.get("/research/NVDA")
    assert client.get("/cache").json()["entries"] == first, "no new cache entry on a repeat"
