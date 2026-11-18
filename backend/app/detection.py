"""Deterministic chat-spike detector. No network or AI provider required."""

from __future__ import annotations

from collections import Counter
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
        if self.window_seconds <= 0 or self.baseline_windows <= 0:
            raise ValueError("window_seconds and baseline_windows must be positive")
        if self.spike_multiplier <= 0 or self.min_messages <= 0:
            raise ValueError("spike_multiplier and min_messages must be positive")
        if self.pre_roll_seconds < 0 or self.post_roll_seconds < 0:
            raise ValueError("clip padding cannot be negative")


def detect_chat_spikes(
    events: list[ChatEvent],
    permission: PermissionRecord,
    config: DetectorConfig | None = None,
) -> list[CandidateMoment]:
    """Return explainable spike candidates only when chat-analysis permission is valid."""
    config = config or DetectorConfig()
    if not events:
        return []

    if any(event.source_id != permission.source_id for event in events):
        raise ValueError("event source does not match the permission record")
    if any(not permission.allows("analyze_chat", event.timestamp) for event in events):
        raise PermissionError("source permission is missing, expired, revoked, or out of scope")

    ordered = sorted(events, key=lambda event: event.timestamp)
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
        threshold = max(config.min_messages, baseline * config.spike_multiplier)
        if current_count < config.min_messages or current_count <= threshold:
            continue

        peak_start = datetime.fromtimestamp(bucket * config.window_seconds, tz=timezone.utc)
        clip_start = peak_start - timedelta(seconds=config.pre_roll_seconds)
        clip_end = peak_start + timedelta(seconds=config.window_seconds + config.post_roll_seconds)
        ratio = current_count / max(baseline, 1.0)
        score = min(100, max(0, round(50 + ratio * 10)))
        explanation = (
            f"{current_count} chat events in {config.window_seconds}s; "
            f"previous {config.baseline_windows}-window average was {baseline:.2f}; "
            f"spike threshold was {threshold:.2f}."
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
