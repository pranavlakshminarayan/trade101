"""
Thin wrapper around the Claude API for Trade101's agents.

Calls are made by PURPOSE (the part of the app doing the spending), not by key.
Each purpose has its own named key env var; when that key is unset it falls back
to the shared analysis key, and the ledger records whichever key actually paid.
So you can run one key or several — the per-purpose spend breakdown holds either
way (see services/usage.py), and splitting keys later changes nothing but which
key_env shows up in the ledger.

Missing key → MissingKeyError, so the endpoint degrades gracefully: the
deterministic chart + indicators still render without any AI.
"""
from __future__ import annotations

import os

import anthropic

from services import usage

# Default to Sonnet 5 (cheaper than Opus, strong reasoning). Override with
# TRADE101_MODEL in .env (e.g. claude-opus-5 for max depth, claude-haiku-4-5 for cheapest).
MODEL = os.environ.get("TRADE101_MODEL", "claude-sonnet-5")

# Each purpose's own key, for per-key attribution in the Anthropic Console.
PURPOSE_KEYS = {
    "analysis": "TRADE101_ANALYSIS_KEY",
    "research": "TRADE101_RESEARCH_KEY",
    "ecosystem": "TRADE101_ECOSYSTEM_KEY",
    "orchestrator": "TRADE101_ORCHESTRATOR_KEY",
}
# The key every purpose falls back to — one key is a perfectly good setup.
FALLBACK_KEY_ENV = "TRADE101_ANALYSIS_KEY"


class MissingKeyError(RuntimeError):
    pass


def resolve_key(purpose: str) -> tuple[str, str]:
    """(api_key, key_env_actually_used) for `purpose`. Raises MissingKeyError."""
    preferred = PURPOSE_KEYS.get(purpose, FALLBACK_KEY_ENV)
    for key_env in (preferred, FALLBACK_KEY_ENV):
        key = os.environ.get(key_env)
        if key:
            return key, key_env
    raise MissingKeyError(
        f"AI narration unavailable — set {preferred} (or {FALLBACK_KEY_ENV}) in your "
        f".env as a named Claude API key. The chart and indicators work without it."
    )


def call(purpose: str, system: str, user: str, ticker: str | None = None,
         effort: str = "high", max_tokens: int = 4000) -> str:
    """Call Claude for `purpose`, log the spend, and return the text response."""
    key, key_env = resolve_key(purpose)
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
    # Record spend before inspecting the outcome: a refusal still costs tokens.
    usage.record(purpose, key_env, MODEL, getattr(resp, "usage", None), ticker)

    if resp.stop_reason == "refusal":
        raise RuntimeError("The model declined this request.")
    return "".join(b.text for b in resp.content if b.type == "text").strip()
