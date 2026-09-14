"""
Secret redaction — keep API keys out of anything that can reach the client.

Provider errors (httpx especially) put the full request URL in their text, and
our request URLs carry `token=<key>`. Any string that might be shown to the user
or serialized into an API response must pass through `redact_secrets` first.
"""
from __future__ import annotations

import os
import re

# Query params that carry a credential in a URL: token=, apikey=, key=, api_key=.
_PARAM_RE = re.compile(r"(?i)\b(token|api[_-]?key|key|secret|access[_-]?token)=([^&\s\"']+)")

# Env vars whose *values* must never appear in client-facing text, even if they
# show up outside a URL query string.
_SECRET_ENV_VARS = (
    "TRADE101_NEWS_KEY",
    "TRADE101_ANALYSIS_KEY",
    "TRADE101_SEARCH_KEY",
    "TRADE101_MARKET_DATA_KEY",
)


def redact_secrets(text: str | None) -> str:
    """Return `text` with credential query-params and known key values masked."""
    if not text:
        return text or ""
    out = _PARAM_RE.sub(r"\1=<redacted>", text)
    for var in _SECRET_ENV_VARS:
        val = os.environ.get(var)
        if val and len(val) >= 6:
            out = out.replace(val, "<redacted>")
    return out
