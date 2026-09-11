"""
Local persistence — SQLite. Deterministic, no LLM.

Two jobs, one small database:
- `llm_usage`  — the per-call spend ledger (see services/usage.py).
- `history`    — researched stocks + their AI takeaway, server-side so a
                 search survives a cleared browser cache (the frontend's
                 localStorage copy stays as the fast path).

Everything degrades: if the database cannot be opened or written, callers get
an empty result / a silent no-op rather than a failed request. Persistence is a
convenience here, never a dependency of the research path.
"""
from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

# Default location: <project root>/data/trade101.db. `data/` is git-ignored.
DEFAULT_DB = Path(__file__).resolve().parent.parent.parent / "data" / "trade101.db"

_lock = threading.Lock()
_initialised = False

SCHEMA = """
CREATE TABLE IF NOT EXISTS llm_usage (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                  TEXT    NOT NULL,   -- UTC ISO-8601
    purpose             TEXT    NOT NULL,   -- which part of the app spent this
    key_env             TEXT    NOT NULL,   -- which named key paid for it
    model               TEXT    NOT NULL,
    ticker              TEXT,
    input_tokens        INTEGER NOT NULL DEFAULT 0,
    output_tokens       INTEGER NOT NULL DEFAULT 0,
    cache_write_tokens  INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens   INTEGER NOT NULL DEFAULT 0,
    cost_usd            REAL    NOT NULL DEFAULT 0.0,
    priced              INTEGER NOT NULL DEFAULT 1  -- 0 = model not in price table
);
CREATE INDEX IF NOT EXISTS idx_usage_ts      ON llm_usage (ts);
CREATE INDEX IF NOT EXISTS idx_usage_purpose ON llm_usage (purpose);

CREATE TABLE IF NOT EXISTS history (
    ticker      TEXT PRIMARY KEY,
    name        TEXT,
    lean        TEXT,
    summary     TEXT,
    as_of       TEXT,          -- the data timestamp the takeaway describes
    last_viewed TEXT NOT NULL  -- UTC ISO-8601
);
CREATE INDEX IF NOT EXISTS idx_history_viewed ON history (last_viewed DESC);
"""


def db_path() -> Path:
    """Where the database lives — override with TRADE101_DB (':memory:' in tests)."""
    env = os.environ.get("TRADE101_DB")
    return Path(env) if env else DEFAULT_DB


@contextmanager
def connect():
    """Yield a connection, or None if the database is unusable.

    Callers MUST handle None — a broken database must never break research.
    """
    global _initialised
    conn = None
    try:
        path = db_path()
        if str(path) != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), timeout=5)
        conn.row_factory = sqlite3.Row
        with _lock:
            if not _initialised or str(path) == ":memory:":
                conn.execute("PRAGMA journal_mode=WAL")
                conn.executescript(SCHEMA)
                conn.commit()
                _initialised = True
        yield conn
        conn.commit()
    except Exception:
        yield None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def reset_for_tests() -> None:
    """Force schema re-creation on the next connect (used when TRADE101_DB changes)."""
    global _initialised
    with _lock:
        _initialised = False


# ---- history ---------------------------------------------------------------

def save_history(ticker: str, name: str | None, lean: str | None,
                 summary: str | None, as_of: str | None = None) -> None:
    """Upsert one researched stock. Silent no-op if the database is unavailable."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with connect() as conn:
        if conn is None:
            return
        conn.execute(
            """INSERT INTO history (ticker, name, lean, summary, as_of, last_viewed)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(ticker) DO UPDATE SET
                 name=excluded.name, lean=excluded.lean, summary=excluded.summary,
                 as_of=excluded.as_of, last_viewed=excluded.last_viewed""",
            (ticker.upper(), name, lean, summary, as_of, now),
        )


def get_history(limit: int = 50) -> list[dict]:
    """Most-recently-researched first. Empty list if the database is unavailable."""
    with connect() as conn:
        if conn is None:
            return []
        rows = conn.execute(
            "SELECT * FROM history ORDER BY last_viewed DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def clear_history() -> int:
    """Delete all saved history; returns the number of rows removed."""
    with connect() as conn:
        if conn is None:
            return 0
        cur = conn.execute("DELETE FROM history")
        return cur.rowcount or 0
