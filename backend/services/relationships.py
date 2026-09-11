"""
Ecosystem graph — typed, sourced relationships between companies.

This module replaces the flat peer list, and the reason is a guardrail rather
than a feature: a bare list of tickers under the heading "ecosystem" invites the
reader to infer a supply chain that was never claimed. Every edge here therefore
carries its relationship TYPE, its SOURCE, a DATE where one exists, a CONFIDENCE,
and a MATERIALITY — and an edge we cannot source is not drawn.

What is genuinely sourceable today:
  competitor / peer   — Finnhub's peer grouping. This is a SECTOR grouping, not
                        a verified business relationship, and is labelled as such
                        with low confidence.
  index_constituent   — ETF holdings and weights, verified from the fund's own
                        published holdings.

What is NOT sourceable today, and is therefore returned EMPTY rather than
guessed: supplier, customer, partner, investor. Those need a licensed
relationship dataset. TRADE101_RELATIONSHIP_PROVIDER is the adapter slot, the
same pattern the news provider uses; until one is configured, the graph says so
out loud. An empty supplier list means "we have no source", never "this company
has no suppliers", and the UI must carry that distinction.

The framing every consumer must repeat: a business relationship is a research
HYPOTHESIS about why two companies might move together. It is not proof of a
price effect, and plenty of tightly-linked companies trade in opposite directions
for years.
"""
from __future__ import annotations

import os

import yfinance as yf

from services import cache, company

EDGE_TYPES = ("supplier", "customer", "partner", "competitor", "investor", "index_constituent")

# Types that need a licensed relationship dataset we do not yet have.
UNSOURCED_TYPES = ("supplier", "customer", "partner", "investor")

CONFIDENCE_MEANING = {
    "high": "Stated in a primary source (a filing, or the fund's own holdings).",
    "moderate": "From a data provider that names the relationship explicitly.",
    "low": "Inferred from a grouping — the provider places these companies together, "
           "which is not the same as a verified business relationship.",
}


def _edge(source_ticker: str, target: str, kind: str, *, source: str,
          confidence: str, materiality=None, date=None, url=None,
          target_name=None, target_is_public=True, note=None) -> dict:
    return {
        "from": source_ticker.upper(),
        "to": (target or "").upper() if target_is_public else target,
        "toName": target_name,
        "type": kind,
        "source": source,
        "sourceUrl": url,
        "date": date,
        "confidence": confidence,
        "confidenceMeaning": CONFIDENCE_MEANING.get(confidence, ""),
        "materiality": materiality,
        "targetIsPublic": target_is_public,
        "note": note,
    }


def _peer_edges(ticker: str) -> list[dict]:
    """Finnhub peers → competitor edges, honestly labelled as a grouping."""
    profile = company.get_profile(ticker)
    return [
        _edge(ticker, p, "competitor",
              source="Finnhub peer grouping",
              confidence="low",
              materiality="unknown",
              note="A provider grouping of similar companies — usually same sector or "
                   "industry. It is not a verified business relationship, and says nothing "
                   "about whether these two prices move together.")
        for p in (profile.get("peers") or [])
    ]


def _etf_edges(ticker: str) -> tuple[list[dict], dict]:
    """If this symbol is a fund, its verified holdings and weights."""
    def fetch():
        t = yf.Ticker(ticker)
        try:
            fd = t.funds_data
            holdings = fd.top_holdings
        except Exception:
            return None
        if holdings is None or getattr(holdings, "empty", True):
            return None
        rows = []
        for sym, row in holdings.iterrows():
            weight = row.get("Holding Percent")
            try:
                weight = round(float(weight) * 100, 2) if weight is not None else None
            except (TypeError, ValueError):
                weight = None
            rows.append({"symbol": str(sym), "name": row.get("Name"), "weightPercent": weight})
        return rows

    try:
        rows, _ = cache.get_or_fetch("etf_holdings", ticker.upper(), fetch)
    except Exception:
        rows = None

    if not rows:
        return [], {"isFund": False}

    edges = [
        _edge(ticker, r["symbol"], "index_constituent",
              source="Fund's published holdings",
              confidence="high",
              materiality=f"{r['weightPercent']}% of the fund" if r["weightPercent"] is not None else None,
              target_name=r.get("name"),
              note="A verified holding with its published weight.")
        for r in rows
    ]
    return edges, {"isFund": True, "holdings": rows}


def _provider_edges(ticker: str) -> tuple[list[dict], str]:
    """Supplier/customer/partner/investor edges from a licensed provider.

    Returns ([], reason) unless one is configured. This function exists to make
    the absence explicit and the addition trivial — not to be filled in with
    guesses.
    """
    provider = os.environ.get("TRADE101_RELATIONSHIP_PROVIDER", "none").lower()
    if provider in ("", "none"):
        return [], ("No relationship data source is configured "
                    "(TRADE101_RELATIONSHIP_PROVIDER). Supplier, customer, partner and "
                    "investor links need a licensed dataset — so none are shown. That "
                    "means we have no source for them, NOT that this company has none.")
    return [], f"Unknown relationship provider '{provider}'."


def graph(ticker: str) -> dict:
    """The full ecosystem graph for `ticker`, with every absence accounted for."""
    ticker = ticker.upper()
    edges = []

    etf_edges, fund_info = _etf_edges(ticker)
    edges.extend(etf_edges)
    if not etf_edges:
        edges.extend(_peer_edges(ticker))

    provider_edges, provider_note = _provider_edges(ticker)
    edges.extend(provider_edges)

    by_type = {t: [e for e in edges if e["type"] == t] for t in EDGE_TYPES}
    missing = [t for t in UNSOURCED_TYPES if not by_type[t]]

    return {
        "ticker": ticker,
        "isFund": fund_info.get("isFund", False),
        "holdings": fund_info.get("holdings"),
        "edges": edges,
        "byType": by_type,
        "unsourced": {
            "types": missing,
            "reason": provider_note,
        },
        "legend": {
            "types": {
                "supplier": "Sells inputs to this company.",
                "customer": "Buys from this company.",
                "partner": "A named commercial or technical partnership.",
                "competitor": "Competes for the same customers.",
                "investor": "Holds a disclosed stake in this company.",
                "index_constituent": "Held by this fund, with a published weight.",
            },
            "confidence": CONFIDENCE_MEANING,
        },
        "caveat": (
            "A business relationship is a research HYPOTHESIS about why two companies might "
            "move together — it is not proof of a price effect. Suppliers routinely fall "
            "while their customer rises, and a supplier's exposure is usually a small "
            "fraction of its own revenue. Treat an edge here as a question worth "
            "investigating, never as a mechanism you can rely on."
        ),
        "fundCaveat": (
            "A fund does not rise because one company somewhere in a possible supply chain "
            "grew. It moves with the weighted sum of everything it holds — so a holding at "
            "0.4% of the fund contributes almost nothing, however dramatic its own move."
        ) if fund_info.get("isFund") else None,
        "meta": {
            "note": "Every edge carries its type, source, confidence and materiality. Edges "
                    "we cannot source are not drawn, and the types we have no source for "
                    "are listed explicitly rather than left blank.",
        },
    }
