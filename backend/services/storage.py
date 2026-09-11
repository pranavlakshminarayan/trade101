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


# ---- learning journal ------------------------------------------------------
#
# The learner's own reasoning, saved. Deliberately NOT a virtual trade: the
# record is "here is what I thought and why", so revisiting it teaches whether
# the REASONING held up — which is the transferable skill — rather than whether
# a hypothetical position made money.

JOURNAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS journal (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker      TEXT NOT NULL,
    created_at  TEXT NOT NULL,     -- UTC ISO-8601
    as_of       TEXT,              -- the data timestamp the note describes
    timeframe   TEXT,
    kind        TEXT NOT NULL,     -- 'study' | 'replay' | 'note'
    lean        TEXT,              -- the learner's own read
    confidence  TEXT,
    hypothesis  TEXT NOT NULL,     -- what they think is happening, and why
    evidence    TEXT,              -- JSON list of the evidence they leaned on
    ai_lean     TEXT,              -- what the AI said, recorded AFTER they committed
    outcome     TEXT,              -- JSON, for replay entries: what actually followed
    reflection  TEXT               -- written on revisit
);
CREATE INDEX IF NOT EXISTS idx_journal_ticker  ON journal (ticker);
CREATE INDEX IF NOT EXISTS idx_journal_created ON journal (created_at DESC);
"""


def _ensure_journal(conn) -> None:
    conn.executescript(JOURNAL_SCHEMA)


def add_journal_entry(entry: dict) -> dict | None:
    """Save one learning-journal entry. Returns the stored row, or None if the
    database is unavailable."""
    import json
    from datetime import datetime, timezone

    row = {
        "ticker": (entry.get("ticker") or "").upper(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": entry.get("asOf"),
        "timeframe": entry.get("timeframe"),
        "kind": entry.get("kind") or "note",
        "lean": entry.get("lean"),
        "confidence": entry.get("confidence"),
        "hypothesis": entry.get("hypothesis") or "",
        "evidence": json.dumps(entry.get("evidence") or []),
        "ai_lean": entry.get("aiLean"),
        "outcome": json.dumps(entry["outcome"]) if entry.get("outcome") is not None else None,
        "reflection": entry.get("reflection"),
    }
    with connect() as conn:
        if conn is None:
            return None
        _ensure_journal(conn)
        cur = conn.execute(
            """INSERT INTO journal (ticker, created_at, as_of, timeframe, kind, lean,
                   confidence, hypothesis, evidence, ai_lean, outcome, reflection)
               VALUES (:ticker, :created_at, :as_of, :timeframe, :kind, :lean,
                   :confidence, :hypothesis, :evidence, :ai_lean, :outcome, :reflection)""",
            row,
        )
        return {"id": cur.lastrowid, **row}


def get_journal(ticker: str | None = None, limit: int = 100) -> list[dict]:
    """Journal entries, newest first; optionally for one ticker."""
    import json
    with connect() as conn:
        if conn is None:
            return []
        _ensure_journal(conn)
        if ticker:
            rows = conn.execute(
                "SELECT * FROM journal WHERE ticker = ? ORDER BY created_at DESC LIMIT ?",
                (ticker.upper(), limit)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM journal ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()

        out = []
        for r in rows:
            d = dict(r)
            for field in ("evidence", "outcome"):
                if d.get(field):
                    try:
                        d[field] = json.loads(d[field])
                    except (ValueError, TypeError):
                        pass
            out.append(d)
        return out


def update_journal_reflection(entry_id: int, reflection: str) -> bool:
    """Attach a revisit reflection to an existing entry."""
    with connect() as conn:
        if conn is None:
            return False
        _ensure_journal(conn)
        cur = conn.execute("UPDATE journal SET reflection = ? WHERE id = ?",
                           (reflection, entry_id))
        return (cur.rowcount or 0) > 0


def delete_journal_entry(entry_id: int) -> bool:
    with connect() as conn:
        if conn is None:
            return False
        _ensure_journal(conn)
        cur = conn.execute("DELETE FROM journal WHERE id = ?", (entry_id,))
        return (cur.rowcount or 0) > 0
