"""
Phase 2.5 tests — style lenses.

The contract every lens must keep: it declares what it ignores, it surfaces
evidence against its own reading, and it names how it fails. A lens that only
argues its own case would be the exact thing this feature exists to inoculate
against.
"""
import pandas as pd
import pytest

from services import indicators, lenses

LENS_IDS = {"trend", "swing", "mean-reversion", "long-term", "event-driven"}


def _series(closes, volumes=None):
    idx = pd.date_range(end="2026-09-01", periods=len(closes), freq="D")
    return pd.DataFrame(
        {"Open": closes, "High": [c + 1 for c in closes], "Low": [c - 1 for c in closes],
         "Close": closes, "Volume": volumes or [1000] * len(closes)},
        index=idx,
    )


def _ind(closes, volumes=None):
    return indicators.compute_indicators(_series(closes, volumes))


UPTREND = [50 + i * 0.25 for i in range(300)]
DOWNTREND = [125 - i * 0.25 for i in range(300)]
RANGE = [100 + (i % 20) * 0.5 for i in range(300)]


# ---- the contract every lens keeps -----------------------------------------

def test_all_five_lenses_present_and_no_day_trading_lens():
    out = lenses.build(_ind(UPTREND))
    assert {l["id"] for l in out["lenses"]} == LENS_IDS
    assert "day-trading" in out["excluded"]
    assert "delayed" in out["excluded"]["day-trading"]


@pytest.mark.parametrize("closes", [UPTREND, DOWNTREND, RANGE])
def test_every_lens_declares_what_it_ignores_and_how_it_fails(closes):
    for l in lenses.build(_ind(closes))["lenses"]:
        assert l["ignores"], f"{l['id']} must say what it does not look at"
        assert l["failureModes"], f"{l['id']} must say how it goes wrong"
        assert l["question"] and l["reading"]
        assert l["lean"] in {"bullish", "bearish", "neutral", "mixed", "unknown"}


def test_lenses_are_deterministic_and_carry_no_model_output():
    a = lenses.build(_ind(UPTREND))
    b = lenses.build(_ind(UPTREND))
    assert a == b
    assert a["meta"]["deterministic"] is True


# ---- the lenses genuinely disagree -----------------------------------------

def test_a_strong_uptrend_splits_trend_against_mean_reversion():
    """The teaching moment: same data, opposite readings, both defensible."""
    out = lenses.build(_ind(UPTREND))
    by_id = {l["id"]: l for l in out["lenses"]}
    assert by_id["trend"]["lean"] == "bullish"
    assert by_id["mean-reversion"]["lean"] == "bearish"
    assert out["disagreement"]["level"] == "high"
    assert "different question" in out["disagreement"]["note"]


def test_agreement_is_explicitly_called_weak_evidence():
    """Agreement between lenses over one dataset must not read as confirmation."""
    out = lenses.build(_ind(RANGE))
    if out["disagreement"]["level"] in ("low", "none"):
        assert "weaker evidence than it feels like" in out["disagreement"]["note"]


def test_downtrend_is_read_as_a_downtrend_by_the_trend_lens():
    by_id = {l["id"]: l for l in lenses.build(_ind(DOWNTREND))["lenses"]}
    assert by_id["trend"]["lean"] == "bearish"


# ---- each lens surfaces evidence against itself ----------------------------

def test_mean_reversion_warns_hardest_in_a_trending_market():
    """Its own worst failure mode, raised on the data where it applies."""
    by_id = {l["id"]: l for l in lenses.build(_ind(UPTREND))["lenses"]}
    mr = by_id["mean-reversion"]
    assert any("trending market" in c for c in mr["conflicts"])
    assert "no rule that says a stretched price returns" in " ".join(mr["conflicts"])
    assert mr["caveat"]


def test_trend_lens_flags_a_stretched_price_against_itself():
    # A steeper climb, so price sits well beyond 25% above its 200-day average.
    steep = [50 + i * 0.5 for i in range(300)]
    by_id = {l["id"]: l for l in lenses.build(_ind(steep))["lenses"]}
    assert any("long way" in c or "extended" in c for c in by_id["trend"]["conflicts"])


def test_trend_lens_flags_thinning_volume_under_a_rising_price():
    # The drop must be recent enough that the 20-day average has not fallen with
    # it — otherwise latest-vs-average is 0% and there is nothing to detect.
    rising_thin = _ind(UPTREND, volumes=[5000] * 295 + [500] * 5)
    trend = {l["id"]: l for l in lenses.build(rising_thin)["lenses"]}["trend"]
    assert any("thinning participation" in c for c in trend["conflicts"])


def test_event_lens_says_nothing_rather_than_inventing_a_catalyst():
    ev = {l["id"]: l for l in lenses.build(_ind(UPTREND), None, [], [])["lenses"]}["event-driven"]
    assert any("nothing to say" in c for c in ev["conflicts"])
    assert "absent catalyst is not the same as no catalyst" in " ".join(ev["conflicts"])


# ---- the long-term lens depends on fundamentals ----------------------------

def test_long_term_lens_is_unknown_without_statements():
    lt = {l["id"]: l for l in lenses.build(_ind(UPTREND), {"coverage": {"level": "none"}})["lenses"]}["long-term"]
    assert lt["lean"] == "unknown"
    assert "cannot be applied" in lt["reading"]


def test_long_term_lens_flags_growth_that_costs_more_than_it_earns():
    fund = {
        "coverage": {"level": "ok"},
        "revenue": {"changePercent": 30.0},
        "netIncome": {"changePercent": -12.0},
        "cashFlow": {"changePercent": 5.0},
        "valuation": {"trailingPE": 44.0},
        "earnings": {},
    }
    lt = {l["id"]: l for l in lenses.build(_ind(UPTREND), fund)["lenses"]}["long-term"]
    assert any("costing more than it brings in" in c for c in lt["conflicts"])
    assert any("chart-based lens cannot see this" in c for c in lt["conflicts"])


def test_long_term_lens_flags_profit_without_cash():
    fund = {
        "coverage": {"level": "ok"},
        "revenue": {"changePercent": 5.0},
        "netIncome": {"changePercent": 8.0},
        "cashFlow": {"changePercent": -20.0},
        "valuation": {}, "earnings": {},
    }
    lt = {l["id"]: l for l in lenses.build(_ind(UPTREND), fund)["lenses"]}["long-term"]
    assert any("cash flow is negative" in c for c in lt["conflicts"])


def test_lenses_survive_an_empty_indicator_snapshot():
    """A symbol with almost no history must not crash the panel."""
    out = lenses.build({}, None, None, None)
    assert len(out["lenses"]) == 5
    assert all(l["reading"] for l in out["lenses"])
