"""
Company profile / ecosystem — deterministic.

Sector, industry, beta, market cap from Yahoo; peer companies from Finnhub's
free peers endpoint. Beta is the "how it lives in the index/market" signal;
peers are the ecosystem. All real data, degrades gracefully.
"""
from __future__ import annotations

import os

import httpx
import numpy as np
import yfinance as yf

FINNHUB = "https://finnhub.io/api/v1"

# Exchange suffix → the market index a stock's beta is measured against. This is
# what lets us compute beta for non-US listings, where yfinance/Finnhub give none.
# Keyed by the ".XX" suffix; US symbols (no suffix) fall through to the S&P 500.
_INDEX_BY_SUFFIX = {
    "T": ("^N225", "Nikkei 225"), "KS": ("^KS11", "KOSPI"), "KQ": ("^KQ11", "KOSDAQ"),
    "HK": ("^HSI", "Hang Seng"), "SS": ("000001.SS", "SSE Composite"),
    "SZ": ("399001.SZ", "SZSE Component"), "SI": ("^STI", "Straits Times"),
    "NS": ("^NSEI", "Nifty 50"), "BO": ("^BSESN", "BSE Sensex"),
    "DE": ("^GDAXI", "DAX"), "L": ("^FTSE", "FTSE 100"), "PA": ("^FCHI", "CAC 40"),
    "TO": ("^GSPTSE", "S&P/TSX"), "AX": ("^AXJO", "S&P/ASX 200"),
    "SW": ("^SSMI", "SMI"), "AS": ("^AEX", "AEX"), "MI": ("FTSEMIB.MI", "FTSE MIB"),
}
_US_INDEX = ("^GSPC", "S&P 500")


def _index_for(ticker: str) -> tuple[str, str]:
    parts = ticker.upper().rsplit(".", 1)
    if len(parts) == 2 and parts[1] in _INDEX_BY_SUFFIX:
        return _INDEX_BY_SUFFIX[parts[1]]
    return _US_INDEX


def _computed_beta(ticker: str) -> tuple[float | None, str | None]:
    """Beta from ~1y of daily returns vs the stock's regional market index —
    deterministic, so non-US listings get a real beta instead of null.
    Returns (beta, index_name) or (None, None) if the data is insufficient."""
    idx_sym, idx_name = _index_for(ticker)
    try:
        stock = yf.Ticker(ticker).history(period="1y", interval="1d", auto_adjust=True)["Close"]
        index = yf.Ticker(idx_sym).history(period="1y", interval="1d", auto_adjust=True)["Close"]
    except Exception:
        return None, None
    sr = stock.pct_change().dropna()
    ir = index.pct_change().dropna()
    df = np.stack([sr.align(ir, join="inner")[0].to_numpy(),
                   sr.align(ir, join="inner")[1].to_numpy()])
    if df.shape[1] < 60:  # need a meaningful sample
        return None, None
    var = np.var(df[1])
    if var == 0:
        return None, None
    beta = float(np.cov(df[0], df[1])[0][1] / var)
    return round(beta, 3), idx_name


def _peers(ticker: str) -> list[str]:
    key = os.environ.get("TRADE101_NEWS_KEY")  # same Finnhub key as news
    if not key:
        return []
    try:
        r = httpx.get(f"{FINNHUB}/stock/peers", params={"symbol": ticker.upper(), "token": key}, timeout=12)
        r.raise_for_status()
        return [p for p in r.json() if p and p.upper() != ticker.upper()][:8]
    except Exception:
        return []


def get_profile(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = {}
    try:
        info = t.info
    except Exception:
        info = {}

    beta = info.get("beta")
    peers = _peers(ticker)
    is_us = "." not in ticker  # US symbols have no exchange suffix (e.g. AAPL vs 7974.T)

    # If no published beta (the usual non-US case), compute it ourselves against
    # the regional index — deterministic, exact, no external key.
    beta_source = "provider" if beta is not None else None
    beta_index = None
    if beta is None:
        beta, beta_index = _computed_beta(ticker)
        if beta is not None:
            beta_source = "computed"

    # Explain the gaps rather than showing a blank panel. Coverage outside the US
    # is thinner: yfinance often has no beta, and Finnhub's peers endpoint is US-only.
    coverage = {}
    if beta is None:
        coverage["beta"] = (
            "Beta isn't available for this listing"
            + (" (no regional index data)." if not is_us else ".")
        )
    if not peers:
        coverage["peers"] = (
            "Peer companies aren't available for this listing"
            + (" — the peers source currently covers US-listed symbols." if not is_us
               else ".")
        )

    return {
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "beta": beta,
        "betaSource": beta_source,   # "provider" | "computed" | None
        "betaIndex": beta_index,     # index name when computed (e.g. "Nikkei 225")
        "marketCap": info.get("marketCap"),
        # marketCap is denominated in the LISTING'S OWN currency (yfinance convention,
        # same as the quote) — never assume USD. The frontend must format it accordingly.
        "marketCapCurrency": info.get("currency"),
        "exchange": info.get("fullExchangeName") or info.get("exchange"),
        "country": info.get("country"),
        "peers": peers,
        "summary": (info.get("longBusinessSummary") or "")[:360] or None,
        "coverage": coverage,
    }
