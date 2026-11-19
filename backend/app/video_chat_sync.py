"""Explicit-offset mapping between chat timestamps and video positions.

The offset must be measured by an operator from a shared synchronization event.
This module never guesses or learns the offset from chat activity.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .models import CandidateMoment, parse_datetime


@dataclass(frozen=True)
class ClockOffset:
    """video_time = chat_time + offset_seconds."""
    offset_seconds: float
    measured_by: str
    measured_at: datetime
    uncertainty_seconds: float = 0.0

    def __post_init__(self) -> None:
        if not self.measured_by.strip():
            raise ValueError("measured_by is required")
        if self.uncertainty_seconds < 0:
            raise ValueError("uncertainty_seconds cannot be negative")
        if abs(self.offset_seconds) > 86400:
            raise ValueError("offset_seconds must be within one day")
        object.__setattr__(self, "measured_at", parse_datetime(self.measured_at))


@dataclass(frozen=True)
class VideoWindow:
    source_id: str
    start_seconds: float
    end_seconds: float
    confidence: str
    offset_seconds: float
    uncertainty_seconds: float

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "start_seconds": round(self.start_seconds, 3),
            "end_seconds": round(self.end_seconds, 3),
            "confidence": self.confidence,
            "offset_seconds": self.offset_seconds,
            "uncertainty_seconds": self.uncertainty_seconds,
            "status": "needs_review",
        }


def map_chat_timestamp_to_video_seconds(
    chat_timestamp: str | datetime,
    video_epoch: str | datetime,
    offset: ClockOffset,
) -> float:
    """Map a chat wall-clock timestamp to seconds from video_epoch."""
    chat_dt = parse_datetime(chat_timestamp)
    video_origin = parse_datetime(video_epoch)
    mapped = (chat_dt - video_origin).total_seconds() + offset.offset_seconds
    if mapped < 0:
        raise ValueError("mapped timestamp falls before the video origin")
    return mapped


def candidate_to_video_window(
    candidate: CandidateMoment,
    video_epoch: str | datetime,
    offset: ClockOffset,
    *,
    video_duration_seconds: float,
) -> VideoWindow:
    """Map a candidate's clip bounds; reject windows outside the supplied video."""
    if video_duration_seconds <= 0:
        raise ValueError("video_duration_seconds must be positive")
    start = map_chat_timestamp_to_video_seconds(candidate.clip_start, video_epoch, offset)
    end = map_chat_timestamp_to_video_seconds(candidate.clip_end, video_epoch, offset)
    if end <= start:
        raise ValueError("mapped clip window must have positive duration")
    if end > video_duration_seconds:
        raise ValueError("mapped clip window exceeds video duration")
    confidence = "low" if offset.uncertainty_seconds > 2 else "operator_measured"
    return VideoWindow(
        source_id=candidate.source_id,
        start_seconds=start,
        end_seconds=end,
        confidence=confidence,
        offset_seconds=offset.offset_seconds,
        uncertainty_seconds=offset.uncertainty_seconds,
    )


def map_candidates(
    candidates: Iterable[CandidateMoment],
    video_epoch: str | datetime,
    offset: ClockOffset,
    *,
    video_duration_seconds: float,
) -> list[VideoWindow]:
    """Map candidates in chronological order without silently dropping failures."""
    windows = [
        candidate_to_video_window(
            candidate, video_epoch, offset, video_duration_seconds=video_duration_seconds
        )
        for candidate in candidates
    ]
    return sorted(windows, key=lambda window: (window.start_seconds, window.end_seconds))
