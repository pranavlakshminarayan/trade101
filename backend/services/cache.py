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

import time
from typing import Any, Callable

_store: dict[str, tuple[float, Any]] = {}
DEFAULT_TTL = 300.0  # 5 min — matches the Claude prompt-cache window


def get_or_set(key: str, fn: Callable[[], Any], ttl: float = DEFAULT_TTL) -> Any:
    """Return the cached value for `key`, or compute it with `fn()`, store, return.
    A stored `None` is cached too (so we don't re-run a lookup that found nothing)."""
    now = time.time()
    hit = _store.get(key)
    if hit is not None and hit[0] > now:
        return hit[1]
    value = fn()
    _store[key] = (now + ttl, value)
    return value


def clear(key: str | None = None) -> None:
    if key is None:
        _store.clear()
    else:
        _store.pop(key, None)
