"""services/company.py — summary truncation and beta-index naming.

Two user-reported bugs, both regressions to guard against:
  1. The company summary was hard-truncated at a fixed character count with
     no regard for word boundaries, then the frontend unconditionally
     appended another "…" — cutting text off mid-word ("...solutions an…").
  2. A PROVIDER-sourced beta (the common case — most US tickers have one)
     carried no benchmark name at all, so the UI could only say the vague
     "the overall market" instead of naming the actual index (e.g. the
     S&P 500) the way a COMPUTED beta already did.
"""
from services import company


def test_truncate_summary_cuts_at_a_word_boundary_not_mid_word():
    text = "Alpha beta gamma delta epsilon zeta eta theta iota kappa"
    out = company._truncate_summary(text, limit=20)
    assert out is not None
    # never cuts mid-word: strip the added ellipsis and confirm it's a prefix
    # of a real word boundary in the original text
    body = out.rstrip("…")
    assert text.startswith(body)
    assert not text[len(body):len(body) + 1].isalpha() or body == ""
    assert out.endswith("…")


def test_truncate_summary_leaves_a_short_text_untouched():
    text = "A short summary that fits easily."
    assert company._truncate_summary(text, limit=360) == text  # no "…" added


def test_truncate_summary_handles_empty_and_none():
    assert company._truncate_summary(None) is None
    assert company._truncate_summary("") is None
    assert company._truncate_summary("   ") is None


def test_truncate_summary_never_leaves_dangling_punctuation_before_ellipsis():
    text = "One two three, four five six, seven eight nine, ten eleven twelve."
    out = company._truncate_summary(text, limit=30)
    assert not out.rstrip("…").endswith((",", ".", ";", ":"))


class _FakeTicker:
    """Minimal yf.Ticker stand-in exposing only `.info`."""
    def __init__(self, info):
        self._info = info

    @property
    def info(self):
        return self._info


def test_provider_beta_gets_a_named_benchmark_index(monkeypatch):
    # Regression: a provider beta (the common case) used to carry no index
    # name at all — only a computed (no-provider-data) beta named its
    # benchmark. Both must name one now, so the UI can say "vs the S&P 500"
    # instead of vaguely "the market".
    monkeypatch.setattr(company.yf, "Ticker",
                         lambda *_a, **_k: _FakeTicker({"beta": 1.4, "sector": "Tech"}))
    monkeypatch.setattr(company, "_peers", lambda *_a, **_k: ([], None))
    profile = company.get_profile("AAPL")
    assert profile["betaSource"] == "provider"
    assert profile["betaIndex"] == "S&P 500"


def test_provider_beta_names_the_regional_index_for_a_non_us_listing(monkeypatch):
    monkeypatch.setattr(company.yf, "Ticker",
                         lambda *_a, **_k: _FakeTicker({"beta": 0.9, "sector": "Tech"}))
    monkeypatch.setattr(company, "_peers", lambda *_a, **_k: ([], None))
    profile = company.get_profile("7974.T")
    assert profile["betaSource"] == "provider"
    assert profile["betaIndex"] == "Nikkei 225"


def test_peer_names_resolves_each_symbol_and_skips_failures(monkeypatch):
    # User-reported: the ecosystem graph showed only bare tickers with no way
    # to see the company name without already knowing it. peerNames is looked
    # up per symbol (in parallel — no keyless batch-quote endpoint survives on
    # Yahoo's side any more) and must degrade per-symbol, not fail the whole
    # profile if one peer's lookup errors.
    fakes = {
        "AVGO": _FakeTicker({"shortName": "Broadcom Inc."}),
        "MU": _FakeTicker({"longName": "Micron Technology, Inc."}),  # no shortName
    }

    def fake_ticker(sym):
        if sym == "BROKEN":
            raise RuntimeError("network down")
        return fakes[sym]

    monkeypatch.setattr(company.yf, "Ticker", fake_ticker)
    out = company._peer_names(["AVGO", "MU", "BROKEN"])
    assert out == {"AVGO": "Broadcom Inc.", "MU": "Micron Technology, Inc."}


def test_peer_names_empty_input_returns_empty_dict():
    assert company._peer_names([]) == {}


# --- fundamentals (docs/AUDIT.md M5 — the biggest content gap: zero
# fundamentals anywhere in the app) ---

