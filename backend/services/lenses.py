"""
Style lenses — the same data, read the way five different kinds of participant
read it. Deterministic; no LLM, no cost, nothing to hallucinate.

A lens is NOT a trading style to copy. It is a way of showing that "what the
chart says" depends entirely on what you were looking for: a trend follower and
a mean-reversion trader can look at one chart and reach opposite conclusions
without either being wrong, because they are answering different questions.

So every lens must declare four things, and the UI must show all four:
  considers   — what it weighs
  ignores     — what it deliberately does not look at (usually the most
                informative part, and the part a single confident narrative hides)
  conflicts   — evidence in THIS data that argues against its own reading
  failureModes— how this way of reading goes wrong

There is deliberately NO day-trading lens. On ~15-minute delayed data an
intraday read would be precise-looking and wrong, which is worse than absent.
"""
from __future__ import annotations


def _g(d: dict | None, *path, default=None):
    """Safe nested get."""
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
    return default if cur is None else cur


def _pct(a: float | None, b: float | None) -> float | None:
    if a is None or b in (None, 0):
        return None
    return round((a - b) / abs(b) * 100, 2)


# --- individual lenses ------------------------------------------------------

def _trend(ind: dict, fund: dict | None) -> dict:
    price, s50, s200 = ind.get("price"), ind.get("sma50"), ind.get("sma200")
    vol_chg = ind.get("volume_vs_20d_pct")
    above50, above200 = ind.get("above_sma50"), ind.get("above_sma200")

    reading, evidence, conflicts = [], [], []

    if s50 is not None and s200 is not None:
        stacked = s50 > s200
        reading.append("the medium-term average is above the long-term one, the classic "
                       "shape of an established uptrend" if stacked else
                       "the medium-term average is below the long-term one, the shape of an "
                       "established downtrend")
        evidence.append({"point": f"SMA50 {s50} vs SMA200 {s200}", "source": "ind:sma50"})
    else:
        reading.append("there is not enough history to compare the 50- and 200-day averages")

    if price is not None and s200 is not None:
        gap = _pct(price, s200)
        evidence.append({"point": f"price is {gap:+.2f}% versus its 200-day average"
                                 if gap is not None else "price vs SMA200 unavailable",
                         "source": "ind:sma200"})
        if gap is not None and abs(gap) > 25:
            conflicts.append(f"Price is {gap:+.2f}% from its 200-day average — a long way "
                             f"extended. Trend-following reads are weakest right after a "
                             f"stretch like this, because the snap-back is the same size.")

    if vol_chg is not None:
        evidence.append({"point": f"volume is {vol_chg:+.1f}% versus its 20-day average",
                         "source": "ind:volume_vs_20d_pct"})
        if vol_chg < -20 and (above50 or above200):
            conflicts.append("Price is holding up but volume is well below its 20-day "
                             "average. A trend carried on thinning participation is the "
                             "one this lens most often misreads.")

    if above50 is not None and above200 is not None and above50 != above200:
        conflicts.append("Price is on opposite sides of its 50- and 200-day averages — the "
                         "medium and long trends disagree, which is exactly the situation "
                         "this lens has no clean answer for.")

    lean = ("bullish" if (above50 and above200) else
            "bearish" if (above50 is False and above200 is False) else "mixed")

    return {
        "id": "trend",
        "name": "Trend",
        "question": "Is there an established direction, and is participation confirming it?",
        "lean": lean,
        "reading": "Read as a trend question, " + "; ".join(reading) + ".",
        "evidence": evidence,
        "considers": ["Price relative to the 50- and 200-day averages",
                      "Whether those averages are stacked in trend order",
                      "Volume as confirmation of participation"],
        "ignores": ["Valuation — a trend lens has no opinion on whether the price is sane",
                    "Earnings and fundamentals entirely",
                    "News and catalysts",
                    "How far the move has already run"],
        "conflicts": conflicts,
        "failureModes": [
            "Whipsaws in a range: the averages cross back and forth and every signal is late.",
            "It is always late by construction — a moving average confirms a move after it happened.",
            "It says nothing about magnitude, so it cannot tell a 2% drift from a 40% run.",
        ],
    }


