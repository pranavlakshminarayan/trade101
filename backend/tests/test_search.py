"""Symbol search ranking (services.search) — regression coverage for
docs/AUDIT.md findings H1/H2: a real company's OTC pink-sheet ADR, Canadian
CDR, or a preferred-share line must never outrank its primary/major listing.
Mocks Yahoo's search response so these run offline and deterministically."""
import json

from services import search


class Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _quotes(*rows):
    """Build a fake Yahoo search response from (symbol, name, exchange_code,
    exch_disp) tuples, all typed as ordinary equities."""
    return {"quotes": [
        {"symbol": sym, "shortname": name, "exchange": exch, "exchDisp": disp, "quoteType": "EQUITY"}
        for sym, name, exch, disp in rows
    ]}


def test_otc_line_ranks_below_the_primary_listing(monkeypatch):
    # Regression for the exact case in docs/AUDIT.md: Yahoo itself returns the
    # OTC ADR (NTDOY) ahead of the real Tokyo listing (7974.T).
    payload = _quotes(
        ("NTDOY", "Nintendo Co., Ltd.", "PNK", "OTC Markets"),
        ("7974.T", "NINTENDO CO LTD", "JPX", "Tokyo Stock Exchange"),
    )
    monkeypatch.setattr(search.httpx, "get", lambda *a, **k: Resp(payload))

    out = search.resolve("nintendo")
    assert [c["symbol"] for c in out] == ["7974.T", "NTDOY"]
    assert out[0]["listingBadge"] is None
    assert out[1]["listingBadge"] == "OTC"


def test_cdr_and_preferred_lines_are_labeled_and_demoted(monkeypatch):
    payload = _quotes(
        ("005935.KS", "SamsungElec(1P)", "KSC", "Korea"),
        ("SONY.NE", "SONY CDR (CAD HEDGED)", "NEO", "NEO"),
        ("005930.KS", "SamsungElec", "KSC", "Korea"),
    )
    monkeypatch.setattr(search.httpx, "get", lambda *a, **k: Resp(payload))

    out = search.resolve("samsung")
    assert out[0]["symbol"] == "005930.KS"       # common shares first
    assert out[0]["listingBadge"] is None
    badges = {c["symbol"]: c["listingBadge"] for c in out}
    assert badges["005935.KS"] == "Pref"
    assert badges["SONY.NE"] == "CDR"


def test_no_junk_sort_keys_leak_into_the_response(monkeypatch):
    payload = _quotes(("AAPL", "Apple Inc.", "NMS", "NASDAQ"))
    monkeypatch.setattr(search.httpx, "get", lambda *a, **k: Resp(payload))
    out = search.resolve("apple")
    assert set(out[0].keys()) == {"symbol", "name", "exchange", "type", "listingBadge"}
    # every candidate must be JSON-serializable as returned (what /search sends)
    json.dumps(out)


def test_empty_result_on_repeated_failure(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("network down")
    monkeypatch.setattr(search.httpx, "get", boom)
    monkeypatch.setattr(search.time, "sleep", lambda *_: None)
    assert search.resolve("anything") == []
