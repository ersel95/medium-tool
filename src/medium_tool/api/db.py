"""SQLite database for article history."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path.home() / ".medium-tool" / "history.db"

_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
    return _conn


def init_db() -> None:
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '',
            subtitle TEXT NOT NULL DEFAULT '',
            markdown TEXT NOT NULL DEFAULT '',
            tags TEXT NOT NULL DEFAULT '[]',
            image_prompts TEXT NOT NULL DEFAULT '[]',
            project_name TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()


def save_article(
    title: str,
    subtitle: str,
    markdown: str,
    tags: list[str],
    image_prompts: list[dict[str, str]],
    project_name: str = "",
) -> str:
    conn = _get_conn()
    article_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO articles (id, title, subtitle, markdown, tags, image_prompts, project_name, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            article_id,
            title,
            subtitle,
            markdown,
            json.dumps(tags),
            json.dumps(image_prompts),
            project_name,
            now,
            now,
        ),
    )
    conn.commit()
    return article_id


def list_articles() -> list[dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, project_name, created_at, updated_at FROM articles ORDER BY updated_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_article(article_id: str) -> dict[str, Any] | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    if row is None:
        return None
    data = dict(row)
    data["tags"] = json.loads(data["tags"])
    data["image_prompts"] = json.loads(data["image_prompts"])
    return data


def update_article(article_id: str, **fields: Any) -> bool:
    conn = _get_conn()
    allowed = {"title", "subtitle", "markdown", "tags", "image_prompts", "project_name"}
    updates: list[str] = []
    values: list[Any] = []
    for key, val in fields.items():
        if key not in allowed:
            continue
        if key in ("tags", "image_prompts"):
            val = json.dumps(val)
        updates.append(f"{key} = ?")
        values.append(val)
    if not updates:
        return False
    updates.append("updated_at = ?")
    values.append(datetime.now(timezone.utc).isoformat())
    values.append(article_id)
    result = conn.execute(
        f"UPDATE articles SET {', '.join(updates)} WHERE id = ?", values
    )
    conn.commit()
    return result.rowcount > 0


def delete_article(article_id: str) -> bool:
    conn = _get_conn()
    result = conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    conn.commit()
    return result.rowcount > 0
