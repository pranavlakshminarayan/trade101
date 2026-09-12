"""
Run the REAL Trade101 backend with only its outbound providers stubbed.

Yahoo/Finnhub/SEC are blocked by this container's egress proxy, so the app
cannot fetch live data here. Everything else — the endpoints, the evidence
gates, the lenses, the freshness logic — is the real code path. This exists
purely so the frontend can be driven and screenshotted.
"""
import pathlib
import sys
from datetime import date, timedelta

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app as trade_app  # noqa: E402
from services import company, fundamentals, marketdata, news, relationships, replay  # noqa: E402
from services import compare as compare_svc  # noqa: E402

N = 400
IDX = pd.date_range(end=pd.Timestamp.now().normalize(), periods=N, freq="D")
CLOSE = [92 + i * 0.14 + (i % 17) * 0.9 for i in range(N)]
HIST = pd.DataFrame(
    {"Open": [c - 0.4 for c in CLOSE], "High": [c + 0.9 for c in CLOSE],
     "Low": [c - 0.9 for c in CLOSE], "Close": CLOSE,
     "Volume": [48_000_000 + (i % 11) * 3_000_000 for i in range(N)]},
    index=IDX,
)
QUOTE = {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": round(CLOSE[-1], 2),
         "previousClose": round(CLOSE[-2], 2),
         "change": round(CLOSE[-1] - CLOSE[-2], 2),
         "changePercent": round((CLOSE[-1] - CLOSE[-2]) / CLOSE[-2] * 100, 2),
         "currency": "USD", "marketCap": 3_420_000_000_000, "exchange": "NasdaqGS"}


def _get(ticker="NVDA", period="1y", interval="1d"):
    bars = {"1d": 78, "5d": 130, "1mo": 22}.get(period, N)
    h = HIST.iloc[-bars:] if period != "1y" else HIST
    q = dict(QUOTE, symbol=(ticker or "NVDA").upper())
    return h, q


for mod in (marketdata, replay.marketdata, compare_svc.marketdata,
            trade_app.marketdata, trade_app.orchestrator.marketdata,
            trade_app.watchlist.marketdata):
    mod.get = _get

marketdata.get_with_meta = lambda t="NVDA", period="1y", interval="1d": (
    _get(t, period, interval),
    {"cached": False, "fetchedAt": pd.Timestamp.now("UTC").isoformat(timespec="seconds"),
     "ageSeconds": 0, "backend": "in-process"})
trade_app.marketdata.get_with_meta = marketdata.get_with_meta

# --- news + filings -------------------------------------------------------
TODAY = date.today()
NEWS = [
    {"headline": "NVIDIA beats on data-centre revenue as Blackwell shipments accelerate",
     "summary": "NVIDIA reported data-centre revenue above consensus, citing faster "
                "Blackwell ramp and continued hyperscaler demand.",
     "source": "Reuters", "url": "https://example.com/nvda-datacentre",
     "datetime": (TODAY - timedelta(days=1)).isoformat()},
    {"headline": "NVIDIA lifts full-year guidance on sustained AI infrastructure demand",
     "summary": "Management raised guidance, pointing to supply improvements.",
     "source": "Bloomberg", "url": "https://example.com/nvda-guidance",
     "datetime": (TODAY - timedelta(days=3)).isoformat()},
    {"headline": "Stocks to watch: NVDA, AAPL, TSLA and other premarket movers",
     "summary": "A round-up of the session's biggest movers.",
     "source": "CNBC", "url": "https://example.com/roundup",
     "datetime": (TODAY - timedelta(days=2)).isoformat()},
    {"headline": "Ford recalls 200,000 trucks over brake software",
     "summary": "Unrelated automotive recall.",
     "source": "AP", "url": "https://example.com/ford",
     "datetime": (TODAY - timedelta(days=1)).isoformat()},
]
FILINGS = [
    {"form": "10-Q", "date": (TODAY - timedelta(days=22)).isoformat(),
     "url": "https://www.sec.gov/Archives/edgar/data/1045810/example-10q.htm"},
    {"form": "8-K", "date": (TODAY - timedelta(days=9)).isoformat(),
     "url": "https://www.sec.gov/Archives/edgar/data/1045810/example-8k.htm"},
]
news.get_news = lambda t, days=30: (NEWS, None)
news.get_recent_filings = lambda t, limit=5: (FILINGS, None)
trade_app.news_svc.get_news = news.get_news
trade_app.news_svc.get_recent_filings = news.get_recent_filings

company.get_profile = lambda t: {
    "sector": "Technology", "industry": "Semiconductors", "beta": 1.62,
    "marketCap": 3_420_000_000_000, "exchange": "NasdaqGS", "country": "United States",
    "peers": ["AMD", "INTC", "AVGO", "QCOM", "TSM"],
    "summary": "NVIDIA Corporation provides graphics and compute platforms, with data-centre "
               "accelerators used for AI training and inference workloads worldwide.",
}
trade_app.company.get_profile = company.get_profile
relationships.company.get_profile = company.get_profile

