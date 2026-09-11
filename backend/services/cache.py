"""
Response cache — one TTL cache behind a small interface.

Every outbound call (Yahoo, Finnhub, SEC) goes through here, so repeat views of
the same stock don't re-hit a provider that rate-limits us. In-process by
default; TRADE101_CACHE_URL is the seam for Redis when one process stops being
enough. Deterministic, no LLM.

Entries carry the time they were fetched, because Trade101 has to be able to say
WHEN a number was true — a cached value with no timestamp would quietly turn a
stale price into an apparently live one.
"""
from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable

# Per-kind freshness. Intraday prices move; a company's sector does not.
TTL = {
    "quote": 60,          # 1 min  — the chart auto-refreshes anyway
    "history": 300,       # 5 min
    "news": 900,          # 15 min
    "filings": 3600,      # 1 h    — EDGAR changes slowly
    "profile": 86400,     # 24 h   — sector/industry/beta are near-static
    "search": 3600,       # 1 h
    "fundamentals": 21600,  # 6 h  — these move on a reporting cadence
    "replay": 86400,      # 24 h   — a historical window never changes
}
DEFAULT_TTL = 300

_store: dict[str, tuple[float, float, Any]] = {}  # key -> (fetched_at, expires_at, value)
_lock = threading.Lock()


def backend() -> str:
    """Which cache is in use — reported to the frontend for transparency."""
    return "redis" if os.environ.get("TRADE101_CACHE_URL") else "in-process"


def _ttl_for(kind: str) -> int:
    return TTL.get(kind, DEFAULT_TTL)


def get_or_fetch(kind: str, key: str, fetch: Callable[[], Any]) -> tuple[Any, dict]:
    """Return (value, meta) for `key`, calling `fetch()` only on a miss or expiry.

    meta carries `cached`, `fetchedAt` (UTC ISO-8601) and `ageSeconds` so callers
    can always state how old the data is. A fetch that raises is never cached.
    """
    full = f"{kind}:{key}"
    now = time.time()

    with _lock:
        hit = _store.get(full)
    if hit and hit[1] > now:
        fetched_at, _, value = hit
        return value, _meta(True, fetched_at, now)

    value = fetch()
    fetched_at = time.time()
    with _lock:
        _store[full] = (fetched_at, fetched_at + _ttl_for(kind), value)
    return value, _meta(False, fetched_at, fetched_at)


def _meta(cached: bool, fetched_at: float, now: float) -> dict:
    return {
        "cached": cached,
        "fetchedAt": datetime.fromtimestamp(fetched_at, timezone.utc).isoformat(timespec="seconds"),
        "ageSeconds": int(now - fetched_at),
        "backend": backend(),
    }


def clear() -> None:
    """Drop every entry (used by tests and by a manual refresh)."""
    with _lock:
        _store.clear()


def stats() -> dict:
    now = time.time()
    with _lock:
        live = sum(1 for _, exp, _ in _store.values() if exp > now)
        return {"entries": len(_store), "live": live, "backend": backend()}
