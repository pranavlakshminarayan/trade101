"""
Thin wrapper around the Claude API for Trade101's agents.

- Each agent uses its own named key (per-component usage tracking) via env vars.
- Model is configurable (TRADE101_MODEL, default claude-opus-5). If the user
  points it at Haiku, we drop the adaptive-thinking/effort params it doesn't take.
- Missing key → MissingKeyError so the endpoint can degrade gracefully (the
  deterministic chart + indicators still render without any AI).
"""
from __future__ import annotations

import os

import anthropic

# Default to Sonnet 5 (cheaper than Opus, strong reasoning). Override with
# TRADE101_MODEL in .env (e.g. claude-opus-5 for max depth, claude-haiku-4-5 for cheapest).
MODEL = os.environ.get("TRADE101_MODEL", "claude-sonnet-5")


class MissingKeyError(RuntimeError):
    pass


def call(key_env: str, system: str, user: str, effort: str = "high", max_tokens: int = 4000) -> str:
    """Call Claude with the key named by `key_env`. Returns the text response.

    The system prompt is sent as a cache_control block: it's byte-identical on
    every call (only the per-ticker `user` payload varies, and it comes after),
    so Claude serves it from the prompt cache at ~0.1× input cost on any call
    within the 5-min window — cutting spend across tickers/sessions. Effective
    only when the system prompt clears the model's minimum cacheable size
    (512 tok on Opus 5 / Fable; 1024 on Sonnet 5) — ours does. A prefix below the
    minimum silently won't cache, but the marker is harmless.
    """
    key = os.environ.get(key_env)
    if not key:
        raise MissingKeyError(
            f"AI narration unavailable — set {key_env} in your .env "
            f"(a named Claude API key). The chart and indicators work without it."
        )
    client = anthropic.Anthropic(api_key=key)

    kwargs = {}
    if "haiku" not in MODEL:  # adaptive thinking + effort aren't valid on Haiku
        kwargs["thinking"] = {"type": "adaptive"}
        kwargs["output_config"] = {"effort": effort}

    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
        **kwargs,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("The model declined this request.")
    _log_usage(resp.usage)
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def call_chat(key_env: str, system: str, messages: list[dict],
              effort: str = "medium", max_tokens: int = 1200) -> str:
    """Multi-turn variant: cached `system` prefix + a full `messages` history.
    Used by the Ask-Claude chat; the cached system (guardrails + the ticker's
    stable data context) is reused across conversation turns."""
    key = os.environ.get(key_env)
    if not key:
        raise MissingKeyError(
            f"Ask-Claude is unavailable — set {key_env} in your .env (a named Claude API key)."
        )
    client = anthropic.Anthropic(api_key=key)

    kwargs = {}
    if "haiku" not in MODEL:
        kwargs["thinking"] = {"type": "adaptive"}
        kwargs["output_config"] = {"effort": effort}

    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=messages,
        **kwargs,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("The model declined this request.")
    _log_usage(resp.usage)
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def _log_usage(u) -> None:
    """Log cache activity so we can confirm prompt caching is working
    (cache_read_input_tokens > 0 on the 2nd+ call within the window)."""
    print(f"[llm] {MODEL} in={u.input_tokens} "
          f"cache_write={getattr(u, 'cache_creation_input_tokens', 0)} "
          f"cache_read={getattr(u, 'cache_read_input_tokens', 0)} "
          f"out={u.output_tokens}")