def test_fundamentals_pulled_straight_from_info_no_computation(monkeypatch):
    info = {
        "trailingPE": 38.03, "forwardPE": 34.67, "trailingEps": 8.74,
        "revenueGrowth": 0.164, "profitMargins": 0.276, "dividendYield": 0.33,
        "debtToEquity": 78.4,
    }
    out = company._fundamentals("AAPL", info)
    assert out["pe"] == 38.03
    assert out["forwardPe"] == 34.67
    assert out["eps"] == 8.74
    assert out["revenueGrowth"] == 0.164
    assert out["profitMargin"] == 0.276
    assert out["dividendYield"] == 0.33
    assert out["debtToEquity"] == 78.4
    assert out["coverage"] is None  # real values present, no gap to explain


def test_fundamentals_missing_everything_sets_a_coverage_note():
    out = company._fundamentals("THINCO", {})
    assert all(out[k] is None for k in
               ("pe", "forwardPe", "eps", "revenueGrowth", "profitMargin",
                "dividendYield", "debtToEquity", "nextEarningsDate"))
    assert out["coverage"]


def test_fundamentals_degrades_when_calendar_lookup_fails(monkeypatch):
    # yf.Ticker(ticker).calendar is a SEPARATE lookup from the `info` dict
    # already fetched by get_profile — its own failure must not raise or
    # block the rest of the fundamentals from coming through.
    class _Boom:
        @property
        def calendar(self):
            raise RuntimeError("network down")

    monkeypatch.setattr(company.yf, "Ticker", lambda *_a, **_k: _Boom())
    out = company._fundamentals("AAPL", {"trailingPE": 20.0})
    assert out["pe"] == 20.0
    assert out["nextEarningsDate"] is None


def test_get_profile_surfaces_fundamentals_and_their_coverage_gap(monkeypatch):
    monkeypatch.setattr(company.yf, "Ticker",
                         lambda *_a, **_k: _FakeTicker({"beta": 1.1, "sector": "Tech"}))
    monkeypatch.setattr(company, "_peers", lambda *_a, **_k: ([], None))
    profile = company.get_profile("AAPL")
    assert profile["fundamentals"]["pe"] is None  # _FakeTicker.info has no PE fields
    assert "fundamentals" in profile["coverage"]


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_peers_deduplicates_case_insensitively(monkeypatch):
    # Regression: Finnhub's own peers list can (and does, confirmed live on
    # QCOM) contain the same symbol twice — the ecosystem graph rendered the
    # same company as two separate nodes as a result.
    monkeypatch.setenv("TRADE101_NEWS_KEY", "fake")
    monkeypatch.setattr(company.httpx, "get",
                         lambda *a, **k: _Resp(["MU", "AMD", "mu", "QCOM", "AMD"]))
    out = company._finnhub_peers("QCOM")
    assert out == ["MU", "AMD"]  # QCOM excluded (it's the ticker itself), no repeats


# --- non-US peers fallback (user-reported: Reliance/RELIANCE.NS showed no
# ecosystem graph at all — Finnhub's free peers endpoint is US-listed-only) ---

def test_peers_falls_back_to_yahoo_when_finnhub_has_nothing(monkeypatch):
    monkeypatch.delenv("TRADE101_NEWS_KEY", raising=False)  # _finnhub_peers returns []
    monkeypatch.setattr(company, "_yahoo_related", lambda *_a, **_k: ["TCS.NS", "HDFCBANK.NS"])
    peers, source = company._peers("RELIANCE.NS")
    assert peers == ["TCS.NS", "HDFCBANK.NS"]
    assert source == "yahoo"


def test_peers_prefers_finnhub_over_yahoo_when_both_available(monkeypatch):
    monkeypatch.setattr(company, "_finnhub_peers", lambda *_a, **_k: ["MU", "AMD"])
    monkeypatch.setattr(company, "_yahoo_related", lambda *_a, **_k: ["SHOULD", "NOT", "APPEAR"])
    peers, source = company._peers("QCOM")
    assert peers == ["MU", "AMD"]
    assert source == "finnhub"


def test_peers_none_when_both_sources_empty(monkeypatch):
    monkeypatch.setattr(company, "_finnhub_peers", lambda *_a, **_k: [])
    monkeypatch.setattr(company, "_yahoo_related", lambda *_a, **_k: [])
    assert company._peers("OBSCURE.XX") == ([], None)


def test_yahoo_related_degrades_on_provider_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(company.httpx, "get", boom)
    assert company._yahoo_related("RELIANCE.NS") == []
