from __future__ import annotations

import hashlib
import io
import os
import sqlite3

import pandas as pd

_DEFAULT_DB = "cache.sqlite"


def _db_path() -> str:
    return os.environ.get("CACHE_DB_PATH", _DEFAULT_DB)


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS response_cache (
            question_hash TEXT PRIMARY KEY,
            question       TEXT NOT NULL,
            sql            TEXT NOT NULL,
            result_json    TEXT NOT NULL,
            summary        TEXT NOT NULL,
            created_at     TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def _question_hash(question: str) -> str:
    return hashlib.sha256(question.strip().lower().encode()).hexdigest()


def get_cached(question: str) -> tuple[str, pd.DataFrame, str] | None:
    """Return (sql, df, summary) if the question is cached, else None."""
    conn = sqlite3.connect(_db_path())
    try:
        _init_db(conn)
        row = conn.execute(
            "SELECT sql, result_json, summary FROM response_cache"
            " WHERE question_hash = ?",
            (_question_hash(question),),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    sql, result_json, summary = row
    df: pd.DataFrame = pd.read_json(io.StringIO(result_json), orient="split")
    return sql, df, summary


def save_to_cache(
    question: str,
    sql: str,
    df: pd.DataFrame,
    summary: str,
) -> None:
    """Persist a question -> (sql, df, summary) mapping to the SQLite cache."""
    conn = sqlite3.connect(_db_path())
    try:
        _init_db(conn)
        conn.execute(
            """
            INSERT OR REPLACE INTO response_cache
                (question_hash, question, sql, result_json, summary)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                _question_hash(question),
                question,
                sql,
                df.to_json(orient="split"),
                summary,
            ),
        )
        conn.commit()
    finally:
        conn.close()
