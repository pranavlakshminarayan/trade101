"""services/net.py — timeout + retry wrappers for flaky yfinance/Yahoo calls.

User-reported (2026-09-17, live on Render): the ecosystem panel for Tencent
(0700.HK) came back with sector/summary/peer-names ALL null, while the exact
same yfinance `.info` calls succeeded instantly when run directly, moments
later, from a different network path. Yahoo's `.info`/`.calendar` endpoint
needs a crumb/cookie handshake that's genuinely flaky from Render's shared
IP (`.history`, which powers the chart, doesn't need this handshake and has
never shown this problem) — a single flaky attempt was silently nullifying
an entire tile's worth of real, available data. `with_retry` gives a second
attempt before giving up."""
import pytest

from services.net import with_retry, with_timeout


def test_with_timeout_returns_result_when_fast_enough():
    assert with_timeout(lambda: 1 + 1, timeout=1) == 2


def test_with_timeout_raises_on_a_genuinely_slow_call():
    import time
    with pytest.raises(TimeoutError):
        with_timeout(lambda: time.sleep(1), timeout=0.1)


def test_with_retry_succeeds_immediately_without_retrying_on_first_success():
    calls = []
    def fn():
        calls.append(1)
        return "ok"
    assert with_retry(fn, timeout=1, backoff=0) == "ok"
    assert len(calls) == 1


def test_with_retry_recovers_from_one_transient_failure():
    # Simulates exactly the reported bug: the first attempt at the crumb
    # handshake fails, the second (moments later) succeeds.
    calls = []
    def fn():
        calls.append(1)
        if len(calls) == 1:
            raise ConnectionError("crumb handshake failed")
        return "ok"
    assert with_retry(fn, timeout=1, attempts=2, backoff=0) == "ok"
    assert len(calls) == 2


def test_with_retry_raises_the_last_error_when_every_attempt_fails():
    def fn():
        raise ConnectionError("still failing")
    with pytest.raises(ConnectionError):
        with_retry(fn, timeout=1, attempts=2, backoff=0)
