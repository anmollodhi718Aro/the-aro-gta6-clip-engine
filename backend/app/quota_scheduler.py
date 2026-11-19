"""SQLite-backed quota-aware scheduler for bounded public chat polling.

This scheduler allocates request budget; it does not perform network calls.
Request costs are configurable because API quota tables can change.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class ScheduledSource:
    source_id: str
    interval_seconds: int
    request_cost_units: int
    priority: int
    next_due_at: datetime


@dataclass(frozen=True)
class ScheduledPoll:
    source_id: str
    reserved_units: int
    quota_used_today: int
    quota_remaining_today: int
    next_due_at: datetime


class QuotaAwareScheduler:
    """Fair, bounded scheduler with a daily UTC quota ledger.

    One claim reserves one request. Callers should claim only immediately
    before making that request. Failed requests still consume the reservation
    conservatively; there is deliberately no automatic refund.
    """

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.database_path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    def _initialize(self):
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_sources (
                    source_id TEXT PRIMARY KEY,
                    interval_seconds INTEGER NOT NULL CHECK(interval_seconds >= 1),
                    request_cost_units INTEGER NOT NULL CHECK(request_cost_units >= 1),
                    priority INTEGER NOT NULL DEFAULT 0,
                    enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
                    next_due_at TEXT NOT NULL,
                    last_claimed_at TEXT
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS quota_reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    utc_day TEXT NOT NULL,
                    units INTEGER NOT NULL CHECK(units > 0),
                    reserved_at TEXT NOT NULL
                )
            """)
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_quota_day ON quota_reservations(utc_day)"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_sources_due ON scheduled_sources(enabled, next_due_at, priority)"
            )

    @staticmethod
    def _now(value: datetime | None) -> datetime:
        current = value or datetime.now(timezone.utc)
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("scheduler timestamps must be timezone-aware")
        return current.astimezone(timezone.utc)

    def configure_source(self, source_id: str, *, interval_seconds: int,
                         request_cost_units: int, priority: int = 0,
                         enabled: bool = True, now: datetime | None = None) -> None:
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id is required")
        if interval_seconds < 1 or request_cost_units < 1:
            raise ValueError("interval and request cost must be positive")
        current = self._now(now)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT next_due_at FROM scheduled_sources WHERE source_id=?",
                (source_id,),
            ).fetchone()
            due = existing["next_due_at"] if existing else current.isoformat()
            db.execute("""
                INSERT INTO scheduled_sources
                    (source_id, interval_seconds, request_cost_units, priority, enabled, next_due_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    interval_seconds=excluded.interval_seconds,
                    request_cost_units=excluded.request_cost_units,
                    priority=excluded.priority,
                    enabled=excluded.enabled
            """, (source_id, interval_seconds, request_cost_units, priority,
                  int(enabled), due))
            db.commit()

    def set_enabled(self, source_id: str, enabled: bool) -> bool:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cursor = db.execute(
                "UPDATE scheduled_sources SET enabled=? WHERE source_id=?",
                (int(enabled), source_id),
            )
            db.commit()
            return cursor.rowcount > 0

    def claim_next(self, *, daily_quota_units: int,
                   now: datetime | None = None) -> ScheduledPoll | None:
        if daily_quota_units < 1:
            raise ValueError("daily_quota_units must be positive")
        current = self._now(now)
        day = current.date().isoformat()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            used = db.execute(
                "SELECT COALESCE(SUM(units),0) AS total FROM quota_reservations WHERE utc_day=?",
                (day,),
            ).fetchone()["total"]
            row = db.execute("""
                SELECT * FROM scheduled_sources
                WHERE enabled=1 AND next_due_at <= ?
                ORDER BY priority DESC, next_due_at ASC, source_id ASC
                LIMIT 1
            """, (current.isoformat(),)).fetchone()
            if row is None or used + row["request_cost_units"] > daily_quota_units:
                db.commit()
                return None
            next_due = current + timedelta(seconds=row["interval_seconds"])
            db.execute("""
                UPDATE scheduled_sources
                SET next_due_at=?, last_claimed_at=?
                WHERE source_id=?
            """, (next_due.isoformat(), current.isoformat(), row["source_id"]))
            db.execute("""
                INSERT INTO quota_reservations(source_id, utc_day, units, reserved_at)
                VALUES (?, ?, ?, ?)
            """, (row["source_id"], day, row["request_cost_units"], current.isoformat()))
            db.commit()
            new_used = used + row["request_cost_units"]
            return ScheduledPoll(row["source_id"], row["request_cost_units"],
                                 new_used, daily_quota_units - new_used, next_due)

    def quota_used(self, *, now: datetime | None = None) -> int:
        day = self._now(now).date().isoformat()
        with self._connect() as db:
            row = db.execute(
                "SELECT COALESCE(SUM(units),0) AS total FROM quota_reservations WHERE utc_day=?",
                (day,),
            ).fetchone()
        return int(row["total"])

    def list_sources(self) -> list[ScheduledSource]:
        with self._connect() as db:
            rows = db.execute("""
                SELECT source_id, interval_seconds, request_cost_units, priority, next_due_at
                FROM scheduled_sources ORDER BY priority DESC, source_id ASC
            """).fetchall()
        return [ScheduledSource(
            row["source_id"], row["interval_seconds"], row["request_cost_units"],
            row["priority"], datetime.fromisoformat(row["next_due_at"])
        ) for row in rows]