def _swing(ind: dict, fund: dict | None) -> dict:
    rsi = ind.get("rsi14")
    macd_l, macd_s = _g(ind, "macd", "macd"), _g(ind, "macd", "signal")
    hist = _g(ind, "macd", "hist")
    up, low, mid = _g(ind, "bollinger", "upper"), _g(ind, "bollinger", "lower"), _g(ind, "bollinger", "middle")
    price = ind.get("price")

    evidence, conflicts, reading = [], [], []

    if rsi is not None:
        evidence.append({"point": f"RSI(14) is {rsi}", "source": "ind:rsi14"})
        reading.append("momentum is stretched to the upside" if rsi >= 70 else
                       "momentum is stretched to the downside" if rsi <= 30 else
                       "momentum is in the middle of its range, with room either way")
    if macd_l is not None and macd_s is not None:
        evidence.append({"point": f"MACD {macd_l} vs signal {macd_s}", "source": "ind:macd.macd"})
        reading.append("MACD is above its signal, so short-term momentum is building"
                       if macd_l >= macd_s else
                       "MACD is below its signal, so short-term momentum is fading")
        if rsi is not None:
            rising = macd_l >= macd_s
            if rising and rsi >= 70:
                conflicts.append("Momentum is still building while RSI is already stretched — "
                                 "these two point opposite ways, and this lens cannot tell you "
                                 "which resolves first.")
            if not rising and rsi <= 30:
                conflicts.append("Momentum is still fading while RSI is already washed out — "
                                 "the same conflict in reverse.")

    if price is not None and up is not None and low is not None:
        width = _pct(up, low)
        evidence.append({"point": f"Bollinger band width is about {width}% of the lower band",
                         "source": "ind:bollinger.upper"})
        if width is not None and width < 8:
            conflicts.append("The bands are unusually narrow. Volatility this compressed "
                             "tends to expand, and it gives no clue about direction.")

    lean = ("bearish" if (rsi is not None and rsi >= 70) else
            "bullish" if (rsi is not None and rsi <= 30) else
            "bullish" if (macd_l is not None and macd_s is not None and macd_l >= macd_s) else
            "bearish" if (macd_l is not None and macd_s is not None) else "neutral")

    return {
        "id": "swing",
        "name": "Swing",
        "question": "Over days to weeks, is momentum building or exhausting?",
        "lean": lean,
        "reading": "Read as a momentum question, " + "; ".join(reading) + "." if reading
                   else "Not enough data to read momentum.",
        "evidence": evidence,
        "considers": ["RSI as a stretch gauge", "MACD versus its signal line",
                      "Bollinger width as a volatility state", "Recent catalysts, when sourced"],
        "ignores": ["The long-term trend — a swing read can be bullish inside a bear market",
                    "Valuation and fundamentals completely",
                    "Whether the company is any good"],
        "conflicts": conflicts,
        "failureModes": [
            "RSI can sit above 70 for months in a strong trend; 'overbought' is not a ceiling.",
            "In a hard trend, momentum oscillators give a stream of losing counter-signals.",
            "Short horizons mean more decisions, more noise, and more chances to be wrong.",
        ],
    }


