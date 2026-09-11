"""Spend-ledger + storage tests — no network, no API keys, no real Claude calls."""
import importlib

import pytest

from agents import llm
from services import storage, usage


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point the ledger at a throwaway database for every test."""
    monkeypatch.setenv("TRADE101_DB", str(tmp_path / "t.db"))
    storage.reset_for_tests()
    yield
    storage.reset_for_tests()


class FakeUsage:
    def __init__(self, i=1000, o=500, cw=0, cr=0):
        self.input_tokens, self.output_tokens = i, o
        self.cache_creation_input_tokens, self.cache_read_input_tokens = cw, cr


# ---- pricing ---------------------------------------------------------------

def test_cost_matches_published_rates():
    # Sonnet 5: $2/1M in, $10/1M out → 1M in + 1M out = $12.00 exactly.
    cost, priced = usage.estimate_cost("claude-sonnet-5", 1_000_000, 1_000_000)
    assert priced is True
    assert cost == pytest.approx(12.00)


def test_cache_tokens_priced_off_the_input_rate():
    # Opus 5 input $5/1M → 1M cache writes = 1.25x, 1M cache reads = 0.10x.
    cost, _ = usage.estimate_cost("claude-opus-5", 0, 0, 1_000_000, 1_000_000)
    assert cost == pytest.approx(5 * 1.25 + 5 * 0.10)


def test_unknown_model_is_counted_but_never_priced():
    """The 'never fabricate a number' rule applies to cost too."""
    cost, priced = usage.estimate_cost("some-future-model", 10_000, 10_000)
    assert (cost, priced) == (0.0, False)
    row = usage.record("analysis", "TRADE101_ANALYSIS_KEY", "some-future-model", FakeUsage())
    assert row["priced"] == 0 and row["cost_usd"] == 0.0
    assert usage.summary()["total"]["unpriced_calls"] == 1


# ---- attribution -----------------------------------------------------------

def test_spend_splits_by_purpose_even_on_one_shared_key():
    """The whole point: one key, still a per-feature breakdown."""
    usage.record("analysis", "TRADE101_ANALYSIS_KEY", "claude-sonnet-5", FakeUsage(1_000_000, 0))
    usage.record("research", "TRADE101_ANALYSIS_KEY", "claude-sonnet-5", FakeUsage(2_000_000, 0))

    s = usage.summary()
    assert s["available"] is True
    by_purpose = {r["name"]: r for r in s["byPurpose"]}
    assert by_purpose["analysis"]["cost_usd"] == pytest.approx(2.00)
    assert by_purpose["research"]["cost_usd"] == pytest.approx(4.00)
    # ...while the key-level view (what the Console shows) sees one bill.
    assert len(s["byKey"]) == 1
    assert s["byKey"][0]["cost_usd"] == pytest.approx(6.00)
    assert s["total"]["calls"] == 2


def test_record_survives_a_missing_usage_object():
    row = usage.record("analysis", "TRADE101_ANALYSIS_KEY", "claude-sonnet-5", None)
    assert row["input_tokens"] == 0 and row["cost_usd"] == 0.0


# ---- key resolution --------------------------------------------------------

def test_purpose_key_used_when_set(monkeypatch):
    monkeypatch.setenv("TRADE101_RESEARCH_KEY", "sk-research")
    monkeypatch.setenv("TRADE101_ANALYSIS_KEY", "sk-analysis")
    assert llm.resolve_key("research") == ("sk-research", "TRADE101_RESEARCH_KEY")


def test_purpose_falls_back_to_the_shared_key(monkeypatch):
    monkeypatch.delenv("TRADE101_RESEARCH_KEY", raising=False)
    monkeypatch.setenv("TRADE101_ANALYSIS_KEY", "sk-analysis")
    assert llm.resolve_key("research") == ("sk-analysis", "TRADE101_ANALYSIS_KEY")


def test_no_key_at_all_raises_missing_key(monkeypatch):
    for env in ("TRADE101_RESEARCH_KEY", "TRADE101_ANALYSIS_KEY"):
        monkeypatch.delenv(env, raising=False)
    with pytest.raises(llm.MissingKeyError):
        llm.resolve_key("research")


# ---- history persistence ---------------------------------------------------

def test_history_upserts_and_orders_by_recency():
    storage.save_history("NVDA", "NVIDIA", "bullish", "first read", "2026-09-10")
    storage.save_history("MSFT", "Microsoft", "neutral", "another", "2026-09-10")
    storage.save_history("NVDA", "NVIDIA", "mixed", "revised read", "2026-09-11")

    rows = storage.get_history()
    assert len(rows) == 2, "same ticker must update, not duplicate"
    assert rows[0]["ticker"] == "NVDA" and rows[0]["summary"] == "revised read"
    assert rows[0]["as_of"] == "2026-09-11"
    assert storage.clear_history() == 2 and storage.get_history() == []


def test_broken_database_degrades_silently(tmp_path, monkeypatch):
    """A dead database must never break research — it just stops recording."""
    # A regular file where a parent directory should be: unopenable for any user.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory")
    monkeypatch.setenv("TRADE101_DB", str(blocker / "t.db"))
    storage.reset_for_tests()
    storage.save_history("NVDA", "NVIDIA", "bullish", "x")  # must not raise
    assert storage.get_history() == []
    assert usage.summary()["available"] is False
