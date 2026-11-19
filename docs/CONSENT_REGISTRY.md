# Creator Consent Registry

## Purpose and boundaries

The local MVP now includes a SQLite-backed registry for source permission metadata. It stores one current grant per source and an append-only sequence of grant/revocation audit events. The registry is dependency-free and intended for the local MVP; a hosted deployment must use an authenticated database service, access controls, backups, and operational monitoring.

The registry does **not** authenticate the creator, collect signatures, or establish legal sufficiency. Keep the actual written authorization and any third-party rights records separately. Never treat a registry row as proof that game footage, music, or other third-party material is cleared.

## Basic use

```python
from datetime import datetime, timezone
from backend.app.consent_registry import ConsentRegistry
from backend.app.models import PermissionRecord

registry = ConsentRegistry("data/consent.sqlite3")
permission = PermissionRecord(
    source_id="YOUTUBE_VIDEO_ID",
    granted_by="creator-handle",
    scopes=frozenset({"analyze_chat"}),
    granted_at=datetime.now(timezone.utc),
)
registry.grant(permission, actor="operator")

# Fail closed if the source, scope, expiry, or revocation is invalid.
permission = registry.require("YOUTUBE_VIDEO_ID", "analyze_chat")

# Revocation is idempotent and recorded in the audit history.
registry.revoke("YOUTUBE_VIDEO_ID", actor="operator")
```

## Behavior

- SQLite persists records across process restarts.
- A grant/renewal replaces the current source grant and appends a `granted` audit event.
- Revocation updates the current record and appends a `revoked` event.
- Repeated revocation and revocation of an unknown source return `False`.
- `require` checks the requested scope, grant start, expiry, and revocation time; missing or invalid grants fail closed.
- The audit API returns metadata only. It does not store chat contents, API keys, or authorization documents.

## Production requirements

Before a public/cloud deployment, replace the local trust boundary with authenticated owner/admin actions, encrypted managed storage, backup/restore testing, retention controls, audit access restrictions, and a verified consent evidence workflow. Do not expose a registry write endpoint publicly without authentication and authorization.
