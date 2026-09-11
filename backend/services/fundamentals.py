"""
Company fundamentals — the business behind the ticker. Deterministic, no LLM.

Earnings dates, results versus estimates, revenue and margin trend, cash flow,
and valuation context, each with the primary filing to read it in. This is the
half of a company that a price chart cannot show, and it is what turns "the line
went up" into a question the learner can actually investigate.

Every field is optional and independently degradable: Yahoo's fundamentals
coverage is strong for US large caps and patchy elsewhere, so a missing value is
reported as missing — never inferred, never back-filled from a ratio.
"""
from __future__ import annotations

import math

import pandas as pd
import yfinance as yf

from services import cache

# Rows we look for, in the order Yahoo tends to name them.
_REVENUE_ROWS = ("Total Revenue", "TotalRevenue", "Revenue")
_NET_INCOME_ROWS = ("Net Income", "NetIncome", "Net Income Common Stockholders")
_GROSS_ROWS = ("Gross Profit", "GrossProfit")
_OP_INCOME_ROWS = ("Operating Income", "OperatingIncome")
_FCF_ROWS = ("Free Cash Flow", "FreeCashFlow")
_OCF_ROWS = ("Operating Cash Flow", "OperatingCashFlow",
             "Total Cash From Operating Activities")


def _clean(v):
    """None for anything that is not a real, finite number."""
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else f


def _row(df: pd.DataFrame | None, names: tuple[str, ...]) -> list[dict] | None:
    """Pull one labelled row out of a Yahoo statement frame as [{period, value}]."""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return None
    for name in names:
        if name in df.index:
            series = df.loc[name]
            out = []
            for period, value in series.items():
                v = _clean(value)
                if v is not None:
                    label = period.date().isoformat() if hasattr(period, "date") else str(period)
                    out.append({"period": label, "value": v})
            out.sort(key=lambda x: x["period"])
            return out or None
    return None


def _pct_change(series: list[dict] | None) -> float | None:
    """Newest period versus the one before it, as a percentage."""
    if not series or len(series) < 2:
        return None
    prev, last = series[-2]["value"], series[-1]["value"]
    if not prev:
        return None
    return round((last - prev) / abs(prev) * 100, 2)


def _margin(numer: list[dict] | None, denom: list[dict] | None) -> list[dict] | None:
    """Margin series, computed only where both sides share a period."""
    if not numer or not denom:
        return None
    by_period = {d["period"]: d["value"] for d in denom}
    out = []
    for n in numer:
        d = by_period.get(n["period"])
        if d:
            out.append({"period": n["period"], "value": round(n["value"] / d * 100, 2)})
    return out or None


def _earnings(t) -> dict:
    """Next/last earnings date and the most recent surprise versus estimate."""
    result = {"nextDate": None, "lastDate": None, "epsActual": None,
              "epsEstimate": None, "surprisePercent": None, "note": None}
    try:
        df = t.earnings_dates
    except Exception:
        df = None
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        result["note"] = "No earnings calendar available from this provider for this symbol."
        return result

    now = pd.Timestamp.now(tz=df.index.tz) if df.index.tz is not None else pd.Timestamp.now()
    future = df[df.index > now]
    past = df[df.index <= now]

    if not future.empty:
        result["nextDate"] = future.index.min().isoformat()
    if not past.empty:
        latest = past.index.max()
        result["lastDate"] = latest.isoformat()
        row = past.loc[latest]
        if isinstance(row, pd.DataFrame):  # duplicate timestamps
            row = row.iloc[0]
        result["epsActual"] = _clean(row.get("Reported EPS"))
        result["epsEstimate"] = _clean(row.get("EPS Estimate"))
        result["surprisePercent"] = _clean(row.get("Surprise(%)"))
    return result


def _valuation(info: dict) -> dict:
    """Valuation multiples as reported — context, never a verdict."""
    return {
        "trailingPE": _clean(info.get("trailingPE")),
        "forwardPE": _clean(info.get("forwardPE")),
        "priceToBook": _clean(info.get("priceToBook")),
        "priceToSales": _clean(info.get("priceToSalesTrailing12Months")),
        "enterpriseToEbitda": _clean(info.get("enterpriseToEbitda")),
        "marketCap": _clean(info.get("marketCap")),
        "note": "A multiple is a comparison, not a judgement: it only means something "
                "against this company's own history and its sector. A low P/E can mean "
                "cheap or it can mean the market expects earnings to fall.",
    }


def get_fundamentals(ticker: str) -> dict:
    """Cached for 6h — fundamentals change on a reporting cadence, not a tick."""
    result, _ = cache.get_or_fetch("fundamentals", ticker.upper(),
                                   lambda: _fetch(ticker))
    return result


def _fetch(ticker: str) -> dict:
    t = yf.Ticker(ticker)

    info, income, cashflow = {}, None, None
    notes = []
    try:
        info = t.info or {}
    except Exception:
        notes.append("Company profile unavailable from the provider.")
    try:
        income = t.income_stmt
    except Exception:
        notes.append("Income statement unavailable from the provider.")
    try:
        cashflow = t.cashflow
    except Exception:
        notes.append("Cash-flow statement unavailable from the provider.")

    revenue = _row(income, _REVENUE_ROWS)
    net_income = _row(income, _NET_INCOME_ROWS)
    gross = _row(income, _GROSS_ROWS)
    op_income = _row(income, _OP_INCOME_ROWS)
    fcf = _row(cashflow, _FCF_ROWS) or _row(cashflow, _OCF_ROWS)

    covered = sum(1 for x in (revenue, net_income, fcf) if x)
    if covered == 0:
        notes.append("No financial statements were returned for this symbol. Coverage is "
                     "strongest for US-listed large caps; many non-US listings have none.")

    return {
        "ticker": ticker.upper(),
        "currency": info.get("financialCurrency") or info.get("currency"),
        "earnings": _earnings(t),
        "revenue": {"series": revenue, "changePercent": _pct_change(revenue)},
        "netIncome": {"series": net_income, "changePercent": _pct_change(net_income)},
        "margins": {
            "gross": _margin(gross, revenue),
            "operating": _margin(op_income, revenue),
            "net": _margin(net_income, revenue),
            "note": "Margin is what the company keeps from each unit of revenue. Rising "
                    "revenue with falling margin means growth is costing more to buy.",
        },
        "cashFlow": {"series": fcf, "changePercent": _pct_change(fcf),
                     "note": "Cash flow is harder to flatter than reported profit, which is "
                             "why it is worth reading alongside net income rather than instead."},
        "valuation": _valuation(info),
        "coverage": {
            "statements": covered,
            "level": "ok" if covered >= 2 else "thin" if covered == 1 else "none",
        },
        "meta": {
            "provider": "Yahoo Finance",
            "note": "Fundamentals are cached for up to 6h and are reported as filed. "
                    "Read them against the primary filing linked alongside.",
            "notes": notes,
        },
    }
