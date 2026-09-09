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

MODEL = os.environ.get("TRADE101_MODEL", "claude-opus-5")


class MissingKeyError(RuntimeError):
    pass


def call(key_env: str, system: str, user: str, effort: str = "high", max_tokens: int = 4000) -> str:
    """Call Claude with the key named by `key_env`. Returns the text response."""
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
        system=system,
        messages=[{"role": "user", "content": user}],
        **kwargs,
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("The model declined this request.")
    return "".join(b.text for b in resp.content if b.type == "text").strip()
