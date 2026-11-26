"""Deterministic chat-spike detector. No network or AI provider required."""

from __future__ import annotations

from collections import Counter
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .models import CandidateMoment, ChatEvent, PermissionRecord


@dataclass(frozen=True)
class DetectorConfig:
    window_seconds: int = 10
    baseline_windows: int = 3
    spike_multiplier: float = 2.0
    min_messages: int = 5
    pre_roll_seconds: int = 15
    post_roll_seconds: int = 15

    def __post_init__(self) -> None:
        positive_integer_fields = {
            "window_seconds": self.window_seconds,
            "baseline_windows": self.baseline_windows,
            "min_messages": self.min_messages,
        }
        for field_name, value in positive_integer_fields.items():
            if type(value) is not int or value <= 0:
                raise ValueError(f"{field_name} must be a positive integer")

        non_negative_integer_fields = {
            "pre_roll_seconds": self.pre_roll_seconds,
            "post_roll_seconds": self.post_roll_seconds,
        }
        for field_name, value in non_negative_integer_fields.items():
            if type(value) is not int or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")

        try:
            multiplier_is_finite = math.isfinite(self.spike_multiplier)
        except (TypeError, OverflowError):
            multiplier_is_finite = False
        if (
            isinstance(self.spike_multiplier, bool)
            or not multiplier_is_finite
            or self.spike_multiplier <= 0
        ):
            raise ValueError("spike_multiplier must be a finite positive number")


def _deduplicate_events(events: list[ChatEvent]) -> list[ChatEvent]:
    """Make ingestion idempotent; reject an ID reused for different event data."""
    by_id: dict[str, ChatEvent] = {}
    for event in events:
        previous = by_id.get(event.event_id)
        if previous is None:
            by_id[event.event_id] = event
        elif previous != event:
            raise ValueError(f"conflicting duplicate event_id: {event.event_id}")
    return sorted(by_id.values(), key=lambda event: (event.timestamp, event.event_id))


def detect_chat_spikes(
    events: list[ChatEvent],
    permission: PermissionRecord,
    config: DetectorConfig | None = None,
) -> list[CandidateMoment]:
    """Return explainable spike candidates only when chat-analysis permission is valid.

    Duplicate identical event IDs are ignored so retrying an event batch cannot
    inflate the chat rate. Reusing an ID for different data is rejected.
    """
    if config is None:
        config = DetectorConfig()
    elif not isinstance(config, DetectorConfig):
        raise ValueError("config must be a DetectorConfig instance")
    if not events:
        return []

    if any(event.source_id != permission.source_id for event in events):
        raise ValueError("event source does not match the permission record")
    if any(not permission.allows("analyze_chat", event.timestamp) for event in events):
        raise PermissionError("source permission is missing, expired, revoked, or out of scope")

    ordered = _deduplicate_events(events)
    if not ordered:
        return []

    counts: Counter[int] = Counter()
    for event in ordered:
        bucket = int(event.timestamp.timestamp()) // config.window_seconds
        counts[bucket] += 1

    first_bucket = min(counts)
    last_bucket = max(counts)
    candidates: list[CandidateMoment] = []

    for bucket in range(first_bucket + config.baseline_windows, last_bucket + 1):
        current_count = counts.get(bucket, 0)
        previous = [counts.get(index, 0) for index in range(bucket - config.baseline_windows, bucket)]
        baseline = sum(previous) / config.baseline_windows
        relative_threshold = baseline * config.spike_multiplier
        if current_count < config.min_messages or current_count <= relative_threshold:
            continue

        peak_start = datetime.fromtimestamp(bucket * config.window_seconds, tz=timezone.utc)
        clip_start = peak_start - timedelta(seconds=config.pre_roll_seconds)
        clip_end = peak_start + timedelta(seconds=config.window_seconds + config.post_roll_seconds)
        ratio = current_count / max(baseline, 1.0)
        score = min(100, max(0, round(50 + ratio * 10)))
        explanation = (
            f"{current_count} unique chat events in {config.window_seconds}s; "
            f"previous {config.baseline_windows}-window average was {baseline:.2f}; "
            f"relative spike threshold was {relative_threshold:.2f}; "
            f"minimum event count was {config.min_messages}."
        )
        candidates.append(CandidateMoment(
            source_id=permission.source_id,
            peak_window_start=peak_start,
            clip_start=clip_start,
            clip_end=clip_end,
            peak_message_count=current_count,
            baseline_average=baseline,
            score=score,
            explanation=explanation,
        ))

    return candidates
