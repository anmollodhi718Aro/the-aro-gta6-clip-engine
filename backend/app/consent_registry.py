"""SQLite-backed creator consent registry with durable revocation audit events.

The registry stores permission metadata only. It does not verify a creator's
identity or prove that consent is legally sufficient; the operator must retain
the underlying authorization evidence separately.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .models import PermissionRecord, parse_datetime


class ConsentRegistry:
    """Persist one current permission record per source and an append-only audit."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS consent_permissions (
                    source_id TEXT PRIMARY KEY,
                    granted_by TEXT NOT NULL,
                    scopes_json TEXT NOT NULL,
                    granted_at TEXT NOT NULL,
                    expires_at TEXT,
                    revoked_at TEXT
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS consent_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    action TEXT NOT NULL CHECK(action IN ('granted', 'revoked')),
                    occurred_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )
            """)
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_consent_audit_source "
                "ON consent_audit(source_id, id)"
            )

    @staticmethod
    def _serialize(permission: PermissionRecord) -> tuple:
        return (
            permission.source_id,
            permission.granted_by,
            json.dumps(sorted(permission.scopes), separators=(",", ":")),
            permission.granted_at.isoformat(),
            permission.expires_at.isoformat() if permission.expires_at else None,
            permission.revoked_at.isoformat() if permission.revoked_at else None,
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> PermissionRecord:
        return PermissionRecord(
            source_id=row["source_id"],
            granted_by=row["granted_by"],
            scopes=frozenset(json.loads(row["scopes_json"])),
            granted_at=parse_datetime(row["granted_at"]),
            expires_at=parse_datetime(row["expires_at"]) if row["expires_at"] else None,
            revoked_at=parse_datetime(row["revoked_at"]) if row["revoked_at"] else None,
        )

    def grant(self, permission: PermissionRecord, *, actor: str = "operator") -> None:
        """Record or renew a source grant and append an audit event."""
        if not actor.strip():
            raise ValueError("actor is required")
        with self._connect() as db:
            db.execute(
                """INSERT INTO consent_permissions
                   (source_id, granted_by, scopes_json, granted_at, expires_at, revoked_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(source_id) DO UPDATE SET
                     granted_by=excluded.granted_by,
                     scopes_json=excluded.scopes_json,
                     granted_at=excluded.granted_at,
                     expires_at=excluded.expires_at,
                     revoked_at=excluded.revoked_at""",
                self._serialize(permission),
            )
            db.execute(
                """INSERT INTO consent_audit
                   (source_id, action, occurred_at, actor, details_json)
                   VALUES (?, 'granted', ?, ?, ?)""",
                (
                    permission.source_id,
                    datetime.now(timezone.utc).isoformat(),
                    actor,
                    json.dumps({"granted_by": permission.granted_by,
                                "scopes": sorted(permission.scopes),
                                "expires_at": permission.expires_at.isoformat()
                                if permission.expires_at else None},
                               separators=(",", ":")),
                ),
            )

    def get(self, source_id: str) -> PermissionRecord | None:
        if not source_id.strip():
            raise ValueError("source_id is required")
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM consent_permissions WHERE source_id = ?",
                (source_id,),
            ).fetchone()
        return self._from_row(row) if row else None

    def require(self, source_id: str, scope: str, *, at: datetime | None = None) -> PermissionRecord:
        """Return a valid grant or fail closed."""
        permission = self.get(source_id)
        check_time = parse_datetime(at or datetime.now(timezone.utc))
        if permission is None or not permission.allows(scope, check_time):
            raise PermissionError(f"valid {scope} permission is required for source {source_id}")
        return permission

    def revoke(
        self,
        source_id: str,
        *,
        actor: str,
        at: datetime | None = None,
    ) -> bool:
        """Revoke an existing grant. Repeated revocation is a no-op."""
        if not source_id.strip() or not actor.strip():
            raise ValueError("source_id and actor are required")
        revoked_at = parse_datetime(at or datetime.now(timezone.utc))
        with self._connect() as db:
            row = db.execute(
                "SELECT revoked_at FROM consent_permissions WHERE source_id = ?",
                (source_id,),
            ).fetchone()
            if row is None or row["revoked_at"] is not None:
                return False
            db.execute(
                "UPDATE consent_permissions SET revoked_at = ? WHERE source_id = ?",
                (revoked_at.isoformat(), source_id),
            )
            db.execute(
                """INSERT INTO consent_audit
                   (source_id, action, occurred_at, actor, details_json)
                   VALUES (?, 'revoked', ?, ?, '{}')""",
                (source_id, revoked_at.isoformat(), actor),
            )
        return True

    def audit_events(self, source_id: str) -> list[dict[str, str]]:
        if not source_id.strip():
            raise ValueError("source_id is required")
        with self._connect() as db:
            rows = db.execute(
                """SELECT action, occurred_at, actor, details_json
                   FROM consent_audit WHERE source_id = ? ORDER BY id""",
                (source_id,),
            ).fetchall()
        return [
            {"action": row["action"], "occurred_at": row["occurred_at"],
             "actor": row["actor"], "details": row["details_json"]}
            for row in rows
        ]
