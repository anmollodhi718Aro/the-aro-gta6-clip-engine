"""Scope-aware source permission registry for export-time rights checks.

This records operator-supplied permission evidence metadata; it does not
authenticate the grantor or determine whether permission is legally sufficient.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_USES = frozenset({"analyze", "edit", "publish"})


def _time(value: str | datetime) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must include a timezone")
    return parsed


class SourceRightsRegistry:
    """Persist source grants and fail closed when scope/platform is missing."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.database_path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS source_rights (
                    source_id TEXT PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    grantor TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL,
                    allowed_uses_json TEXT NOT NULL,
                    platforms_json TEXT NOT NULL,
                    attribution TEXT NOT NULL,
                    disclosure TEXT NOT NULL,
                    valid_from TEXT NOT NULL,
                    expires_at TEXT,
                    revoked_at TEXT
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS source_rights_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    details_json TEXT NOT NULL
                )
            """)

    def register(self, record: dict[str, Any], *, actor: str = "operator") -> None:
        required = ("source_id", "source_url", "grantor", "evidence_ref",
                    "allowed_uses", "platforms", "valid_from")
        missing = [key for key in required if not record.get(key)]
        if missing:
            raise ValueError("missing required rights fields: " + ", ".join(missing))
        if not actor.strip():
            raise ValueError("actor is required")
        uses = frozenset(str(x).strip().lower() for x in record["allowed_uses"])
        if not uses or not uses.issubset(ALLOWED_USES):
            raise ValueError("allowed_uses must contain only analyze, edit, publish")
        platforms = sorted({str(x).strip().lower() for x in record["platforms"] if str(x).strip()})
        if not platforms:
            raise ValueError("at least one permitted platform is required")
        source_url = str(record["source_url"]).strip()
        if not source_url.startswith(("https://", "http://")):
            raise ValueError("source_url must be an http(s) URL")
        values = (
            str(record["source_id"]).strip(), source_url, str(record["grantor"]).strip(),
            str(record["evidence_ref"]).strip(), json.dumps(sorted(uses)),
            json.dumps(platforms), str(record.get("attribution", "")).strip(),
            str(record.get("disclosure", "")).strip(), _time(record["valid_from"]).isoformat(),
            _time(record["expires_at"]).isoformat() if record.get("expires_at") else None,
            None,
        )
        if not all(values[:4]):
            raise ValueError("source_id, grantor, and evidence_ref must be non-empty")
        if values[9] and _time(values[9]) <= _time(values[8]):
            raise ValueError("expires_at must be later than valid_from")
        with self._connect() as db:
            db.execute("""
                INSERT INTO source_rights VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    source_url=excluded.source_url, grantor=excluded.grantor,
                    evidence_ref=excluded.evidence_ref, allowed_uses_json=excluded.allowed_uses_json,
                    platforms_json=excluded.platforms_json, attribution=excluded.attribution,
                    disclosure=excluded.disclosure, valid_from=excluded.valid_from,
                    expires_at=excluded.expires_at, revoked_at=NULL
            """, values)
            db.execute("""
                INSERT INTO source_rights_audit(source_id, action, actor, occurred_at, details_json)
                VALUES (?, 'registered', ?, ?, ?)
            """, (values[0], actor, datetime.now(timezone.utc).isoformat(),
                  json.dumps({"uses": sorted(uses), "platforms": platforms})))

    def authorize(self, source_id: str, use: str, platform: str,
                  *, at: datetime | None = None) -> dict[str, Any]:
        """Return the grant metadata or raise PermissionError; unknown is blocked."""
        if use not in ALLOWED_USES:
            raise ValueError(f"unsupported use: {use}")
        if not source_id.strip() or not platform.strip():
            raise ValueError("source_id and platform are required")
        with self._connect() as db:
            row = db.execute("SELECT * FROM source_rights WHERE source_id=?",
                             (source_id,)).fetchone()
        now = _time(at or datetime.now(timezone.utc))
        if row is None:
            raise PermissionError(f"no recorded rights for source {source_id}")
        if row["revoked_at"] and now >= _time(row["revoked_at"]):
            raise PermissionError(f"rights revoked for source {source_id}")
        if now < _time(row["valid_from"]):
            raise PermissionError(f"rights not yet valid for source {source_id}")
        if row["expires_at"] and now >= _time(row["expires_at"]):
            raise PermissionError(f"rights expired for source {source_id}")
        if use not in json.loads(row["allowed_uses_json"]):
            raise PermissionError(f"{use} is outside the recorded permission scope")
        if platform.lower() not in json.loads(row["platforms_json"]):
            raise PermissionError(f"{platform} is outside the permitted platforms")
        return {
            "source_id": row["source_id"], "source_url": row["source_url"],
            "grantor": row["grantor"], "evidence_ref": row["evidence_ref"],
            "attribution": row["attribution"], "disclosure": row["disclosure"],
        }

    def revoke(self, source_id: str, *, actor: str,
               at: datetime | None = None) -> bool:
        if not source_id.strip() or not actor.strip():
            raise ValueError("source_id and actor are required")
        when = _time(at or datetime.now(timezone.utc)).isoformat()
        with self._connect() as db:
            cur = db.execute("UPDATE source_rights SET revoked_at=? "
                             "WHERE source_id=? AND revoked_at IS NULL",
                             (when, source_id))
            if cur.rowcount:
                db.execute("""
                    INSERT INTO source_rights_audit(source_id, action, actor, occurred_at, details_json)
                    VALUES (?, 'revoked', ?, ?, '{}')
                """, (source_id, actor, when))
            return cur.rowcount == 1

    def audit_events(self, source_id: str) -> list[dict[str, str]]:
        with self._connect() as db:
            rows = db.execute("""
                SELECT action, actor, occurred_at, details_json
                FROM source_rights_audit WHERE source_id=? ORDER BY id
            """, (source_id,)).fetchall()
        return [dict(row) for row in rows]
