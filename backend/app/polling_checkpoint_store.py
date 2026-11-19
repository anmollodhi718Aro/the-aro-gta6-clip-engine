"""Durable SQLite checkpoints for bounded YouTube chat polling."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class PollingCheckpoint:
    video_id: str
    live_chat_id: str | None
    page_token: str | None
    updated_at: str


class PollingCheckpointStore:
    """Persist the last successfully handled page cursor per video.

    Save only after the caller's batch callback has completed. This is
    at-least-once processing: a crash between callback completion and
    checkpoint commit can replay a batch, so callbacks must be idempotent.
    """

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS youtube_poll_checkpoints (
                    video_id TEXT PRIMARY KEY,
                    live_chat_id TEXT,
                    page_token TEXT,
                    updated_at TEXT NOT NULL
                )
            """)

    @staticmethod
    def _validate_video_id(video_id: str) -> None:
        if not isinstance(video_id, str) or not video_id.strip():
            raise ValueError("video_id is required")

    def load(self, video_id: str) -> PollingCheckpoint | None:
        self._validate_video_id(video_id)
        with self._connect() as db:
            row = db.execute(
                "SELECT video_id, live_chat_id, page_token, updated_at "
                "FROM youtube_poll_checkpoints WHERE video_id = ?",
                (video_id,),
            ).fetchone()
        if row is None:
            return None
        return PollingCheckpoint(row["video_id"], row["live_chat_id"],
                                 row["page_token"], row["updated_at"])

    def save(self, video_id: str, *, live_chat_id: str | None,
             page_token: str | None) -> PollingCheckpoint:
        self._validate_video_id(video_id)
        if live_chat_id is not None and (not isinstance(live_chat_id, str) or not live_chat_id.strip()):
            raise ValueError("live_chat_id must be a non-empty string or None")
        if page_token is not None and (not isinstance(page_token, str) or not page_token.strip()):
            raise ValueError("page_token must be a non-empty string or None")
        updated_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.execute("""
                INSERT INTO youtube_poll_checkpoints
                    (video_id, live_chat_id, page_token, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    live_chat_id=excluded.live_chat_id,
                    page_token=excluded.page_token,
                    updated_at=excluded.updated_at
            """, (video_id, live_chat_id, page_token, updated_at))
        return PollingCheckpoint(video_id, live_chat_id, page_token, updated_at)

    def clear(self, video_id: str) -> bool:
        self._validate_video_id(video_id)
        with self._connect() as db:
            cursor = db.execute(
                "DELETE FROM youtube_poll_checkpoints WHERE video_id = ?",
                (video_id,),
            )
            return cursor.rowcount > 0