def _mean_reversion(ind: dict, fund: dict | None) -> dict:
    price = ind.get("price")
    up, low, mid = _g(ind, "bollinger", "upper"), _g(ind, "bollinger", "lower"), _g(ind, "bollinger", "middle")
    rsi = ind.get("rsi14")
    s200 = ind.get("sma200")

    evidence, conflicts, reading = [], [], []
    position = None

    if price is not None and up is not None and low is not None and up != low:
        position = round((price - low) / (up - low) * 100, 1)
        evidence.append({"point": f"price sits at {position}% of the Bollinger range",
                         "source": "ind:bollinger.upper"})
        reading.append("price is near the top of its recent range" if position > 80 else
                       "price is near the bottom of its recent range" if position < 20 else
                       "price is mid-range, which is where this lens has least to say")
    if rsi is not None:
        evidence.append({"point": f"RSI(14) is {rsi}", "source": "ind:rsi14"})

    # The critical caveat: mean reversion fails hardest in a strong trend.
    if s200 is not None and price is not None:
        gap = _pct(price, s200)
        if gap is not None and abs(gap) > 15:
            conflicts.append(
                f"Price is {gap:+.2f}% from its 200-day average — this is a trending market, "
                f"and a trending market is precisely where 'it must come back' fails worst. "
                f"There is no rule that says a stretched price returns to any average.")

    lean = ("bearish" if (position is not None and position > 80) else
            "bullish" if (position is not None and position < 20) else "neutral")

    return {
        "id": "mean-reversion",
        "name": "Mean reversion",
        "question": "Is price unusually far from its own recent average?",
        "lean": lean,
        "reading": ("Read as a range question, " + "; ".join(reading) + "."
                    if reading else "Not enough data to place price within a range."),
        "evidence": evidence,
        "considers": ["Where price sits inside its recent volatility range",
                      "RSI as a stretch gauge", "How wide that range currently is"],
        "ignores": ["Whether there is a reason for the move — a collapse on real news looks "
                    "identical to noise on this lens",
                    "The direction of the longer trend", "Fundamentals and valuation"],
        "conflicts": conflicts,
        "failureModes": [
            "This is the most dangerous lens for a beginner: it reads every fall as a "
            "discount, including falls that never recover.",
            "'Far from average' has no upper bound — a stock 30% below its average can go "
            "60% below.",
            "It has no mechanism for distinguishing a temporary dislocation from a permanent "
            "repricing, and those look the same on a chart.",
        ],
        "caveat": "Treat this lens as the most heavily caveated of the five. It describes "
                  "where price sits in a range; it does not imply price will return.",
    }


def _long_term(ind: dict, fund: dict | None) -> dict:
    evidence, conflicts, reading = [], [], []
    rev = _g(fund, "revenue", "changePercent")
    ni = _g(fund, "netIncome", "changePercent")
    fcf = _g(fund, "cashFlow", "changePercent")
    pe = _g(fund, "valuation", "trailingPE")
    coverage = _g(fund, "coverage", "level", default="none")

    if coverage == "none":
        reading.append("no financial statements were available for this company, so this "
                       "lens cannot be applied — which is itself worth knowing, rather than "
                       "substituting a chart read in its place")
    else:
        if rev is not None:
            evidence.append({"point": f"revenue changed {rev:+.2f}% in the latest period",
                             "source": "fund:revenue"})
            reading.append(f"revenue {'grew' if rev >= 0 else 'fell'} {abs(rev):.1f}%")
        if ni is not None:
            evidence.append({"point": f"net income changed {ni:+.2f}%", "source": "fund:netIncome"})
        if fcf is not None:
            evidence.append({"point": f"free cash flow changed {fcf:+.2f}%", "source": "fund:cashFlow"})
        if pe is not None:
            evidence.append({"point": f"trailing P/E is {pe}", "source": "fund:valuation"})

        if rev is not None and ni is not None and rev > 0 and ni < 0:
            conflicts.append("Revenue is growing while net income is falling — growth is "
                             "costing more than it brings in. A chart-based lens cannot see "
                             "this at all.")
        if ni is not None and fcf is not None and ni > 0 and fcf < 0:
            conflicts.append("Reported profit is positive while cash flow is negative. Cash "
                             "is the harder number to flatter, so this gap is worth "
                             "understanding before anything else here.")

    lean = ("bullish" if (rev is not None and rev > 0 and (ni is None or ni > 0)) else
            "bearish" if (rev is not None and rev < 0) else "neutral")

    return {
        "id": "long-term",
        "name": "Long term",
        "question": "Is the underlying business growing, and what is being paid for it?",
        "lean": lean if coverage != "none" else "unknown",
        "reading": ("Read as a business question, " + "; ".join(reading) + "."
                    if reading else "No fundamentals available."),
        "evidence": evidence,
        "considers": ["Revenue, profit and cash-flow direction", "Margin trend",
                      "Valuation multiples as context", "Primary filings"],
        "ignores": ["The chart entirely — price action plays no part in this lens",
                    "Timing of any kind", "Short-term momentum and sentiment"],
        "conflicts": conflicts,
        "failureModes": [
            "Accounting figures are backward-looking and arrive months after the period.",
            "A cheap multiple is often cheap for a reason the statements do not show.",
            "A good business and a good price are different questions; this lens blurs them.",
            "Coverage is patchy outside US large caps — absent data is not good news.",
        ],
    }


