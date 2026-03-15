from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id() -> str:
    return uuid.uuid4().hex[:12]


SCHEMA = """
CREATE TABLE IF NOT EXISTS submissions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_url TEXT,
    source_id TEXT,
    source_instance TEXT,
    author_name TEXT,
    author_handle TEXT,
    author_avatar_url TEXT,
    description TEXT,
    submitter_name TEXT,
    submitter_email TEXT,
    created_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    moderated_at TEXT,
    moderated_by TEXT,
    UNIQUE(source_id, source_instance)
);

CREATE TABLE IF NOT EXISTS photos (
    id TEXT PRIMARY KEY,
    submission_id TEXT NOT NULL REFERENCES submissions(id),
    original_url TEXT,
    local_path TEXT,
    thumbnail_path TEXT,
    alt_text TEXT,
    width INTEGER,
    height INTEGER,
    original_size INTEGER,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS poller_state (
    instance TEXT PRIMARY KEY,
    last_seen_id TEXT,
    last_polled_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_source ON submissions(source);
CREATE INDEX IF NOT EXISTS idx_photos_submission ON photos(submission_id);
"""


def get_db_path() -> str:
    return settings.database_path


def init_db(db_path: str | None = None) -> None:
    path = db_path or get_db_path()
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_connection(db_path: str | None = None):
    path = db_path or get_db_path()
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# --- Submissions ---


def create_submission(
    source: str,
    created_at: str | None = None,
    source_url: str | None = None,
    source_id: str | None = None,
    source_instance: str | None = None,
    author_name: str | None = None,
    author_handle: str | None = None,
    author_avatar_url: str | None = None,
    description: str | None = None,
    submitter_name: str | None = None,
    submitter_email: str | None = None,
    db_path: str | None = None,
) -> str:
    sid = _generate_id()
    now = _now()
    with get_connection(db_path) as conn:
        conn.execute(
            """INSERT INTO submissions
               (id, source, source_url, source_id, source_instance,
                author_name, author_handle, author_avatar_url,
                description, submitter_name, submitter_email,
                created_at, fetched_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
            (
                sid, source, source_url, source_id, source_instance,
                author_name, author_handle, author_avatar_url,
                description, submitter_name, submitter_email,
                created_at or now, now,
            ),
        )
    return sid


def get_submission(submission_id: str, db_path: str | None = None) -> dict | None:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM submissions WHERE id = ?", (submission_id,)
        ).fetchone()
        return dict(row) if row else None


def list_submissions(
    status: str | None = None,
    source: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db_path: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM submissions WHERE 1=1"
    params: list[Any] = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if source:
        query += " AND source = ?"
        params.append(source)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def moderate_submission(
    submission_id: str,
    status: str,
    moderated_by: str = "admin",
    db_path: str | None = None,
) -> bool:
    now = _now()
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """UPDATE submissions
               SET status = ?, moderated_at = ?, moderated_by = ?
               WHERE id = ?""",
            (status, now, moderated_by, submission_id),
        )
        return cursor.rowcount > 0


def count_submissions(db_path: str | None = None) -> dict[str, int]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM submissions GROUP BY status"
        ).fetchall()
        counts = {r["status"]: r["cnt"] for r in rows}
        counts["total"] = sum(counts.values())
        return counts


def submission_exists_by_source(
    source_id: str, source_instance: str, db_path: str | None = None
) -> bool:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM submissions WHERE source_id = ? AND source_instance = ?",
            (source_id, source_instance),
        ).fetchone()
        return row is not None


# --- Photos ---


def add_photo(
    submission_id: str,
    original_url: str | None = None,
    local_path: str | None = None,
    thumbnail_path: str | None = None,
    alt_text: str | None = None,
    width: int | None = None,
    height: int | None = None,
    original_size: int | None = None,
    sort_order: int = 0,
    db_path: str | None = None,
) -> str:
    pid = _generate_id()
    with get_connection(db_path) as conn:
        conn.execute(
            """INSERT INTO photos
               (id, submission_id, original_url, local_path, thumbnail_path,
                alt_text, width, height, original_size, sort_order)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                pid, submission_id, original_url, local_path, thumbnail_path,
                alt_text, width, height, original_size, sort_order,
            ),
        )
    return pid


def get_photos_for_submission(
    submission_id: str, db_path: str | None = None
) -> list[dict]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM photos WHERE submission_id = ? ORDER BY sort_order",
            (submission_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def list_approved_photos(
    limit: int = 50, offset: int = 0, db_path: str | None = None
) -> list[dict]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """SELECT p.*, s.author_name, s.author_handle, s.source_url,
                      s.source, s.description, s.created_at as submission_date,
                      s.submitter_name
               FROM photos p
               JOIN submissions s ON p.submission_id = s.id
               WHERE s.status = 'approved'
               ORDER BY s.created_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]


def count_approved_photos(db_path: str | None = None) -> int:
    with get_connection(db_path) as conn:
        row = conn.execute(
            """SELECT COUNT(*) as cnt FROM photos p
               JOIN submissions s ON p.submission_id = s.id
               WHERE s.status = 'approved'"""
        ).fetchone()
        return row["cnt"]


# --- Poller state ---


def get_poller_state(instance: str, db_path: str | None = None) -> dict | None:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM poller_state WHERE instance = ?", (instance,)
        ).fetchone()
        return dict(row) if row else None


def update_poller_state(
    instance: str, last_seen_id: str, db_path: str | None = None
) -> None:
    now = _now()
    with get_connection(db_path) as conn:
        conn.execute(
            """INSERT INTO poller_state (instance, last_seen_id, last_polled_at)
               VALUES (?, ?, ?)
               ON CONFLICT(instance) DO UPDATE SET
                 last_seen_id = excluded.last_seen_id,
                 last_polled_at = excluded.last_polled_at""",
            (instance, last_seen_id, now),
        )
