"""Measured chat-to-recording clock calibration.

This module never guesses an offset. Operators must provide at least three
paired synchronization markers measured against the same authorized source.
Mappings are restricted to the calibrated time interval (no extrapolation).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .models import parse_datetime


def _is_finite_number(value: int | float) -> bool:
    """Return False for numeric values too large for math.isfinite to convert."""
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


@dataclass(frozen=True)
class ClockAnchor:
    """One manually verified pair of chat time and local-media position."""

    source_id: str
    chat_time: datetime
    media_seconds: float

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id is required")
        # Store one canonical identity so surrounding whitespace cannot make
        # otherwise identical anchor and candidate IDs compare differently.
        object.__setattr__(self, "source_id", self.source_id.strip())
        object.__setattr__(self, "chat_time", parse_datetime(self.chat_time).astimezone(timezone.utc))
        if isinstance(self.media_seconds, bool) or not isinstance(self.media_seconds, (int, float)):
            raise ValueError("media_seconds must be a finite number")
        if not _is_finite_number(self.media_seconds) or self.media_seconds < 0:
            raise ValueError("media_seconds must be a finite non-negative number")
        object.__setattr__(self, "media_seconds", float(self.media_seconds))


@dataclass(frozen=True)
class ClockSync:
    """Linear clock mapping calibrated from operator-measured anchors."""

    source_id: str
    origin_chat_time: datetime
    end_chat_time: datetime
    media_at_origin: float
    rate: float
    max_residual_seconds: float
    drift_ppm: float

    def map_chat_time(self, chat_time: datetime) -> float:
        """Map a chat timestamp to media seconds inside the measured interval."""
        instant = parse_datetime(chat_time).astimezone(timezone.utc)
        if instant < self.origin_chat_time or instant > self.end_chat_time:
            raise ValueError("chat timestamp is outside the calibrated interval")
        elapsed = (instant - self.origin_chat_time).total_seconds()
        mapped = self.media_at_origin + self.rate * elapsed
        if not math.isfinite(mapped) or mapped < 0:
            raise ValueError("mapped media position is invalid")
        return mapped


def fit_clock_sync(
    anchors: Iterable[ClockAnchor],
    *,
    max_residual_seconds: float = 1.0,
    max_drift_ppm: float = 1000.0,
) -> ClockSync:
    """Fit a measured linear clock mapping and reject poor calibration data.

    Three or more anchors are required so the fit has an independent residual
    check. The default drift ceiling is 1000 ppm (0.1%); callers may tighten it.
    """
    if (
        isinstance(max_residual_seconds, bool)
        or not isinstance(max_residual_seconds, (int, float))
        or not _is_finite_number(max_residual_seconds)
        or max_residual_seconds <= 0
    ):
        raise ValueError("max_residual_seconds must be a positive finite number")
    if (
        isinstance(max_drift_ppm, bool)
        or not isinstance(max_drift_ppm, (int, float))
        or not _is_finite_number(max_drift_ppm)
        or max_drift_ppm <= 0
    ):
        raise ValueError("max_drift_ppm must be a positive finite number")

    rows = list(anchors)
    if len(rows) < 3:
        raise ValueError("at least three measured clock anchors are required")
    if not all(isinstance(anchor, ClockAnchor) for anchor in rows):
        raise TypeError("all anchors must be ClockAnchor instances")
    source_ids = {anchor.source_id for anchor in rows}
    if len(source_ids) != 1:
        raise ValueError("all clock anchors must belong to the same source")

    rows.sort(key=lambda anchor: anchor.chat_time)
    chat_seconds = [anchor.chat_time.timestamp() for anchor in rows]
    media_seconds = [anchor.media_seconds for anchor in rows]
    if any(b <= a for a, b in zip(chat_seconds, chat_seconds[1:])):
        raise ValueError("chat anchor times must be strictly increasing")
    if any(b <= a for a, b in zip(media_seconds, media_seconds[1:])):
        raise ValueError("media anchor positions must be strictly increasing")

    # Center x values around the first anchor to avoid loss of precision from
    # large Unix timestamps. Fit y = intercept + rate * elapsed_chat_seconds.
    origin = chat_seconds[0]
    xs = [value - origin for value in chat_seconds]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(media_seconds) / len(media_seconds)
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator <= 0:
        raise ValueError("clock anchors do not span a measurable interval")
    rate = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, media_seconds)) / denominator
    intercept = mean_y - rate * mean_x
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("measured clock rate must be positive and finite")

    drift_ppm = (rate - 1.0) * 1_000_000
    if abs(drift_ppm) > max_drift_ppm:
        raise ValueError(
            f"measured clock drift {drift_ppm:.1f} ppm exceeds limit {max_drift_ppm:.1f} ppm"
        )

    residuals = [abs(y - (intercept + rate * x)) for x, y in zip(xs, media_seconds)]
    worst_residual = max(residuals)
    if worst_residual > max_residual_seconds:
        raise ValueError(
            f"clock anchor residual {worst_residual:.3f}s exceeds limit "
            f"{max_residual_seconds:.3f}s"
        )

    return ClockSync(
        source_id=next(iter(source_ids)),
        origin_chat_time=rows[0].chat_time,
        end_chat_time=rows[-1].chat_time,
        media_at_origin=intercept,
        rate=rate,
        max_residual_seconds=worst_residual,
        drift_ppm=drift_ppm,
    )
