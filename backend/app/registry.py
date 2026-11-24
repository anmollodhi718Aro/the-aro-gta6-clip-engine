"""Small in-memory source permission registry for the MVP.

This registry deliberately stores metadata only. It does not fetch sources,
persist credentials, or grant rights beyond the scopes recorded by a creator.
"""

from __future__ import annotations

from datetime import datetime

from .models import PermissionRecord, parse_datetime


class SourcePermissionRegistry:
    """Register, inspect, revoke, and enforce source-scoped permissions."""

    def __init__(self) -> None:
        self._records: dict[str, PermissionRecord] = {}

    def register(self, record: PermissionRecord) -> None:
        if record.source_id in self._records:
            raise ValueError(f"permission already registered for source: {record.source_id}")
        self._records[record.source_id] = record

    def get(self, source_id: str) -> PermissionRecord | None:
        return self._records.get(source_id)

    def revoke(self, source_id: str, at: datetime) -> PermissionRecord:
        current = self._records.get(source_id)
        if current is None:
            raise KeyError(f"unknown source: {source_id}")
        revoked_at = parse_datetime(at)
        if revoked_at < current.granted_at:
            raise ValueError("revocation cannot precede the permission grant")
        if current.revoked_at is not None and revoked_at >= current.revoked_at:
            return current

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

    def is_allowed(self, source_id: str, scope: str, at: datetime) -> bool:
        record = self._records.get(source_id)
        return record is not None and record.allows(scope, at)

    def require(self, source_id: str, scope: str, at: datetime) -> PermissionRecord:
        record = self._records.get(source_id)
        if record is None or not record.allows(scope, at):
            raise PermissionError(
                f"source '{source_id}' is not authorized for scope '{scope}' at the requested time"
            )
        return record
