"""Small local source-permission registry with atomic JSON persistence.

This registry stores permission metadata only. It never stores credentials or
downloads source media. A source must be explicitly registered before use.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..models import PermissionRecord, parse_datetime

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class SourceRecord:
    permission: PermissionRecord
    permission_reference: str
    permitted_uses: tuple[str, ...]
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.permission_reference.strip():
            raise ValueError("permission_reference is required")
        if not self.permitted_uses:
            raise ValueError("at least one permitted use is required")
        object.__setattr__(self, "updated_at", parse_datetime(self.updated_at))


class SourceRegistry:
    """JSON-backed registry; callers should use one writer process per file."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": SCHEMA_VERSION, "sources": {}, "audit": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read source registry: {exc}") from exc
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported source registry schema version")
        if not isinstance(data.get("sources"), dict) or not isinstance(data.get("audit"), list):
            raise ValueError("source registry has an invalid structure")
        return data

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        except Exception:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
            raise

    @staticmethod
    def _permission_dict(permission: PermissionRecord) -> dict[str, Any]:
        return {
            "source_id": permission.source_id,
            "granted_by": permission.granted_by,
            "scopes": sorted(permission.scopes),
            "granted_at": permission.granted_at.isoformat(),
            "expires_at": permission.expires_at.isoformat() if permission.expires_at else None,
            "revoked_at": permission.revoked_at.isoformat() if permission.revoked_at else None,
        }

    @staticmethod
    def _permission_from_dict(data: dict[str, Any]) -> PermissionRecord:
        return PermissionRecord.from_dict(data)

    def register(
        self,
        permission: PermissionRecord,
        *,
        permission_reference: str,
        permitted_uses: tuple[str, ...],
        actor: str,
    ) -> SourceRecord:
        """Register a new source. Existing source IDs cannot be silently replaced."""
        if not actor.strip():
            raise ValueError("actor is required for the audit record")
        record = SourceRecord(
            permission=permission,
            permission_reference=permission_reference,
            permitted_uses=tuple(use.strip() for use in permitted_uses if use.strip()),
            updated_at=datetime.now(timezone.utc),
        )
        data = self._load()
        if permission.source_id in data["sources"]:
            raise ValueError("source is already registered; use an explicit future update workflow")
        data["sources"][permission.source_id] = {
            "permission": self._permission_dict(permission),
            "permission_reference": record.permission_reference,
            "permitted_uses": list(record.permitted_uses),
            "updated_at": record.updated_at.isoformat(),
        }
        data["audit"].append({
            "action": "source_registered",
            "source_id": permission.source_id,
            "actor": actor,
            "at": record.updated_at.isoformat(),
        })
        self._save(data)
        return record

    def get(self, source_id: str) -> SourceRecord:
        data = self._load()
        try:
            item = data["sources"][source_id]
        except KeyError as exc:
            raise KeyError(f"source is not registered: {source_id}") from exc
        return SourceRecord(
            permission=self._permission_from_dict(item["permission"]),
            permission_reference=item["permission_reference"],
            permitted_uses=tuple(item["permitted_uses"]),
            updated_at=parse_datetime(item["updated_at"]),
        )

    def require(self, source_id: str, scope: str, *, at: datetime | None = None) -> SourceRecord:
        """Return a registered source only when the requested scope is currently valid."""
        record = self.get(source_id)
        check_time = at or datetime.now(timezone.utc)
        if not record.permission.allows(scope, check_time):
            raise PermissionError("source permission is missing, expired, revoked, or out of scope")
        return record

    def revoke(self, source_id: str, *, actor: str, at: datetime | None = None) -> SourceRecord:
        """Revoke permission without deleting the source or its audit history."""
        if not actor.strip():
            raise ValueError("actor is required for the audit record")
        data = self._load()
        try:
            item = data["sources"][source_id]
        except KeyError as exc:
            raise KeyError(f"source is not registered: {source_id}") from exc
        now = parse_datetime(at or datetime.now(timezone.utc))
        permission = self._permission_from_dict(item["permission"])
        if permission.revoked_at is not None:
            raise ValueError("source permission is already revoked")
        revoked = PermissionRecord(
            source_id=permission.source_id,
            granted_by=permission.granted_by,
            scopes=permission.scopes,
            granted_at=permission.granted_at,
            expires_at=permission.expires_at,
            revoked_at=now,
        )
        item["permission"] = self._permission_dict(revoked)
        item["updated_at"] = now.isoformat()
        data["audit"].append({
            "action": "source_revoked",
            "source_id": source_id,
            "actor": actor,
            "at": now.isoformat(),
        })
        self._save(data)
        return self.get(source_id)

    def audit_log(self) -> list[dict[str, Any]]:
        """Return a copy of the append-only-by-API audit entries."""
        return list(self._load()["audit"])
