"""
Phase 3 tests — comparison, watchlist, practice lab.

Three promises get tested here, because all three are easy to break by accident:
comparison never ranks, watchlist alerts never prompt, and practice-lab figures
are never presented as real.
"""
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app
from services import cache, compare as compare_svc, storage, watchlist

client = TestClient(app.app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("TRADE101_DB", str(tmp_path / "t.db"))
    storage.reset_for_tests()
    cache.clear()
    yield
    storage.reset_for_tests()
    cache.clear()


def _hist(start, step, n=260):
    idx = pd.date_range(end="2026-09-01", periods=n, freq="D")
    close = [start + i * step for i in range(n)]
    return pd.DataFrame(
        {"Open": close, "High": [c + 1 for c in close], "Low": [c - 1 for c in close],
         "Close": close, "Volume": [1000] * n}, index=idx)


@pytest.fixture
def two_stocks(monkeypatch):
    """One cheap slow riser, one expensive fast riser — different in price, same
    in shape, which is exactly what rebasing must reveal."""
    book = {
        "AAA": (_hist(10, 0.02), {"symbol": "AAA", "name": "Alpha", "price": 15.18, "currency": "USD"}),
        "BBB": (_hist(1000, 4.0), {"symbol": "BBB", "name": "Beta", "price": 2036.0, "currency": "USD"}),
    }
    monkeypatch.setattr(compare_svc.marketdata, "get",
                        lambda t, **k: book.get(t.upper()))
    monkeypatch.setattr(compare_svc.fund_svc, "get_fundamentals",
                        lambda t: {"revenue": {"changePercent": 10.0}, "netIncome": {},
                                   "cashFlow": {}, "valuation": {"trailingPE": 20.0},
                                   "earnings": {}, "coverage": {"level": "ok"}})
    monkeypatch.setattr(compare_svc.company_svc, "get_profile",
                        lambda t: {"sector": "Technology", "industry": "Software",
                                   "beta": 1.1, "marketCap": 1e11})
    return book


# ---- comparison ------------------------------------------------------------

def test_comparison_rebases_so_different_price_levels_are_comparable(two_stocks):
    r = compare_svc.compare(["AAA", "BBB"])
    assert r["tickers"] == ["AAA", "BBB"]
    for e in r["entries"]:
        assert e["series"][0]["value"] == 100.0, "every line must start at 100"
    assert "rebased to 100" in r["basis"]


def test_comparison_produces_no_ranking_score_or_winner(two_stocks):
    """The promise: it shows difference, it does not decide."""
    import json
    r = compare_svc.compare(["AAA", "BBB"])

    # Scan the DATA, not the prose that promises no ranking — that sentence
    # legitimately contains the words "ranking" and "score".
    data = {k: v for k, v in r.items() if k not in ("note", "basis")}
    blob = json.dumps(data).lower()
    for word in ("winner", "better", "best", "outperform", "rank", "score", "recommend"):
        assert word not in blob, f"comparison leaked a ranking word: {word}"

    # No entry may carry a position, grade or ordering key.
    for e in r["entries"]:
        assert not ({"rank", "position", "grade", "verdict"} & set(e))

    assert "no ranking and no score" in r["note"]


def test_comparison_reports_an_unreachable_symbol_instead_of_dropping_it(monkeypatch, two_stocks):
    from services import marketdata
    real = compare_svc.marketdata.get

    def selective(t, **k):
        if t.upper() == "CCC":
            raise marketdata.ProviderError("CCC", ConnectionError("down"))
        return real(t, **k)

    monkeypatch.setattr(compare_svc.marketdata, "get", selective)
    r = compare_svc.compare(["AAA", "CCC"])
    assert [f["ticker"] for f in r["failed"]] == ["CCC"]
    assert r["failed"][0]["retryable"] is True
    assert r["tickers"] == ["AAA"], "the reachable company still renders"


def test_comparison_warns_when_sectors_or_currencies_differ(two_stocks, monkeypatch):
    profiles = {"AAA": {"sector": "Technology", "marketCap": 1e11},
                "BBB": {"sector": "Utilities", "marketCap": 1e11}}
    monkeypatch.setattr(compare_svc.company_svc, "get_profile", lambda t: profiles[t.upper()])
    r = compare_svc.compare(["AAA", "BBB"])
    assert r["comparability"]["level"] in ("partial", "weak")
    assert any("Different sectors" in w for w in r["comparability"]["warnings"])


def test_comparison_warns_on_a_large_size_mismatch(two_stocks, monkeypatch):
    caps = {"AAA": 1e8, "BBB": 5e12}
    monkeypatch.setattr(compare_svc.company_svc, "get_profile",
                        lambda t: {"sector": "Technology", "marketCap": caps[t.upper()]})
    r = compare_svc.compare(["AAA", "BBB"])
    assert any("20x" in w for w in r["comparability"]["warnings"])


def test_comparison_deduplicates_and_caps_the_ticker_list(two_stocks):
    r = compare_svc.compare(["AAA", "aaa", "BBB", "AAA"])
    assert r["tickers"] == ["AAA", "BBB"]


def test_compare_endpoint_needs_at_least_two(two_stocks):
    assert client.get("/compare?tickers=AAA").status_code == 400
    assert client.get("/compare?tickers=AAA,BBB").status_code == 200


def test_performance_stats_are_computed_not_guessed(two_stocks):
    r = compare_svc.compare(["AAA", "BBB"])
    e = r["entries"][0]["performance"]
    # AAA: 10.00 → 10 + 259*0.02 = 15.18, i.e. +51.8%
    assert e["changePercent"] == pytest.approx(51.8, abs=0.1)
    assert e["maxDrawdownPercent"] == 0.0, "a monotonic riser has no drawdown"


# ---- watchlist -------------------------------------------------------------

def test_watchlist_add_list_remove_round_trip():
    r = client.post("/watchlist", json={"ticker": "nvda", "name": "NVIDIA",
                                        "note": "AI capex cycle", "level": 150})
    assert r.status_code == 200 and r.json()["ticker"] == "NVDA"

    items = client.get("/watchlist?refresh=false").json()["items"]
    assert len(items) == 1 and items[0]["level"] == 150.0
    assert items[0]["note"] == "AI capex cycle"

    assert client.delete("/watchlist/NVDA").status_code == 200
    assert client.get("/watchlist?refresh=false").json()["items"] == []


def test_removing_an_unwatched_ticker_is_a_404():
    assert client.delete("/watchlist/NOPE").status_code == 404


def test_level_crossing_is_phrased_as_information_never_as_a_prompt():
    """The load-bearing promise of the whole watchlist."""
    storage.watch_add("NVDA", "NVIDIA", None, 150.0)
    storage.watch_record_price("NVDA", 140.0)
    w = dict(storage.watch_list()[0])

    ev = watchlist._crossing_event(w, 155.0)
    assert ev is not None
    text = (ev["text"] + " " + ev["context"]).lower()
    for word in ("buy", "sell", "should", "opportunity", "act now", "target", "signal to"):
        assert word not in text, f"watchlist alert used a prompting word: {word}"
    assert "information" in text and "not a signal" in text


def test_a_level_that_was_not_crossed_produces_no_event():
    storage.watch_add("NVDA", None, None, 150.0)
    storage.watch_record_price("NVDA", 140.0)
    w = dict(storage.watch_list()[0])
    assert watchlist._crossing_event(w, 145.0) is None


def test_crossing_works_in_both_directions():
    w = {"level": 100.0, "last_seen": 90.0}
    assert "up through" in watchlist._crossing_event(w, 110.0)["text"]
    assert "down through" in watchlist._crossing_event({"level": 100.0, "last_seen": 110.0}, 90.0)["text"]


def test_watchlist_survives_a_dead_provider(monkeypatch):
    from services import marketdata
    storage.watch_add("NVDA", None, None, None)
    monkeypatch.setattr(watchlist.marketdata, "get",
                        lambda *a, **k: (_ for _ in ()).throw(
                            marketdata.ProviderError("NVDA", ConnectionError("down"))))
    s = watchlist.status()
    assert s["errors"] == ["NVDA"]
    assert s["items"][0]["error"] and s["items"][0]["price"] is None


# ---- practice lab ----------------------------------------------------------

def test_practice_entry_requires_a_reason():
    r = client.post("/practice", json={"ticker": "NVDA", "price": 100, "reason": "  "})
    assert r.status_code == 400
    assert "teaches nothing" in r.json()["detail"]


def test_practice_rejects_a_nonsense_direction():
    r = client.post("/practice", json={"ticker": "NVDA", "price": 100, "reason": "testing",
                                       "direction": "sideways"})
    assert r.status_code == 400


def test_practice_results_are_labelled_hypothetical_everywhere(monkeypatch):
    monkeypatch.setattr(app.marketdata, "get",
                        lambda *a, **k: (_hist(100, 0), {"symbol": "NVDA", "price": 120.0}))
    client.post("/practice", json={"ticker": "NVDA", "price": 100, "quantity": 10,
                                   "reason": "Testing whether the trend read holds."})
    body = client.get("/practice").json()

    assert "HYPOTHETICAL" in body["disclaimer"]
    assert "no costs, spread, slippage" in body["disclaimer"] or "slippage" in body["disclaimer"]
    assert "not to keep score" in body["purpose"]

    e = body["entries"][0]
    assert set(e["hypothetical"]) == {"hypotheticalChangePercent", "hypotheticalAmount"}
    assert e["hypothetical"]["hypotheticalChangePercent"] == 20.0
    assert e["hypothetical"]["hypotheticalAmount"] == 200.0
    assert "pnl" not in e and "profit" not in e


def test_short_direction_inverts_the_hypothetical_result(monkeypatch):
    monkeypatch.setattr(app.marketdata, "get",
                        lambda *a, **k: (_hist(100, 0), {"symbol": "NVDA", "price": 120.0}))
    client.post("/practice", json={"ticker": "NVDA", "price": 100, "quantity": 1,
                                   "direction": "short", "reason": "Testing the inverse."})
    e = client.get("/practice").json()["entries"][0]
    assert e["hypothetical"]["hypotheticalChangePercent"] == -20.0


def test_closing_a_practice_entry_records_the_reflection(monkeypatch):
    monkeypatch.setattr(app.marketdata, "get",
                        lambda *a, **k: (_hist(100, 0), {"symbol": "NVDA", "price": 120.0}))
    opened = client.post("/practice", json={"ticker": "NVDA", "price": 100,
                                            "reason": "Trend read."}).json()
    r = client.patch(f"/practice/{opened['id']}",
                     json={"price": 130, "reflection": "The volume read was the weak part."})
    assert r.status_code == 200

    e = client.get("/practice").json()["entries"][0]
    assert e["closed_at"] and e["close_price"] == 130.0
    assert e["reflection"] == "The volume read was the weak part."
    # A closed entry marks to its close price, not to the live one.
    assert e["hypothetical"]["hypotheticalChangePercent"] == 30.0


def test_closing_an_already_closed_entry_is_a_404(monkeypatch):
    monkeypatch.setattr(app.marketdata, "get",
                        lambda *a, **k: (_hist(100, 0), {"symbol": "NVDA", "price": 120.0}))
    opened = client.post("/practice", json={"ticker": "NVDA", "price": 100,
                                            "reason": "Trend read."}).json()
    client.patch(f"/practice/{opened['id']}", json={"price": 130})
    assert client.patch(f"/practice/{opened['id']}", json={"price": 140}).status_code == 404
