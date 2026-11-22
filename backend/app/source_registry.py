"""Small in-memory registry for scoped creator/source permissions.

Persistence and provider integrations are intentionally out of scope for this
first registry slice. Callers must supply a verified PermissionRecord.
"""
from __future__ import annotations

from datetime import datetime

from .models import PermissionRecord, parse_datetime


class SourceRegistry:
    """Store permission records and enforce unique source IDs."""

    def __init__(self) -> None:
        self._records: dict[str, PermissionRecord] = {}

    def register(self, record: PermissionRecord) -> None:
        if not isinstance(record, PermissionRecord):
            raise TypeError("record must be a PermissionRecord")
        if record.source_id in self._records:
            raise ValueError(f"source already registered: {record.source_id}")
        self._records[record.source_id] = record

    def get(self, source_id: str) -> PermissionRecord:
        try:
            return self._records[source_id]
        except KeyError as exc:
            raise KeyError(f"unknown source: {source_id}") from exc

    def revoke(self, source_id: str, at: datetime) -> PermissionRecord:
        current = self.get(source_id)
        revoked_at = parse_datetime(at)
        if revoked_at < current.granted_at:
            raise ValueError("revocation cannot precede the permission grant")
        if current.revoked_at is not None:
            raise ValueError("source permission is already revoked")
        updated = PermissionRecord(
            source_id=current.source_id,
            granted_by=current.granted_by,
            scopes=current.scopes,
            granted_at=current.granted_at,
            expires_at=current.expires_at,
            revoked_at=revoked_at,
        )
        self._records[source_id] = updated
        return updated

    def list_sources(self) -> tuple[PermissionRecord, ...]:
        """Return a stable snapshot without exposing the internal dictionary."""
        return tuple(self._records[key] for key in sorted(self._records))
