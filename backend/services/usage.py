"""
LLM spend ledger — what each part of Trade101 costs to run.

Every Claude call is recorded against the PURPOSE that made it (the momentum
read, the news inference, a future Ask-Claude turn) and the named key that paid
for it. That gives per-use expenditure tracking whether you run one API key or
several — the purpose is recorded independently of the key, so the breakdown
survives consolidating keys, and still lines up with the Anthropic Console when
you split them.

Cost here is a LOCAL ESTIMATE computed from published per-token rates. The
Anthropic Console remains the billing source of truth; a model missing from the
price table is recorded with priced=0 (tokens counted, cost not claimed) rather
than silently guessed — the same "never fabricate a number" rule the rest of the
app follows.
"""
from __future__ import annotations

from datetime import datetime, timezone

from services import storage

# USD per 1M tokens (input, output). Published Anthropic API rates, captured
# 2026-06-24. Update alongside TRADE101_MODEL when rates change.
PRICING = {
    "claude-fable-5-1": (10.00, 50.00),
    "claude-fable-5":   (10.00, 50.00),
    "claude-opus-5":    (5.00, 25.00),
    "claude-opus-4-8":  (5.00, 25.00),
    "claude-opus-4-7":  (5.00, 25.00),
    "claude-opus-4-6":  (5.00, 25.00),
    "claude-sonnet-5":  (2.00, 10.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
}

# Cache pricing is a multiple of the model's input rate.
CACHE_WRITE_MULT = 1.25
CACHE_READ_MULT = 0.10


def estimate_cost(model: str, input_tokens: int, output_tokens: int,
                  cache_write_tokens: int = 0, cache_read_tokens: int = 0) -> tuple[float, bool]:
    """(cost_usd, priced) for one call. priced=False when the model has no known rate."""
    rates = PRICING.get(model)
    if rates is None:
        return 0.0, False
    in_rate, out_rate = rates
    cost = (
        input_tokens * in_rate
        + output_tokens * out_rate
        + cache_write_tokens * in_rate * CACHE_WRITE_MULT
        + cache_read_tokens * in_rate * CACHE_READ_MULT
    ) / 1_000_000
    return round(cost, 6), True


def record(purpose: str, key_env: str, model: str, usage, ticker: str | None = None) -> dict:
    """Log one Claude call. `usage` is the SDK response.usage object (or None).

    Returns the recorded row. Never raises — accounting must not break a request.
    """
    def field(name: str) -> int:
        try:
            return int(getattr(usage, name, 0) or 0)
        except (TypeError, ValueError):
            return 0

    inp, out = field("input_tokens"), field("output_tokens")
    cw, cr = field("cache_creation_input_tokens"), field("cache_read_input_tokens")
    cost, priced = estimate_cost(model, inp, out, cw, cr)

    row = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": purpose,
        "key_env": key_env,
        "model": model,
        "ticker": ticker.upper() if ticker else None,
        "input_tokens": inp,
        "output_tokens": out,
        "cache_write_tokens": cw,
        "cache_read_tokens": cr,
        "cost_usd": cost,
        "priced": 1 if priced else 0,
    }
    try:
        with storage.connect() as conn:
            if conn is not None:
                conn.execute(
                    """INSERT INTO llm_usage (ts, purpose, key_env, model, ticker,
                           input_tokens, output_tokens, cache_write_tokens,
                           cache_read_tokens, cost_usd, priced)
                       VALUES (:ts, :purpose, :key_env, :model, :ticker,
                           :input_tokens, :output_tokens, :cache_write_tokens,
                           :cache_read_tokens, :cost_usd, :priced)""",
                    row,
                )
    except Exception:
        pass  # tracking is observability, never a dependency
    return row


def _agg(conn, group_by: str, since: str | None) -> list[dict]:
    where, params = ("WHERE ts >= ?", [since]) if since else ("", [])
    rows = conn.execute(
        f"""SELECT {group_by} AS name, COUNT(*) AS calls,
                   SUM(input_tokens) AS input_tokens, SUM(output_tokens) AS output_tokens,
                   SUM(cache_write_tokens) AS cache_write_tokens,
                   SUM(cache_read_tokens) AS cache_read_tokens,
                   ROUND(SUM(cost_usd), 6) AS cost_usd,
                   SUM(CASE WHEN priced = 0 THEN 1 ELSE 0 END) AS unpriced_calls
            FROM llm_usage {where}
            GROUP BY {group_by} ORDER BY cost_usd DESC""",
        params,
    ).fetchall()
    return [dict(r) for r in rows]


def summary(since: str | None = None) -> dict:
    """Spend broken down by purpose, by key, and by model, plus the total.

    `since` is an ISO-8601 UTC timestamp; omit for all-time.
    """
    with storage.connect() as conn:
        if conn is None:
            return {"available": False,
                    "reason": "Usage database unavailable — tracking is off, the app is unaffected."}
        by_purpose = _agg(conn, "purpose", since)
        by_key = _agg(conn, "key_env", since)
        by_model = _agg(conn, "model", since)
        total = {
            "calls": sum(r["calls"] for r in by_purpose),
            "cost_usd": round(sum(r["cost_usd"] or 0 for r in by_purpose), 6),
            "input_tokens": sum(r["input_tokens"] or 0 for r in by_purpose),
            "output_tokens": sum(r["output_tokens"] or 0 for r in by_purpose),
            "unpriced_calls": sum(r["unpriced_calls"] or 0 for r in by_purpose),
        }
        return {
            "available": True,
            "since": since,
            "total": total,
            "byPurpose": by_purpose,
            "byKey": by_key,
            "byModel": by_model,
            "note": "Local estimate from published per-token rates; the Anthropic Console is "
                    "the billing source of truth. Calls on a model with no known rate are "
                    "counted but not priced (see unpriced_calls).",
        }
