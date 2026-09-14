"""Evidence relevance filter — the Phase-1.5 guardrail that keeps unrelated news
out of the AI payload. These are the 'feed irrelevant content, assert it's
rejected' tests the recommendations review asked for."""
from services import company, evidence


def test_regional_index_mapping():
    assert company._index_for("7974.T")[1] == "Nikkei 225"
    assert company._index_for("005930.KS")[1] == "KOSPI"
    assert company._index_for("AAPL")[1] == "S&P 500"       # US default
    assert company._index_for("RELIANCE.NS")[1] == "Nifty 50"
    assert company._index_for("SOMETHING.XYZ")[1] == "S&P 500"  # unknown suffix → default

NVDA_NEWS = [
    {"headline": "Nvidia unveils new Blackwell GPU", "summary": "The chipmaker announced..."},
    {"headline": "Fed holds rates steady", "summary": "The central bank left policy unchanged."},
    {"headline": "AMD reports strong data-center sales", "summary": "Rival AMD posted results."},
    {"headline": "Best pancake recipes for autumn", "summary": "A cozy breakfast guide."},
]


def test_company_article_classified_company():
    cat = evidence.classify(NVDA_NEWS[0], name="NVIDIA Corporation", ticker="NVDA")
    assert cat == "company"


def test_unrelated_article_classified_irrelevant():
    cat = evidence.classify(NVDA_NEWS[3], name="NVIDIA Corporation", ticker="NVDA",
                            sector="Technology", industry="Semiconductors", peers=["AMD"])
    assert cat == "irrelevant"


def test_peer_article_classified_related():
    cat = evidence.classify(NVDA_NEWS[2], name="NVIDIA Corporation", ticker="NVDA",
                            peers=["AMD", "INTC"])
    assert cat == "related"


def test_filter_drops_irrelevant_and_reports():
    kept, report = evidence.filter_news(
        NVDA_NEWS, name="NVIDIA Corporation", ticker="NVDA",
        sector="Technology", industry="Semiconductors", peers=["AMD"],
    )
    headlines = [a["headline"] for a in kept]
    assert "Best pancake recipes for autumn" not in headlines  # irrelevant dropped
    assert "Nvidia unveils new Blackwell GPU" in headlines
    assert report["has_company_news"] is True
    assert report["dropped"] >= 1
    # company-specific sorts ahead of peer news
    assert kept[0]["category"] == "company"


def test_no_company_news_flag_when_only_noise():
    only_noise = [NVDA_NEWS[3]]
    kept, report = evidence.filter_news(only_noise, name="NVIDIA Corporation", ticker="NVDA")
    assert kept == []
    assert report["has_company_news"] is False


def test_ticker_suffix_stripped_for_matching():
    # A non-US ticker like 7974.T should still match on its base number/name.
    art = [{"headline": "Nintendo posts record Switch sales", "summary": ""}]
    kept, report = evidence.filter_news(art, name="Nintendo Co Ltd", ticker="7974.T")
    assert report["has_company_news"] is True
