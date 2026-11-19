"""Permission-gated contracts for creator-authorized live sources.

Provider adapters must use official platform APIs or creator-supplied authorized
media references. This module deliberately does not scrape, rip, or bypass streams.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .models import PermissionRecord


@dataclass(frozen=True)
class LiveStream:
    source_id: str
    creator_id: str
    stream_id: str
    title: str
    started_at: datetime
    media_reference: str

    def __post_init__(self) -> None:
        values = (self.source_id, self.creator_id, self.stream_id, self.title, self.media_reference)
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError("live stream fields must be non-empty strings")
        if self.started_at.tzinfo is None or self.started_at.utcoffset() is None:
            raise ValueError("started_at must include a timezone")


class CreatorLiveSource(Protocol):
    """Adapter implemented by a platform's official, authorized integration."""

    def find_live_stream(self, creator_id: str) -> LiveStream | None:
        """Return current stream metadata, never an extracted protected stream URL."""
        ...

    def get_media_reference(self, stream: LiveStream) -> str:
        """Return a platform-approved media reference usable by an authorized worker."""
        ...


def require_source_permission(
    permission: PermissionRecord, source_id: str, *, at: datetime | None = None
) -> None:
    now = at or datetime.now(timezone.utc)
    if permission.source_id != source_id:
        raise PermissionError("permission grant does not match this source")
    if not permission.allows("read_live_stream", now):
        raise PermissionError("active read_live_stream permission is required")


def resolve_authorized_stream(
    adapter: CreatorLiveSource,
    creator_id: str,
    permission: PermissionRecord,
    *,
    at: datetime | None = None,
) -> LiveStream | None:
    """Discover a creator's live stream only under a matching current creator grant."""
    if not isinstance(creator_id, str) or not creator_id.strip():
        raise ValueError("creator_id is required")
    # The grant must match the requested creator before any provider call is made.
    require_source_permission(permission, creator_id, at=at)
    stream = adapter.find_live_stream(creator_id)
    if stream is None:
        return None
    if stream.source_id != permission.source_id or stream.creator_id != creator_id:
        raise PermissionError("provider returned a stream outside the granted creator/source")
    approved_reference = adapter.get_media_reference(stream)
    if not isinstance(approved_reference, str) or not approved_reference.strip():
        raise ValueError("provider returned an empty authorized media reference")
    return LiveStream(
        source_id=stream.source_id,
        creator_id=stream.creator_id,
        stream_id=stream.stream_id,
        title=stream.title,
        started_at=stream.started_at,
        media_reference=approved_reference,
    )
