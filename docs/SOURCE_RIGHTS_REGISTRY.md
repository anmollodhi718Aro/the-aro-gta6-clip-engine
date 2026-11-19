# Source Rights Registry

`SourceRightsRegistry` stores source-specific permission metadata in SQLite and blocks a requested use unless all recorded conditions match.

## Record fields

- Stable source ID and source URL
- Grantor identity and evidence reference (for example, a contract or permission email reference; never store passwords or private credentials)
- Allowed uses: `analyze`, `edit`, `publish`
- Allowed platforms
- Required attribution and disclosure text
- Timezone-aware validity start and optional expiry
- Append-only registration/revocation audit events

## Example

```python
from backend.app.rights_registry import SourceRightsRegistry

rights = SourceRightsRegistry("state/rights.sqlite3")
rights.register({
    "source_id": "creator-video-001",
    "source_url": "https://example.com/source",
    "grantor": "Creator or rights holder",
    "evidence_ref": "permission-record-2026-001",
    "allowed_uses": ["analyze", "edit", "publish"],
    "platforms": ["youtube"],
    "attribution": "Required credit line",
    "disclosure": "Required disclosure",
    "valid_from": "2026-11-19T00:00:00+00:00"
})
rights.authorize("creator-video-001", "publish", "youtube")
```

Unknown, expired, future-dated, revoked, out-of-scope, or wrong-platform permissions fail closed. Re-registering a source renews the current record and adds an audit event.

## Limits

This is a metadata gate, not legal verification. It does not authenticate the grantor, validate the underlying evidence, clear embedded music/game/third-party rights, or establish compliance with platform rules. A recorded creator grant may be insufficient for other rights. When uncertain, do not process or publish.
