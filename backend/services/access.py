"""
Access guard for the paid endpoints (/analyze, /ask) — the pre-share fix.

Every call to these two endpoints spends the owner's Claude key. Once the app's
URL is shared, an unauthenticated visitor could otherwise run up the bill with
zero friction. Two independent, deliberately simple layers (both optional,
both off by default so local dev is unaffected):

- A shared access token (TRADE101_ACCESS_TOKEN): if set, callers must send it
  as the `X-Access-Token` header, or every request is rejected with 401.
- A daily cap (TRADE101_DAILY_CAP, default 50): a process-wide counter over
  both endpoints combined, resetting at UTC midnight, rejecting with 429 once
  exhausted — a backstop even if the token itself leaks or is shared onward.

Deliberately NOT a distributed rate-limiter or per-user quota system — this is
a single free-tier instance for one owner's personal app, not a multi-tenant
product; a process-wide in-memory counter is the right amount of engineering
for that. Restarting the process resets the counter, which is an accepted
trade-off, not a bug.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timezone

from fastapi import Header, HTTPException

_lock = threading.Lock()
_usage = {"day": None, "count": 0}


def _daily_cap() -> int:
    try:
        return int(os.environ.get("TRADE101_DAILY_CAP", "50"))
    except ValueError:
        return 50


def guard_paid_endpoint(x_access_token: str | None = Header(default=None)) -> None:
    """FastAPI dependency: raises 401/429 to block a request before it reaches
    the Claude API. Wire onto /analyze and /ask only — the deterministic
    endpoints (chart, indicators, patterns, compare, watchlist) cost nothing
    and stay open."""
    required = os.environ.get("TRADE101_ACCESS_TOKEN")
    if required and x_access_token != required:
        raise HTTPException(
            status_code=401,
            detail="This app requires an access token to run AI analysis. "
                   "Ask the owner for the link that includes it.",
        )

    today = datetime.now(timezone.utc).date().isoformat()
    with _lock:
        if _usage["day"] != today:
            _usage["day"] = today
            _usage["count"] = 0
        if _usage["count"] >= _daily_cap():
            raise HTTPException(
                status_code=429,
                detail="Daily AI analysis limit reached for this app (a personal-use "
                       "cost safeguard). Please try again tomorrow.",
            )
        _usage["count"] += 1
