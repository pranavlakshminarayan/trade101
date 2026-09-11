"""
Evidence pipeline tests — the sourcing contract, made checkable.

These are the tests the review asked for: they prove that irrelevant evidence
never reaches the model, and that a claim citing something we never supplied
cannot reach the user.
"""
from datetime import date

import pytest

from services import cache, evidence

TODAY = date(2026, 9, 11)


def item(headline, days_ago=1, url="https://example.com/a", summary="", source="Reuters"):
    from datetime import timedelta
    return {"headline": headline, "summary": summary, "source": source, "url": url,
            "datetime": (TODAY - timedelta(days=days_ago)).isoformat()}


# ---- relevance filtering ---------------------------------------------------

def test_article_naming_the_company_is_kept():
    s, why = evidence.score_item(item("NVIDIA beats on data-centre revenue"),
                                 "NVDA", "NVIDIA Corporation", TODAY)
    assert s >= 0.5 and "names the company" in why


def test_article_about_another_company_is_dropped():
    s, why = evidence.score_item(item("Ford recalls 200,000 trucks"),
                                 "NVDA", "NVIDIA Corporation", TODAY)
    assert s == 0.0 and why == "does not mention this company"


def test_multi_stock_roundup_is_penalised():
    """A round-up mentioning the ticker is not evidence ABOUT the company."""
    round_up = evidence.score_item(item("Stocks to watch: NVDA, AAPL, TSLA and more movers"),
                                   "NVDA", "NVIDIA Corporation", TODAY)[0]
    specific = evidence.score_item(item("NVIDIA lifts guidance"),
                                   "NVDA", "NVIDIA Corporation", TODAY)[0]
    assert round_up < specific


def test_stale_article_scores_below_a_fresh_one():
    fresh = evidence.score_item(item("NVIDIA lifts guidance", 1), "NVDA", "NVIDIA", TODAY)[0]
    old = evidence.score_item(item("NVIDIA lifts guidance", 90), "NVDA", "NVIDIA", TODAY)[0]
    assert old < fresh


def test_unlinkable_article_is_penalised():
    """If the learner cannot open it, it cannot be checked."""
    linked = evidence.score_item(item("NVIDIA lifts guidance"), "NVDA", "NVIDIA", TODAY)[0]
    bare = evidence.score_item(item("NVIDIA lifts guidance", url=None), "NVDA", "NVIDIA", TODAY)[0]
    assert bare < linked


def test_select_reports_what_it_dropped_and_why():
    items = [item("NVIDIA beats on data-centre revenue"),
             item("Ford recalls 200,000 trucks"),
             item("Stocks to watch: NVDA, AAPL, TSLA and more movers")]
    kept, report = evidence.select(items, "NVDA", "NVIDIA Corporation")

    assert [k["headline"] for k in kept] == ["NVIDIA beats on data-centre revenue"]
    assert report["considered"] == 3 and report["kept"] == 1 and report["dropped"] == 2
    assert all("why" in d and d["why"] for d in report["droppedExamples"])
    assert all("relevance" in k and "relevanceWhy" in k for k in kept)


# ---- citation verification -------------------------------------------------

@pytest.fixture
def catalog():
    return evidence.build_catalog(
        {"rsi14": 56.2, "sma50": 120.0},
        [item("NVIDIA beats on data-centre revenue")],
        [{"form": "8-K", "date": "2026-09-02", "url": "https://sec.gov/x"}],
    )


def test_catalog_ids_cover_indicators_news_and_filings(catalog):
    assert {e["id"] for e in catalog} == {"ind:rsi14", "ind:sma50", "news:0", "filing:0"}


def test_claim_citing_real_evidence_is_kept_with_its_source(catalog):
    ok, bad = evidence.verify([{"point": "RSI is mid-range", "source": "ind:rsi14"}], catalog)
    assert not bad and len(ok) == 1
    assert ok[0]["citations"][0]["id"] == "ind:rsi14"
    assert ok[0]["citations"][0]["detail"] == "rsi14 = 56.2"


def test_claim_citing_nothing_we_supplied_is_dropped(catalog):
    """The anti-hallucination guarantee: an unsupplied source cannot reach the UI."""
    ok, bad = evidence.verify(
        [{"point": "Analysts at a major bank raised targets", "source": "Bloomberg terminal"}],
        catalog)
    assert ok == [] and len(bad) == 1
    assert "not in the evidence supplied" in bad[0]["reason"]


def test_claim_may_cite_by_headline_not_only_by_id(catalog):
    ok, _ = evidence.verify(
        [{"point": "Revenue beat", "source": "NVIDIA beats on data-centre revenue"}], catalog)
    assert len(ok) == 1 and ok[0]["citations"][0]["id"] == "news:0"


def test_verify_tolerates_missing_and_malformed_claims(catalog):
    ok, bad = evidence.verify([None, "a string", {"point": "no source field"}], catalog)
    assert ok == [] and len(bad) == 1


# ---- coverage honesty ------------------------------------------------------

def test_no_sources_reports_none_and_says_so():
    cov = evidence.coverage([], [], {"considered": 0, "kept": 0})
    assert cov["level"] == "none" and "partial picture" in cov["note"]


def test_thin_coverage_tells_the_learner_to_lower_confidence():
    cov = evidence.coverage([item("NVIDIA beats")], [], {"considered": 5, "kept": 1})
    assert cov["level"] == "thin" and "Lower your confidence" in cov["note"]


def test_good_coverage_counts_what_informed_the_read():
    cov = evidence.coverage([item("a"), item("b"), item("c")],
                            [{"form": "8-K"}], {"considered": 6, "kept": 3})
    assert cov["level"] == "ok" and "3 relevant article(s)" in cov["note"]


# ---- cache -----------------------------------------------------------------

def test_cache_serves_the_second_call_without_refetching():
    cache.clear()
    calls = []

    def fetch():
        calls.append(1)
        return {"v": 1}

    first, m1 = cache.get_or_fetch("profile", "NVDA", fetch)
    second, m2 = cache.get_or_fetch("profile", "NVDA", fetch)

    assert first == second == {"v": 1}
    assert len(calls) == 1, "second call must come from cache"
    assert m1["cached"] is False and m2["cached"] is True
    assert m2["fetchedAt"] == m1["fetchedAt"], "a cached value keeps its original fetch time"


def test_failed_fetch_is_not_cached():
    cache.clear()

    def boom():
        raise RuntimeError("provider down")

    with pytest.raises(RuntimeError):
        cache.get_or_fetch("news", "NVDA", boom)
    assert cache.stats()["entries"] == 0
