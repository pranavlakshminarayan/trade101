"""
Phase 2 tests — the learning engine.

The load-bearing test here is test_setup_never_leaks_a_single_future_bar: if the
replay setup exposes anything after the cut, the exercise is worthless, and the
leak would be invisible in the UI.
"""
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app
from services import cache, fundamentals, replay, storage

client = TestClient(app.app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("TRADE101_DB", str(tmp_path / "t.db"))
    storage.reset_for_tests()
    cache.clear()
    yield
    storage.reset_for_tests()
    cache.clear()


def _hist(n=400):
    """A deterministic series with an obvious run-up then a fall."""
    idx = pd.date_range(end=pd.Timestamp("2026-09-01"), periods=n, freq="D")
    close = [50 + i * 0.2 + (i % 11) * 0.5 for i in range(n)]
    return pd.DataFrame(
        {"Open": [c - 0.3 for c in close], "High": [c + 0.5 for c in close],
         "Low": [c - 0.5 for c in close], "Close": close,
         "Volume": [10_000 + i for i in range(n)]},
        index=idx,
    )


@pytest.fixture
def stub_market(monkeypatch):
    hist = _hist()
    monkeypatch.setattr(replay.marketdata, "get",
                        lambda *a, **k: (hist, {"symbol": "NVDA", "name": "NVIDIA"}))
    return hist


# ---- retrospective replay --------------------------------------------------

def test_setup_never_leaks_a_single_future_bar(stub_market):
    """The whole exercise rests on this."""
    s = replay.setup("NVDA", horizon=30, variant=0)
    assert s["available"] is True

    cut_ts = pd.Timestamp(s["asOf"])
    latest_shown = max(b["time"] for b in s["ohlcv"])
    assert latest_shown == int(cut_ts.timestamp())

    # Nothing in the payload may describe anything after the cut.
    hidden = stub_market[stub_market.index > cut_ts]
    assert not hidden.empty, "fixture must actually have a future to hide"
    assert all(b["time"] <= int(cut_ts.timestamp()) for b in s["ohlcv"])
    assert s["bars"] == len(stub_market[stub_market.index <= cut_ts])
    assert "outcome" not in s and "reveal" not in s

    # The invariant is temporal, not numeric: a price series revisits the same
    # levels constantly, so a visible bar's low legitimately equals some later
    # close. What must never appear is a TIMESTAMP from after the cut.
    import json
    cut_epoch = int(cut_ts.timestamp())
    hidden_epochs = {int(ts.timestamp()) for ts in hidden.index}
    blob = json.dumps(s)
    assert not any(str(e) in blob for e in hidden_epochs), "a post-cut timestamp leaked"
    assert max(b["time"] for b in s["ohlcv"]) == cut_epoch


def test_setup_indicators_are_computed_only_from_visible_bars(stub_market):
    s = replay.setup("NVDA", horizon=30, variant=0)
    cut = pd.Timestamp(s["asOf"])
    visible = stub_market[stub_market.index <= cut]

    from services import indicators
    expected = indicators.compute_indicators(visible)
    assert s["indicators"]["rsi14"] == expected["rsi14"]
    # ...and demonstrably NOT the full-history value.
    assert s["indicators"]["sma50"] != indicators.compute_indicators(stub_market)["sma50"]


def test_reveal_returns_the_outcome_and_the_one_sample_caveat(stub_market):
    r = replay.reveal("NVDA", horizon=30, variant=0)
    assert r["available"] is True
    assert r["outcome"]["barsRevealed"] == 30
    assert isinstance(r["outcome"]["changePercent"], float)
    assert "one sample" in r["caveat"].lower()
    assert "cannot confirm or refute" in r["caveat"]


def test_setup_and_reveal_agree_on_the_same_cut(stub_market):
    s = replay.setup("NVDA", horizon=30, variant=0)
    r = replay.reveal("NVDA", horizon=30, variant=0)
    assert r["cutClose"] == s["ohlcv"][-1]["close"]
    assert min(b["time"] for b in r["ohlcv"]) > max(b["time"] for b in s["ohlcv"])


def test_same_variant_is_reproducible_and_a_new_variant_differs(stub_market):
    a1 = replay.setup("NVDA", variant=0)["asOf"]
    a2 = replay.setup("NVDA", variant=0)["asOf"]
    b = replay.setup("NVDA", variant=1)["asOf"]
    assert a1 == a2, "the same exercise must be stable across renders"
    assert b != a1, "asking for another should move the cut"


def test_short_history_refuses_rather_than_giving_an_unfair_exercise(monkeypatch):
    monkeypatch.setattr(replay.marketdata, "get",
                        lambda *a, **k: (_hist(40), {"symbol": "TINY"}))
    s = replay.setup("TINY", horizon=30)
    assert s["available"] is False and "at least" in s["reason"]


def test_replay_endpoints_are_separate_so_the_outcome_is_a_deliberate_request(stub_market):
    setup_body = client.get("/replay/NVDA").json()
    assert "outcome" not in setup_body
    reveal_body = client.get("/replay/NVDA/reveal").json()
    assert "outcome" in reveal_body


# ---- learning journal ------------------------------------------------------

def test_journal_requires_reasoning_not_just_a_lean():
    r = client.post("/journal", json={"ticker": "NVDA", "lean": "bullish", "hypothesis": "  "})
    assert r.status_code == 400
    assert "why" in r.json()["detail"]


def test_journal_requires_a_ticker():
    assert client.post("/journal", json={"hypothesis": "looks strong"}).status_code == 400


def test_journal_round_trip_keeps_evidence_and_the_learners_own_lean():
    r = client.post("/journal", json={
        "ticker": "nvda", "kind": "study", "lean": "bullish", "confidence": "moderate",
        "hypothesis": "Price is above both moving averages and volume is rising.",
        "evidence": ["ind:sma50", "ind:sma200"], "asOf": "2026-09-11T00:00:00",
    })
    assert r.status_code == 200
    entry_id = r.json()["id"]

    entries = client.get("/journal?ticker=NVDA").json()["entries"]
    assert len(entries) == 1
    e = entries[0]
    assert e["ticker"] == "NVDA" and e["lean"] == "bullish"
    assert e["evidence"] == ["ind:sma50", "ind:sma200"]
    assert e["reflection"] is None

    assert client.patch(f"/journal/{entry_id}", json={"reflection": "The volume read was weak."}).status_code == 200
    assert client.get("/journal").json()["entries"][0]["reflection"] == "The volume read was weak."
    assert client.delete(f"/journal/{entry_id}").status_code == 200
    assert client.get("/journal").json()["entries"] == []


def test_reflecting_on_a_missing_entry_is_a_404():
    assert client.patch("/journal/999", json={"reflection": "x"}).status_code == 404


def test_ai_lean_is_stored_separately_from_the_learners_lean():
    """Guided Study records the AI's view only AFTER the learner commits, so the
    two must never be conflated in storage."""
    client.post("/journal", json={"ticker": "NVDA", "hypothesis": "Topping out.",
                                  "lean": "bearish", "aiLean": "bullish"})
    e = client.get("/journal").json()["entries"][0]
    assert e["lean"] == "bearish" and e["ai_lean"] == "bullish"


# ---- fundamentals ----------------------------------------------------------

def test_fundamentals_computes_margins_and_growth_from_statements(monkeypatch):
    periods = ["2024-12-31", "2025-12-31"]
    income = pd.DataFrame(
        [[1000.0, 1500.0], [400.0, 690.0], [200.0, 300.0]],
        index=["Total Revenue", "Gross Profit", "Net Income"],
        columns=pd.to_datetime(periods))
    cash = pd.DataFrame([[150.0, 240.0]], index=["Free Cash Flow"],
                        columns=pd.to_datetime(periods))

    class T:
        info = {"trailingPE": 30.0, "currency": "USD", "financialCurrency": "USD"}
        income_stmt = income
        cashflow = cash
        earnings_dates = None

    monkeypatch.setattr(fundamentals.yf, "Ticker", lambda *a, **k: T())
    f = fundamentals.get_fundamentals("NVDA")

    assert f["revenue"]["changePercent"] == 50.0
    assert f["netIncome"]["changePercent"] == 50.0
    assert f["cashFlow"]["changePercent"] == 60.0
    assert f["margins"]["gross"][-1]["value"] == 46.0   # 690/1500
    assert f["margins"]["net"][-1]["value"] == 20.0     # 300/1500
    assert f["valuation"]["trailingPE"] == 30.0
    assert f["coverage"]["level"] == "ok"


def test_fundamentals_reports_missing_coverage_instead_of_inventing_it(monkeypatch):
    class T:
        info = {}
        income_stmt = pd.DataFrame()
        cashflow = pd.DataFrame()
        earnings_dates = None

    monkeypatch.setattr(fundamentals.yf, "Ticker", lambda *a, **k: T())
    f = fundamentals.get_fundamentals("OBSCURE.XX")

    assert f["coverage"]["level"] == "none"
    assert f["revenue"]["series"] is None and f["revenue"]["changePercent"] is None
    assert f["valuation"]["trailingPE"] is None
    assert any("No financial statements" in n for n in f["meta"]["notes"])


def test_fundamentals_survives_a_provider_that_raises(monkeypatch):
    class T:
        @property
        def info(self): raise ConnectionError("down")
        @property
        def income_stmt(self): raise ConnectionError("down")
        @property
        def cashflow(self): raise ConnectionError("down")
        @property
        def earnings_dates(self): raise ConnectionError("down")

    monkeypatch.setattr(fundamentals.yf, "Ticker", lambda *a, **k: T())
    f = fundamentals.get_fundamentals("NVDA")
    assert f["coverage"]["level"] == "none"
    assert len(f["meta"]["notes"]) >= 3


def test_nan_values_are_dropped_not_rendered_as_numbers(monkeypatch):
    income = pd.DataFrame([[float("nan"), 1500.0]], index=["Total Revenue"],
                          columns=pd.to_datetime(["2024-12-31", "2025-12-31"]))

    class T:
        info = {}
        income_stmt = income
        cashflow = pd.DataFrame()
        earnings_dates = None

    monkeypatch.setattr(fundamentals.yf, "Ticker", lambda *a, **k: T())
    f = fundamentals.get_fundamentals("NVDA")
    assert f["revenue"]["series"] == [{"period": "2025-12-31", "value": 1500.0}]
    assert f["revenue"]["changePercent"] is None, "one period cannot yield a growth rate"
