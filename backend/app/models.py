"""Validated data models for permissions, chat events, and clip candidates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


def parse_datetime(value: str | datetime) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must include a timezone")
    return parsed


@dataclass(frozen=True)
class PermissionRecord:
    source_id: str
    granted_by: str
    scopes: frozenset[str]
    granted_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.granted_by.strip():
            raise ValueError("source_id and granted_by are required")
        object.__setattr__(self, "granted_at", parse_datetime(self.granted_at))
        if self.expires_at is not None:
            object.__setattr__(self, "expires_at", parse_datetime(self.expires_at))
        if self.revoked_at is not None:
            object.__setattr__(self, "revoked_at", parse_datetime(self.revoked_at))

    def allows(self, scope: str, at: datetime) -> bool:
        at = parse_datetime(at)
        if scope not in self.scopes or at < self.granted_at:
            return False
        if self.expires_at is not None and at >= self.expires_at:
            return False
        if self.revoked_at is not None and at >= self.revoked_at:
            return False
        return True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PermissionRecord":
        return cls(
            source_id=str(data["source_id"]),
            granted_by=str(data["granted_by"]),
            scopes=frozenset(str(scope) for scope in data.get("scopes", [])),
            granted_at=parse_datetime(data["granted_at"]),
            expires_at=parse_datetime(data["expires_at"]) if data.get("expires_at") else None,
            revoked_at=parse_datetime(data["revoked_at"]) if data.get("revoked_at") else None,
        )


@dataclass(frozen=True)
class ChatEvent:
    event_id: str
    source_id: str
    timestamp: datetime
    text: str = ""

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.source_id.strip():
            raise ValueError("event_id and source_id are required")
        object.__setattr__(self, "timestamp", parse_datetime(self.timestamp))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatEvent":
        return cls(
            event_id=str(data["event_id"]),
            source_id=str(data["source_id"]),
            timestamp=parse_datetime(data["timestamp"]),
            text=str(data.get("text", "")),
        )


@dataclass(frozen=True)
class CandidateMoment:
    source_id: str
    peak_window_start: datetime
    clip_start: datetime
    clip_end: datetime
    peak_message_count: int
    baseline_average: float
    score: int
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "peak_window_start": self.peak_window_start.isoformat(),
            "clip_start": self.clip_start.isoformat(),
            "clip_end": self.clip_end.isoformat(),
            "peak_message_count": self.peak_message_count,
            "baseline_average": round(self.baseline_average, 2),
            "score": self.score,
            "explanation": self.explanation,
            "status": "needs_review",
        }
