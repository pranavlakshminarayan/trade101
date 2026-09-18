"""
Tiny in-memory TTL cache — deterministic, process-local.

Used to hold a ticker's gathered data bundle briefly so that a burst of requests
(the analysis run, then several Ask-Claude chat turns) reuses ONE identical
bundle instead of re-fetching. Keeping the bundle byte-identical across chat
turns is also what lets the Claude prompt cache hit on the shared context.

Single-user prototype scope: a plain dict, no eviction beyond TTL expiry. Swap
for Redis/SQLite here if this ever needs to be shared across processes.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable

_store: dict[str, tuple[float, Any]] = {}
DEFAULT_TTL = 300.0  # 5 min — matches the Claude prompt-cache window

# Bug (user-reported 2026-09-18): /analyze's gather() and /ecosystem both call
# company.get_profile() for the SAME ticker — the frontend fires both requests
# within milliseconds of each other, so both missed this cache before either
# had stored a result, and both fired their own full ~11-call concurrent
# yfinance blitz at once. Doubling the load on Yahoo's already-flaky
# crumb-negotiated .info endpoint (services/net.py) made the intermittent
# failure noticeably WORSE for exactly the pair of features the user reported
# ("if ecosystem works, the AI buttons don't, and vice versa") — they were
# racing each other for the same fragile resource. A per-key lock makes only
# the FIRST concurrent caller actually run `fn()`; everyone else waits for
# that one real fetch and reuses its result, instead of each starting their
# own redundant, contention-worsening attempt.
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(key: str) -> threading.Lock:
    with _locks_guard:
        lock = _locks.get(key)
        if lock is None:
            lock = _locks[key] = threading.Lock()
        return lock


def get_or_set(
    key: str, fn: Callable[[], Any], ttl: float = DEFAULT_TTL,
    should_cache: Callable[[Any], bool] = lambda v: True,
) -> Any:
    """Return the cached value for `key`, or compute it with `fn()`, store, return.
    A stored `None` is cached too (so we don't re-run a lookup that found nothing).
    Concurrent callers for the same key that both miss the cache block on one
    shared lock so only one of them actually runs `fn()` — see the note above.

    Bug (user-reported 2026-09-18, caught right after the lock fix above
    shipped): `company.get_profile()` never raises — a failed Yahoo `.info`
    call degrades internally to a dict of `None`s rather than an exception,
    so the FIRST caller's one bad attempt was getting cached as a normal,
    successful result for the full 5-min TTL — every subsequent request for
    that ticker, even ones that would have succeeded on their own, got stuck
    replaying that one failure. Confirmed live: three separate `/ecosystem`
    calls, 3s apart, all returned the byte-identical empty profile. `should_cache`
    lets a caller reject a degraded-looking result so it's never stored — the
    next request gets a genuinely fresh attempt instead of the poisoned one."""
    now = time.time()
    hit = _store.get(key)
    if hit is not None and hit[0] > now:
        return hit[1]
    with _lock_for(key):
        # Re-check: another thread may have just filled this in while we waited.
        now = time.time()
        hit = _store.get(key)
        if hit is not None and hit[0] > now:
            return hit[1]
        value = fn()
        if should_cache(value):
            _store[key] = (now + ttl, value)
        return value


def clear(key: str | None = None) -> None:
    if key is None:
        _store.clear()
    else:
        _store.pop(key, None)
