"""Measured conversion from UTC chat timestamps to local-media offsets."""
from __future__ import annotations
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from .clipping import MAX_CLIP_SECONDS, render_clip
from .models import CandidateMoment, parse_datetime

@dataclass(frozen=True)
class ClockSync:
    # chat_time = media_time + chat_minus_media_seconds
    chat_minus_media_seconds: float
    uncertainty_seconds: float
    measured_at: datetime
    method: str

    def __post_init__(self):
        if not math.isfinite(self.chat_minus_media_seconds):
            raise ValueError("clock offset must be finite")
        if not math.isfinite(self.uncertainty_seconds) or self.uncertainty_seconds < 0:
            raise ValueError("clock uncertainty must be finite and nonnegative")
        object.__setattr__(self, "measured_at", parse_datetime(self.measured_at))
        if not self.method.strip():
            raise ValueError("clock synchronization method is required")

@dataclass(frozen=True)
class MediaBounds:
    start_seconds: float
    end_seconds: float
    requested_start_seconds: float
    requested_end_seconds: float
    clipped_to_media_bounds: bool

    @property
    def duration_seconds(self):
        return self.end_seconds - self.start_seconds

    def to_dict(self):
        return {
            "start_seconds": round(self.start_seconds, 3),
            "end_seconds": round(self.end_seconds, 3),
            "duration_seconds": round(self.duration_seconds, 3),
            "requested_start_seconds": round(self.requested_start_seconds, 3),
            "requested_end_seconds": round(self.requested_end_seconds, 3),
            "clipped_to_media_bounds": self.clipped_to_media_bounds,
        }

def candidate_media_bounds(candidate: CandidateMoment, sync: ClockSync,
                           media_start_utc: datetime, media_duration_seconds: float,
                           *, max_sync_uncertainty_seconds: float = 2.0) -> MediaBounds:
    """Map candidate timestamps into seconds relative to the local media file."""
    media_start = parse_datetime(media_start_utc).astimezone(timezone.utc)
    if not math.isfinite(media_duration_seconds) or media_duration_seconds <= 0:
        raise ValueError("media duration must be finite and positive")
    if not math.isfinite(max_sync_uncertainty_seconds) or max_sync_uncertainty_seconds < 0:
        raise ValueError("maximum sync uncertainty must be finite and nonnegative")
    if sync.uncertainty_seconds > max_sync_uncertainty_seconds:
        raise ValueError("clock synchronization uncertainty exceeds the allowed limit")
    # chat_time = media_time + offset, hence media_time = chat_time - offset.
    requested_start = (parse_datetime(candidate.clip_start).astimezone(timezone.utc)
                       - media_start).total_seconds() - sync.chat_minus_media_seconds
    requested_end = (parse_datetime(candidate.clip_end).astimezone(timezone.utc)
                     - media_start).total_seconds() - sync.chat_minus_media_seconds
    if not math.isfinite(requested_start) or not math.isfinite(requested_end):
        raise ValueError("mapped clip bounds must be finite")
    if requested_end <= requested_start:
        raise ValueError("mapped clip bounds are reversed or empty")
    if requested_end - requested_start > MAX_CLIP_SECONDS:
        raise ValueError(f"candidate exceeds the {MAX_CLIP_SECONDS:g}-second clip limit")
    start = max(0.0, requested_start)
    end = min(float(media_duration_seconds), requested_end)
    if end <= start:
        raise ValueError("candidate does not overlap the supplied media file")
    return MediaBounds(round(start, 3), round(end, 3), requested_start, requested_end,
                       start != requested_start or end != requested_end)

def render_candidate(candidate: CandidateMoment, sync: ClockSync,
                     media_path: str | Path, output_path: str | Path, *,
                     media_start_utc: datetime, media_duration_seconds: float,
                     rights_confirmed: bool, max_sync_uncertainty_seconds: float = 2.0,
                     ffmpeg_binary: str = "ffmpeg") -> Path:
    """Render one candidate from an authorized local file through the existing clipper."""
    bounds = candidate_media_bounds(candidate, sync, media_start_utc, media_duration_seconds,
                                     max_sync_uncertainty_seconds=max_sync_uncertainty_seconds)
    return render_clip(media_path, output_path, bounds.start_seconds, bounds.end_seconds,
                       rights_confirmed=rights_confirmed, ffmpeg_binary=ffmpeg_binary)
