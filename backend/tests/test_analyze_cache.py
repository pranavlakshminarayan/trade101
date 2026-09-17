"""orchestrator.analyze() result caching (docs/AUDIT.md finding M2) — every
page reload, new tab, or friend opening the shared link used to spend a
fresh Claude call for the same ticker, even though gather() being cached
already kept the underlying numbers stable across those calls. This is the
other half: cache the LLM-produced result itself, but never a failure."""
import numpy as np
import pandas as pd

from agents import llm, orchestrator


def _fake_hist(n=60):
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    close = pd.Series(100 + np.cumsum(np.random.default_rng(7).normal(0, 1, n)), index=idx)
    return pd.DataFrame({
        "Open": close, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": pd.Series([1_000_000] * n, index=idx),
    })


def _patch_gather(monkeypatch, ticker="CACHETEST"):
    orchestrator.cache.clear()
    quote = {"symbol": ticker, "name": "Cache Test Co", "currency": "USD"}
    monkeypatch.setattr(orchestrator.marketdata, "get", lambda *a, **k: (_fake_hist(), quote))
    monkeypatch.setattr(orchestrator.news, "get_news", lambda *a, **k: ([], None))
    monkeypatch.setattr(orchestrator.news, "get_recent_filings", lambda *a, **k: ([], None))
    monkeypatch.setattr(orchestrator.company, "get_profile", lambda *a, **k: {"peers": []})


def test_repeated_analyze_calls_hit_the_llm_only_once(monkeypatch):
    _patch_gather(monkeypatch)
    calls = {"n": 0}

    def fake_run(*a, **k):
        calls["n"] += 1
        return {"momentum": {"lean": "neutral", "confidence": "low", "summary": "s", "evidence": []},
                "news_inference": {"summary": "", "sources": []}, "learning_note": ""}

    monkeypatch.setattr(orchestrator.analysis, "run", fake_run)

    r1 = orchestrator.analyze("CACHETEST")
    r2 = orchestrator.analyze("CACHETEST")
    assert calls["n"] == 1          # the LLM was only actually called once
    assert r1 == r2                 # same cached result returned both times


def test_a_failed_analyze_is_never_cached_and_is_retried(monkeypatch):
    _patch_gather(monkeypatch)
    calls = {"n": 0}

    def flaky_run(*a, **k):
        calls["n"] += 1
        raise llm.MissingKeyError("no key configured")

    monkeypatch.setattr(orchestrator.analysis, "run", flaky_run)

    for _ in range(3):
        try:
            orchestrator.analyze("CACHETEST")
            assert False, "expected MissingKeyError to propagate"
        except llm.MissingKeyError:
            pass
    # every call actually retried the LLM — a failure must never be cached,
    # or a transient error (or a temporarily-missing key) would stick around
    # for the full cache TTL instead of recovering on the next request.
    assert calls["n"] == 3


def test_different_tickers_are_cached_independently(monkeypatch):
    orchestrator.cache.clear()
    calls = {"n": 0}

    def counting_get(ticker, *a, **k):
        calls["n"] += 1
        return (_fake_hist(), {"symbol": ticker, "name": ticker, "currency": "USD"})

    monkeypatch.setattr(orchestrator.marketdata, "get", counting_get)
    monkeypatch.setattr(orchestrator.news, "get_news", lambda *a, **k: ([], None))
    monkeypatch.setattr(orchestrator.news, "get_recent_filings", lambda *a, **k: ([], None))
    monkeypatch.setattr(orchestrator.company, "get_profile", lambda *a, **k: {"peers": []})
    monkeypatch.setattr(orchestrator.analysis, "run", lambda *a, **k: {
        "momentum": {"lean": "neutral", "confidence": "low", "summary": "s", "evidence": []},
        "news_inference": {"summary": "", "sources": []}, "learning_note": "",
    })

    orchestrator.analyze("AAA")
    orchestrator.analyze("BBB")
    assert calls["n"] == 2  # two distinct tickers, each fetched/analyzed once
