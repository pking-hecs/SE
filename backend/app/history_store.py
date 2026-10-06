"""Small SQLite store for interview conversations.

This is intentionally independent of the platform's optional PostgreSQL stack so
chat history also works in the local development setup.
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "chat_history.db"


def _connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize() -> None:
    with _connect() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)


def create_conversation(conversation_id: str, title: str, project_id: int) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as db:
        db.execute(
            "INSERT OR IGNORE INTO conversations(id, title, project_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, title, project_id, now, now),
        )
    return get_conversation(conversation_id)


def add_message(conversation_id: str, role: str, text: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as db:
        db.execute(
            "INSERT INTO conversation_messages(conversation_id, role, text, created_at) VALUES (?, ?, ?, ?)",
            (conversation_id, role, text, now),
        )
        db.execute("UPDATE conversations SET updated_at=? WHERE id=?", (now, conversation_id))


def list_conversations() -> list[dict]:
    with _connect() as db:
        rows = db.execute("""
            SELECT c.id, c.title, c.project_id, c.created_at, c.updated_at, COUNT(m.id) AS message_count
            FROM conversations c LEFT JOIN conversation_messages m ON m.conversation_id = c.id
            GROUP BY c.id ORDER BY c.updated_at DESC
        """).fetchall()
    return [dict(row) for row in rows]


def get_conversation(conversation_id: str) -> dict | None:
    with _connect() as db:
        row = db.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["messages"] = [dict(item) for item in db.execute(
            "SELECT role, text, created_at FROM conversation_messages WHERE conversation_id=? ORDER BY id",
            (conversation_id,),
        ).fetchall()]
    return data


def delete_conversation(conversation_id: str) -> bool:
    with _connect() as db:
        return db.execute("DELETE FROM conversations WHERE id=?", (conversation_id,)).rowcount > 0
