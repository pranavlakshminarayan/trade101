"""
Evidence pipeline — decide what the AI is allowed to reason from, and prove
afterwards that it actually did.

Two deterministic gates around the one analysis call:

  BEFORE  select()   — only evidence plausibly ABOUT this company reaches the
                       model. A headline that merely mentions the ticker in a
                       market round-up is noise, and noise is what makes an AI
                       read sound confident about nothing.
  AFTER   verify()   — every claim must name a source that exists in what we
                       sent. A claim citing something we never supplied is
                       dropped, not rewritten: the app would rather show less
                       than show something it cannot trace.

No LLM here. This is the machinery that makes "every AI claim is sourced" a
checkable property instead of a promise in a prompt.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

# A round-up that lists many tickers is rarely ABOUT any one of them.
MARKET_ROUNDUP = re.compile(
    r"\b(stocks? to watch|movers|market wrap|midday|premarket|top gainers|losers|"
    r"futures (?:rise|fall|slip|climb)|week ahead|what to watch)\b", re.I)

# Low-signal syndicated/promotional patterns.
LOW_SIGNAL = re.compile(r"\b(zacks rank|motley fool|should you buy|is it time to buy|"
                        r"3 reasons|7 stocks|best stocks)\b", re.I)


def _tokens(name: str | None) -> list[str]:
    """Distinctive words from a company name ('NVIDIA Corporation' -> ['nvidia'])."""
    if not name:
        return []
    stop = {"inc", "corp", "corporation", "ltd", "limited", "plc", "co", "company",
            "group", "holdings", "the", "sa", "ag", "nv", "se", "spa", "ab", "as"}
    words = re.findall(r"[A-Za-z][A-Za-z&.-]{2,}", name.lower())
    return [w.strip(".-") for w in words if w.strip(".-") not in stop]


def score_item(item: dict, ticker: str, name: str | None, today: date | None = None) -> tuple[float, str]:
    """(relevance 0-1, why). Deterministic and explainable — the learner can be
    told WHY a headline was kept or dropped."""
    today = today or date.today()
    text = f"{item.get('headline') or ''} {item.get('summary') or ''}"
    low = text.lower()
    reasons, score = [], 0.0

    # Does it actually name the company?
    name_hit = any(tok in low for tok in _tokens(name))
    ticker_hit = re.search(rf"\b{re.escape(ticker.split('.')[0])}\b", text, re.I) is not None
    if name_hit:
        score += 0.6; reasons.append("names the company")
    elif ticker_hit:
        score += 0.35; reasons.append("mentions the ticker")
    else:
        return 0.0, "does not mention this company"

    # Named in the headline is stronger than buried in the body.
    head = (item.get("headline") or "").lower()
    if any(tok in head for tok in _tokens(name)) or re.search(
            rf"\b{re.escape(ticker.split('.')[0])}\b", item.get("headline") or "", re.I):
        score += 0.2; reasons.append("in the headline")

    # Recency: a month-old headline explains today's tape far less well.
    try:
        age = (today - datetime.fromisoformat(item["datetime"]).date()).days
        if age <= 3:
            score += 0.2; reasons.append("published in the last 3 days")
        elif age <= 14:
            score += 0.1; reasons.append("published in the last 2 weeks")
        elif age > 45:
            score -= 0.2; reasons.append("over 45 days old")
    except (KeyError, TypeError, ValueError):
        reasons.append("undated")

    if MARKET_ROUNDUP.search(text):
        score -= 0.35; reasons.append("reads as a multi-stock round-up")
    if LOW_SIGNAL.search(text):
        score -= 0.25; reasons.append("promotional / listicle framing")
    if not item.get("url"):
        score -= 0.5; reasons.append("no link to verify")

    return max(0.0, min(1.0, score)), "; ".join(reasons)


def select(items: list[dict], ticker: str, name: str | None,
           threshold: float = 0.5, limit: int = 8) -> tuple[list[dict], dict]:
    """Keep only evidence about THIS company. Returns (kept, report).

    The report is shown to the user — filtering you can't inspect is just a
    different kind of black box.
    """
    scored = []
    for it in items:
        s, why = score_item(it, ticker, name)
        scored.append({**it, "relevance": round(s, 2), "relevanceWhy": why})
    scored.sort(key=lambda x: x["relevance"], reverse=True)

    kept = [x for x in scored if x["relevance"] >= threshold][:limit]
    dropped = [x for x in scored if x not in kept]
    return kept, {
        "considered": len(items),
        "kept": len(kept),
        "dropped": len(dropped),
        "threshold": threshold,
        "droppedExamples": [{"headline": d.get("headline"), "why": d["relevanceWhy"]}
                            for d in dropped[:3]],
    }


# ---- citation verification -------------------------------------------------

def build_catalog(indicators: dict, news_items: list[dict], filings: list[dict]) -> list[dict]:
    """Everything the model is allowed to cite, each with a stable id.

    Giving citations ids (rather than free text) is what lets the UI turn a
    claim into a clickable, checkable source.
    """
    catalog = []
    for k, v in (indicators or {}).items():
        if v is not None and not isinstance(v, (dict, list)):
            catalog.append({"id": f"ind:{k}", "kind": "indicator", "label": k,
                            "detail": f"{k} = {v}", "url": None})
    for i, n in enumerate(news_items or []):
        catalog.append({"id": f"news:{i}", "kind": "news",
                        "label": n.get("headline") or n.get("source") or f"news {i}",
                        "detail": n.get("source"), "url": n.get("url"),
                        "date": n.get("datetime")})
    for i, f in enumerate(filings or []):
        catalog.append({"id": f"filing:{i}", "kind": "filing",
                        "label": f"SEC {f.get('form')} ({f.get('date')})",
                        "detail": "SEC EDGAR", "url": f.get("url"), "date": f.get("date")})
    return catalog


def _resolve(cite: str, catalog: list[dict]) -> dict | None:
    """Match a model-supplied citation to a real catalog entry, by id or label."""
    if not cite or not isinstance(cite, str):
        return None
    c = cite.strip().lower()
    by_id = {e["id"].lower(): e for e in catalog}
    if c in by_id:
        return by_id[c]
    for e in catalog:  # tolerate the model quoting the label instead of the id
        label = (e["label"] or "").lower()
        if label and (c == label or c in label or label in c):
            return e
    return None


def verify(claims: list[dict], catalog: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split claims into (supported, unsupported).

    A supported claim carries the resolved source object, so the UI can show
    WHY it backs the statement. Unsupported claims are never rewritten — they
    are reported, so a sourcing failure is visible rather than papered over.
    """
    supported, unsupported = [], []
    for claim in claims or []:
        if not isinstance(claim, dict):
            continue
        raw = claim.get("source") or claim.get("citation") or ""
        cites = raw if isinstance(raw, list) else [raw]
        resolved = [r for r in (_resolve(str(c), catalog) for c in cites) if r]
        if resolved:
            supported.append({**claim, "citations": resolved})
        else:
            unsupported.append({**claim, "reason": f"cites '{raw}', which was not in the "
                                                   f"evidence supplied to the model"})
    return supported, unsupported


def coverage(news_items: list[dict], filings: list[dict], report: dict) -> dict:
    """How well-sourced this read is — so thin evidence shows as thin.

    Returns a level plus the sentence the UI puts in front of the learner.
    """
    n, f = len(news_items), len(filings)
    if n == 0 and f == 0:
        return {"level": "none", "news": 0, "filings": 0,
                "note": "No company-specific sources were reachable. The read below rests on "
                        "price and indicators alone — treat it as a partial picture."}
    if n + f < 3 or (report.get("kept", 0) == 0 and report.get("considered", 0) > 0):
        return {"level": "thin", "news": n, "filings": f,
                "note": f"Thin coverage: {n} relevant article(s) and {f} filing(s). "
                        f"Lower your confidence in anything the news is said to explain."}
    return {"level": "ok", "news": n, "filings": f,
            "note": f"{n} relevant article(s) and {f} filing(s) informed this read."}
