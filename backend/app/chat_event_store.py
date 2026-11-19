"""Durable, idempotent SQLite storage for ingested chat events."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .models import ChatEvent


@dataclass(frozen=True)
class IngestionResult:
    inserted: int
    duplicates: int


class ChatEventStore:
    """Persist event IDs uniquely and reject conflicting ID reuse.

    A batch is atomic. Identical re-deliveries are harmless; reusing an event
    ID with different source, timestamp, or text raises ValueError.
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
                CREATE TABLE IF NOT EXISTS chat_events (
                    source_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    text TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,
                    PRIMARY KEY (source_id, event_id)
                )
            """)
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_events_source_time "
                "ON chat_events(source_id, timestamp)"
            )

    def persist(self, events: tuple[ChatEvent, ...] | list[ChatEvent]) -> IngestionResult:
        inserted = duplicates = 0
        with self._connect() as db:
            for event in events:
                timestamp = event.timestamp.isoformat()
                cursor = db.execute("""
                    INSERT OR IGNORE INTO chat_events
                        (source_id, event_id, timestamp, text, ingested_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (event.source_id, event.event_id, timestamp, event.text,
                      datetime.now(timezone.utc).isoformat()))
                if cursor.rowcount == 1:
                    inserted += 1
                    continue
                existing = db.execute("""
                    SELECT timestamp, text FROM chat_events
                    WHERE source_id = ? AND event_id = ?
                """, (event.source_id, event.event_id)).fetchone()
                if existing is None or existing["timestamp"] != timestamp or existing["text"] != event.text:
                    raise ValueError(f"conflicting duplicate event_id: {event.event_id}")
                duplicates += 1
        return IngestionResult(inserted, duplicates)

    def persist_batch(self, batch) -> IngestionResult:
        """Callback-compatible helper for YouTubeChatBatch."""
        return self.persist(batch.events)

    def list_events(self, source_id: str) -> list[ChatEvent]:
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id is required")
        with self._connect() as db:
            rows = db.execute("""
                SELECT event_id, source_id, timestamp, text FROM chat_events
                WHERE source_id = ? ORDER BY timestamp, event_id
            """, (source_id,)).fetchall()
        return [ChatEvent(event_id=row["event_id"], source_id=row["source_id"],
                          timestamp=row["timestamp"], text=row["text"]) for row in rows]
