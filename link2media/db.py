"""SQLite database management for user preferences."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Optional

from .i18n import DEFAULT_LANG, SUPPORTED_LANGS

SCHEMA = """
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY,
    language TEXT NOT NULL DEFAULT 'km',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_user_preferences_lang ON user_preferences(language);
"""


def _get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db_sync(db_path: Path) -> None:
    """Initialize database tables synchronously."""
    with _get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


async def init_db(db_path: Path) -> None:
    """Initialize database tables asynchronously."""
    await asyncio.to_thread(init_db_sync, db_path)


def get_user_language_sync(db_path: Path, user_id: int) -> str:
    """Get language code for user, defaulting to DEFAULT_LANG."""
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT language FROM user_preferences WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row and row[0] in SUPPORTED_LANGS:
            return str(row[0])
        return DEFAULT_LANG


async def get_user_language(db_path: Path, user_id: int) -> str:
    """Asynchronously retrieve user's language preference."""
    return await asyncio.to_thread(get_user_language_sync, db_path, user_id)


def set_user_language_sync(db_path: Path, user_id: int, language: str) -> None:
    """Save user's language preference."""
    lang = language if language in SUPPORTED_LANGS else DEFAULT_LANG
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO user_preferences (user_id, language, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                language = excluded.language,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, lang),
        )


async def set_user_language(db_path: Path, user_id: int, language: str) -> None:
    """Asynchronously save user's language preference."""
    await asyncio.to_thread(set_user_language_sync, db_path, user_id, language)