_periods = pd.to_datetime(["2023-12-31", "2024-12-31", "2025-12-31"])
fundamentals.get_fundamentals = lambda t: {
    "ticker": (t or "NVDA").upper(), "currency": "USD",
    "earnings": {"nextDate": (TODAY + timedelta(days=34)).isoformat() + "T00:00:00",
                 "lastDate": (TODAY - timedelta(days=56)).isoformat() + "T00:00:00",
                 "epsActual": 0.81, "epsEstimate": 0.75, "surprisePercent": 8.0, "note": None},
    "revenue": {"series": [{"period": "2023-12-31", "value": 26_974_000_000},
                           {"period": "2024-12-31", "value": 60_922_000_000},
                           {"period": "2025-12-31", "value": 130_497_000_000}],
                "changePercent": 114.2},
    "netIncome": {"series": [{"period": "2023-12-31", "value": 4_368_000_000},
                             {"period": "2024-12-31", "value": 29_760_000_000},
                             {"period": "2025-12-31", "value": 72_880_000_000}],
                  "changePercent": 144.9},
    "margins": {"gross": [{"period": "2025-12-31", "value": 75.0}],
                "operating": [{"period": "2025-12-31", "value": 62.4}],
                "net": [{"period": "2023-12-31", "value": 16.2},
                        {"period": "2024-12-31", "value": 48.8},
                        {"period": "2025-12-31", "value": 55.8}],
                "note": "Margin is what the company keeps from each unit of revenue. Rising "
                        "revenue with falling margin means growth is costing more to buy."},
    "cashFlow": {"series": [{"period": "2024-12-31", "value": 27_021_000_000},
                            {"period": "2025-12-31", "value": 60_853_000_000}],
                 "changePercent": 125.2,
                 "note": "Cash flow is harder to flatter than reported profit, which is why it "
                         "is worth reading alongside net income rather than instead."},
    "valuation": {"trailingPE": 46.2, "forwardPE": 29.8, "priceToBook": 38.1,
                  "priceToSales": 24.9, "enterpriseToEbitda": 40.3,
                  "marketCap": 3_420_000_000_000,
                  "note": "A multiple is a comparison, not a judgement: it only means something "
                          "against this company's own history and its sector. A low P/E can mean "
                          "cheap or it can mean the market expects earnings to fall."},
    "coverage": {"statements": 3, "level": "ok"},
    "meta": {"provider": "Yahoo Finance (stubbed locally)",
             "note": "Fundamentals are cached for up to 6h and are reported as filed.",
             "notes": []},
}
trade_app.fundamentals.get_fundamentals = fundamentals.get_fundamentals
compare_svc.fund_svc.get_fundamentals = fundamentals.get_fundamentals
compare_svc.company_svc.get_profile = company.get_profile


# --- the AI read ----------------------------------------------------------
# Stubbed so the curtain has something real to reveal without spending a key.
# Shaped exactly like the orchestrator's output, INCLUDING one deliberately
# untraceable claim so the "withheld" path is visible.
def _analyze(ticker, period="1y"):
    hist, quote = _get(ticker)
    from services import evidence, indicators
    ind = indicators.compute_indicators(hist)
    kept, report = evidence.select(NEWS, quote["symbol"], quote["name"])
    coverage = evidence.coverage(kept, FILINGS, report)
    catalog = evidence.build_catalog(ind, kept, FILINGS)

    raw_evidence = [
        {"point": f"Price {quote['price']} is above both the 50-day ({ind['sma50']}) and "
                  f"200-day ({ind['sma200']}) averages", "source": "ind:sma200"},
        {"point": f"RSI(14) at {ind['rsi14']} sits mid-range rather than stretched",
         "source": "ind:rsi14"},
        {"point": "MACD remains above its signal line, so short-term momentum is still building",
         "source": "ind:macd.signal"},
        {"point": "Data-centre revenue came in above consensus on a faster Blackwell ramp",
         "source": "news:0"},
        {"point": "A major bank raised its target to $250", "source": "Bloomberg terminal"},
    ]
    raw_claims = [
        {"point": "Guidance was lifted on sustained AI infrastructure demand, which is the "
                  "kind of catalyst that tends to support a trend rather than start one",
         "source": "news:1"},
        {"point": "The most recent 10-Q gives you the segment detail behind that revenue line",
         "source": "filing:0"},
    ]
    ev_ok, ev_bad = evidence.verify(raw_evidence, catalog)
    inf_ok, inf_bad = evidence.verify(raw_claims, catalog)

    return {
        "ticker": quote["symbol"],
        "asOf": hist.index[-1].isoformat(),
        "timeframe": period,
        "momentum": {
            "lean": "bullish", "confidence": "moderate",
            "summary": "Price is holding above both moving averages with momentum still "
                       "building rather than exhausted, and the recent news explains the "
                       "move rather than contradicting it. The read is a continuation of an "
                       "existing trend, not the start of one — and the stretch above the "
                       "200-day is the part that makes it fragile.",
            "evidence": ev_ok,
        },
        "learning_note": "The useful habit here is checking whether the signals agree. Price "
                         "above both averages tells you the trend; RSI tells you how much room "
                         "is left in it; MACD tells you whether it is still being pushed. When "
                         "all three point the same way the read is easy — it is when they "
                         "disagree that you learn something, so notice which one you are "
                         "discounting and why.",
        "news": {"feed": kept, "note": None,
                 "inference": {"summary": "The two company-specific items both describe demand "
                                          "running ahead of expectations, which is consistent "
                                          "with the price action rather than an explanation for "
                                          "a reversal. Note this is confirmation, not new "
                                          "information — by the time guidance is public it is "
                                          "usually in the price.",
                               "claims": inf_ok}},
        "filings": FILINGS,
        "coverage": coverage,
        "evidenceFilter": report,
        "sources": catalog,
        "meta": {"model": "claude-sonnet-5 (stubbed locally)", "parse_error": False,
                 "unsupportedClaims": ev_bad + inf_bad, "notes": []},
    }


trade_app.orchestrator.analyze = _analyze

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(trade_app.app, host="127.0.0.1", port=8000, log_level="warning")
