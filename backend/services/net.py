"""
Hard wall-clock timeouts for calls to providers (yfinance/Yahoo) that don't
reliably time out on their own.

Bug (user-reported 2026-09-17, live on Render): searching "SK hynix" hung
forever on the 10D chart tab, and the Ecosystem panel showed a nonsensical
peer graph. Root cause: yfinance's underlying Yahoo requests default to a
30s timeout PER request, but a single ecosystem/research call can chain
several of them sequentially (info, calendar, beta history x2, peer names) —
so a slow or rate-limited response (much more common from Render's shared
datacenter IP than from a home IP in local dev) can stack into 60s, 90s, or
more, with nothing in this app ever giving up. `with_timeout` bounds a call
to a hard wall-clock deadline: if the call doesn't finish in time, the
caller gets a `TimeoutError` back and can degrade gracefully (matching the
rest of this app's "never fabricate, explain the gap" philosophy) instead of
hanging the request — and the UI — indefinitely. The underlying call keeps
running in its worker thread until it actually finishes or errors; this
frees the caller, it doesn't cancel the network request.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutureTimeout

_POOL = ThreadPoolExecutor(max_workers=32, thread_name_prefix="net-timeout")


def with_timeout(fn, *args, timeout: float = 15, **kwargs):
    """Run fn(*args, **kwargs) with a hard deadline. Raises TimeoutError if it
    doesn't finish in time; any other exception from fn propagates as-is."""
    fut = _POOL.submit(fn, *args, **kwargs)
    try:
        return fut.result(timeout=timeout)
    except _FutureTimeout:
        raise TimeoutError(f"provider call exceeded {timeout}s")
