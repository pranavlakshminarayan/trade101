"""services/cache.py — the per-key lock that dedupes concurrent misses.

Bug (user-reported 2026-09-18, live on Render): /analyze's gather() and
/ecosystem both call company.get_profile() for the same ticker. The frontend
fires both requests within milliseconds of each other, so both missed this
cache before either had stored a result — each firing its own full ~11-call
concurrent yfinance blitz at once, doubling the load on Yahoo's already-flaky
.info endpoint right when it's most likely to fail. The user saw this as an
inverse correlation: whichever of the two features "won" the race would work,
the other would come back empty/stuck. A per-key lock makes only the FIRST
concurrent caller actually run `fn()`; everyone else waits for that one real
fetch and reuses its result."""
import threading
import time

from services import cache


def test_get_or_set_returns_cached_value_on_a_plain_hit():
    calls = []
    def fn():
        calls.append(1)
        return "value"
    key = f"test-plain-hit-{time.time()}"
    assert cache.get_or_set(key, fn) == "value"
    assert cache.get_or_set(key, fn) == "value"
    assert len(calls) == 1  # second call was a cache hit, fn() not re-run


def test_concurrent_misses_for_the_same_key_only_run_fn_once():
    calls = []
    call_lock = threading.Lock()

    def slow_fn():
        with call_lock:
            calls.append(1)
        time.sleep(0.2)  # simulates the real ~11-call yfinance blitz
        return "profile-data"

    key = f"test-concurrent-{time.time()}"
    results = []
    def worker():
        results.append(cache.get_or_set(key, slow_fn))

    # Simulates /analyze's gather() and /ecosystem firing within
    # milliseconds of each other — both starting before either has cached.
    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(calls) == 1, "fn() should only run once even with 5 concurrent misses"
    assert all(r == "profile-data" for r in results)


def test_concurrent_misses_for_DIFFERENT_keys_both_run_fn():
    # The lock is per-key — two different tickers must not block each other.
    calls = []
    def fn():
        calls.append(1)
        time.sleep(0.05)
        return "value"

    k1, k2 = f"test-diff-a-{time.time()}", f"test-diff-b-{time.time()}"
    t1 = threading.Thread(target=lambda: cache.get_or_set(k1, fn))
    t2 = threading.Thread(target=lambda: cache.get_or_set(k2, fn))
    t1.start(); t2.start()
    t1.join(); t2.join()
    assert len(calls) == 2
