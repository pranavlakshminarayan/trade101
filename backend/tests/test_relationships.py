"""
Phase 4 tests — the ecosystem graph.

The guarantee under test: an edge we cannot source is never drawn, and an empty
relationship list is reported as "no source" rather than "none exist". Those two
read identically in a UI and mean opposite things, which is exactly why the
distinction has to be enforced in the payload.
"""
import pandas as pd
import pytest

from services import cache, relationships


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    cache.clear()
    monkeypatch.delenv("TRADE101_RELATIONSHIP_PROVIDER", raising=False)
    yield
    cache.clear()


@pytest.fixture
def peers(monkeypatch):
    monkeypatch.setattr(relationships.company, "get_profile",
                        lambda t: {"peers": ["AMD", "INTC"], "sector": "Technology"})


@pytest.fixture
def no_fund(monkeypatch):
    class T:
        @property
        def funds_data(self): raise Exception("not a fund")
    monkeypatch.setattr(relationships.yf, "Ticker", lambda *a, **k: T())


# ---- unsourced relationship types ------------------------------------------

def test_supplier_and_customer_edges_are_never_invented(peers, no_fund):
    """We have no licensed relationship dataset, so these must stay empty."""
    g = relationships.graph("NVDA")
    for t in ("supplier", "customer", "partner", "investor"):
        assert g["byType"][t] == []


def test_an_empty_list_is_reported_as_no_source_not_as_none_exist(peers, no_fund):
    """The distinction the whole module exists to preserve."""
    g = relationships.graph("NVDA")
    assert set(g["unsourced"]["types"]) == {"supplier", "customer", "partner", "investor"}
    reason = g["unsourced"]["reason"]
    assert "no source for them" in reason
    assert "NOT that this company has none" in reason


def test_configuring_an_unknown_provider_is_reported(monkeypatch, peers, no_fund):
    monkeypatch.setenv("TRADE101_RELATIONSHIP_PROVIDER", "acme")
    g = relationships.graph("NVDA")
    assert "Unknown relationship provider" in g["unsourced"]["reason"]


# ---- peer edges carry their provenance and their weakness ------------------

def test_peers_become_competitor_edges_with_low_confidence(peers, no_fund):
    g = relationships.graph("NVDA")
    comp = g["byType"]["competitor"]
    assert {e["to"] for e in comp} == {"AMD", "INTC"}
    for e in comp:
        assert e["type"] == "competitor"
        assert e["source"] == "Finnhub peer grouping"
        assert e["confidence"] == "low"
        assert "not a verified business relationship" in e["note"]
        assert e["targetIsPublic"] is True


def test_every_edge_declares_type_source_confidence_and_materiality(peers, no_fund):
    for e in relationships.graph("NVDA")["edges"]:
        for field in ("type", "source", "confidence", "materiality", "targetIsPublic"):
            assert field in e, f"edge missing {field}"
        assert e["type"] in relationships.EDGE_TYPES
        assert e["confidenceMeaning"]


def test_the_graph_states_a_relationship_is_a_hypothesis_not_a_mechanism(peers, no_fund):
    caveat = relationships.graph("NVDA")["caveat"]
    assert "HYPOTHESIS" in caveat
    assert "not proof of a price effect" in caveat


# ---- ETF holdings ----------------------------------------------------------

@pytest.fixture
def etf(monkeypatch):
    holdings = pd.DataFrame(
        {"Name": ["Apple Inc", "Nvidia Corp"], "Holding Percent": [0.071, 0.064]},
        index=["AAPL", "NVDA"])

    class FD:
        top_holdings = holdings

    class T:
        funds_data = FD()

    monkeypatch.setattr(relationships.yf, "Ticker", lambda *a, **k: T())


def test_fund_holdings_become_verified_constituent_edges_with_weights(etf):
    g = relationships.graph("SPY")
    assert g["isFund"] is True
    edges = g["byType"]["index_constituent"]
    assert {e["to"] for e in edges} == {"AAPL", "NVDA"}

    apple = next(e for e in edges if e["to"] == "AAPL")
    assert apple["confidence"] == "high"
    assert apple["materiality"] == "7.1% of the fund"
    assert apple["toName"] == "Apple Inc"
    assert apple["source"] == "Fund's published holdings"


def test_a_fund_carries_the_weighted_sum_caveat(etf):
    g = relationships.graph("SPY")
    assert g["fundCaveat"]
    assert "does not rise because one company" in g["fundCaveat"]
    assert "weighted sum" in g["fundCaveat"]


def test_a_fund_shows_holdings_rather_than_peer_guesses(etf, monkeypatch):
    """For a fund, the verified holdings replace the peer grouping entirely."""
    called = []
    monkeypatch.setattr(relationships.company, "get_profile",
                        lambda t: called.append(t) or {"peers": ["XLK"]})
    g = relationships.graph("SPY")
    assert called == [], "a fund must not fall back to a peer grouping"
    assert g["byType"]["competitor"] == []


def test_a_non_fund_reports_no_fund_caveat(peers, no_fund):
    g = relationships.graph("NVDA")
    assert g["isFund"] is False and g["fundCaveat"] is None


def test_malformed_holding_weights_do_not_break_the_graph(monkeypatch):
    holdings = pd.DataFrame({"Name": ["Odd"], "Holding Percent": ["n/a"]}, index=["ODD"])

    class FD:
        top_holdings = holdings

    class T:
        funds_data = FD()

    monkeypatch.setattr(relationships.yf, "Ticker", lambda *a, **k: T())
    edges = relationships.graph("WEIRD")["byType"]["index_constituent"]
    assert len(edges) == 1 and edges[0]["materiality"] is None


def test_legend_documents_every_edge_type(peers, no_fund):
    legend = relationships.graph("NVDA")["legend"]["types"]
    assert set(legend) == set(relationships.EDGE_TYPES)
    assert all(v for v in legend.values())
