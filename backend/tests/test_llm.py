"""agents/llm.py — client timeouts (docs/AUDIT.md finding M11). Previously
unset, meaning a hung Claude request could occupy a FastAPI worker
indefinitely. Verifies the timeout is actually passed to the Anthropic
client, not just documented in a comment."""
from agents import llm


class _FakeUsage:
    input_tokens = 10
    output_tokens = 5
    cache_creation_input_tokens = 0
    cache_read_input_tokens = 0


class _FakeBlock:
    type = "text"
    text = "ok"


class _FakeMessages:
    def create(self, **kwargs):
        return _FakeResponse()


class _FakeResponse:
    stop_reason = "end_turn"
    content = [_FakeBlock()]
    usage = _FakeUsage()


class _FakeClient:
    """Captures the kwargs it was constructed with (in particular `timeout`)
    so the test can assert on them without making a real API call."""
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.messages = _FakeMessages()
        _FakeClient.instances.append(self)


def test_call_sets_the_analysis_timeout(monkeypatch):
    _FakeClient.instances.clear()
    monkeypatch.setenv("FAKE_KEY", "x")
    monkeypatch.setattr(llm.anthropic, "Anthropic", _FakeClient)

    llm.call("FAKE_KEY", "system prompt", "user payload")

    assert len(_FakeClient.instances) == 1
    assert _FakeClient.instances[0].kwargs.get("timeout") == llm.ANALYSIS_TIMEOUT_S


def test_call_chat_sets_the_chat_timeout(monkeypatch):
    _FakeClient.instances.clear()
    monkeypatch.setenv("FAKE_KEY", "x")
    monkeypatch.setattr(llm.anthropic, "Anthropic", _FakeClient)

    llm.call_chat("FAKE_KEY", "system prompt", [{"role": "user", "content": "hi"}])

    assert len(_FakeClient.instances) == 1
    assert _FakeClient.instances[0].kwargs.get("timeout") == llm.CHAT_TIMEOUT_S


def test_timeouts_are_distinct_and_positive():
    # Analysis (high effort, up to 4000 tokens) reasonably gets more time than
    # chat (medium effort, up to 1200 tokens) — not required to be different,
    # but both must be finite and positive (i.e. an actual timeout is set).
    assert llm.ANALYSIS_TIMEOUT_S > 0
    assert llm.CHAT_TIMEOUT_S > 0