def _event_driven(ind: dict, fund: dict | None, news: list | None, filings: list | None) -> dict:
    evidence, conflicts, reading = [], [], []
    next_earnings = _g(fund, "earnings", "nextDate")
    surprise = _g(fund, "earnings", "surprisePercent")
    n_news, n_filings = len(news or []), len(filings or [])

    if next_earnings:
        evidence.append({"point": f"next earnings dated {next_earnings[:10]}",
                         "source": "fund:earnings"})
        reading.append("there is a scheduled earnings date ahead, which is the single most "
                       "reliable source of a large move in this stock")
    else:
        reading.append("no earnings date was available, so the main scheduled catalyst is unknown")

    if surprise is not None:
        evidence.append({"point": f"last reported EPS surprise was {surprise:+.2f}%",
                         "source": "fund:earnings"})

    if n_filings:
        evidence.append({"point": f"{n_filings} recent SEC filing(s) available",
                         "source": "filing:0"})
    if n_news:
        evidence.append({"point": f"{n_news} relevant article(s) passed the evidence filter",
                         "source": "news:0"})

    if n_news == 0 and n_filings == 0:
        conflicts.append("No company-specific news or filings were reachable. This lens is "
                         "built entirely on catalysts, so with none sourced it has nothing "
                         "to say — an absent catalyst is not the same as no catalyst.")

    return {
        "id": "event-driven",
        "name": "Event driven",
        "question": "What scheduled or disclosed events could move this, and when?",
        "lean": "neutral",
        "reading": "Read as a catalyst question, " + "; ".join(reading) + ".",
        "evidence": evidence,
        "considers": ["Earnings dates and past surprise", "Recent filings and disclosures",
                      "Sourced company news", "Sensitivity to the broader market (beta)"],
        "ignores": ["Chart shape and technical levels",
                    "Whether the valuation is reasonable",
                    "Anything not yet public — this lens is strictly backward- and "
                    "calendar-looking"],
        "conflicts": conflicts,
        "failureModes": [
            "The event happening is not the same as the price reacting — 'sell the news' is "
            "the normal case, not the exception.",
            "By the time news is public it is usually in the price already.",
            "Scheduled dates move, and unscheduled events dominate exactly when they matter.",
        ],
    }


def build(indicators: dict, fundamentals: dict | None = None,
          news: list | None = None, filings: list | None = None) -> dict:
    """All five lenses over the same snapshot, plus the disagreement between them."""
    ind = indicators or {}
    lenses = [
        _trend(ind, fundamentals),
        _swing(ind, fundamentals),
        _mean_reversion(ind, fundamentals),
        _long_term(ind, fundamentals),
        _event_driven(ind, fundamentals, news, filings),
    ]

    leans = {l["lean"] for l in lenses} - {"neutral", "unknown"}
    return {
        "lenses": lenses,
        "disagreement": {
            "level": "high" if len(leans) > 1 else "low" if leans else "none",
            "note": (
                "These lenses do not agree, and that is the point: each is answering a "
                "different question, so a single confident verdict would have to hide one "
                "of them. When you read a market opinion anywhere, the useful question is "
                "which lens it is using — and which it is quietly ignoring."
                if len(leans) > 1 else
                "These lenses happen to point the same way here. That is worth noticing, "
                "but it is not confirmation: they share the same input data, so agreement "
                "between them is much weaker evidence than it feels like."
            ),
        },
        "excluded": {
            "day-trading": "Deliberately not offered. This app runs on data delayed by "
                           "roughly 15 minutes, and an intraday lens on delayed data would "
                           "look precise while being wrong — the most damaging combination "
                           "for someone learning.",
        },
        "meta": {"deterministic": True,
                 "note": "Every lens here is computed from the exact numbers by code, not "
                         "written by a model. Nothing on this panel can be hallucinated."},
    }
