"""Deterministic, review-only selection of non-overlapping mapped clip windows.

This ranks already-detected candidates by their existing chat-activity score.
It does not inspect video, infer entertainment value, or authorize rendering.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .clipping import MAX_CLIP_SECONDS
from .models import CandidateMoment
from .video_chat_sync import VideoWindow


@dataclass(frozen=True)
class SelectionPolicy:
    max_clips: int = 5
    min_gap_seconds: float = 5.0
    max_total_duration_seconds: float = 300.0

    def __post_init__(self) -> None:
        if self.max_clips < 1:
            raise ValueError("max_clips must be at least one")
        if self.min_gap_seconds < 0:
            raise ValueError("min_gap_seconds cannot be negative")
        if self.max_total_duration_seconds <= 0:
            raise ValueError("max_total_duration_seconds must be positive")


def select_review_windows(
    candidates: Iterable[CandidateMoment],
    windows: Iterable[VideoWindow],
    policy: SelectionPolicy | None = None,
) -> list[dict[str, object]]:
    """Select high-scoring, separated windows; return them chronologically.

    Candidates and windows are paired by their input order. Their source IDs
    and mapped bounds are checked before any ranking occurs.
    """
    policy = policy or SelectionPolicy()
    candidate_list = list(candidates)
    window_list = list(windows)
    if len(candidate_list) != len(window_list):
        raise ValueError("each candidate must have exactly one mapped window")

    pairs: list[tuple[CandidateMoment, VideoWindow]] = []
    for candidate, window in zip(candidate_list, window_list):
        if candidate.source_id != window.source_id:
            raise ValueError("candidate and mapped window source IDs do not match")
        if window.start_seconds < 0 or window.end_seconds <= window.start_seconds:
            raise ValueError("mapped window has invalid bounds")
        duration = window.end_seconds - window.start_seconds
        if duration > MAX_CLIP_SECONDS:
            continue
        pairs.append((candidate, window))

    ranked = sorted(
        pairs,
        key=lambda pair: (
            -pair[0].score,
            -pair[0].peak_message_count,
            pair[1].start_seconds,
            pair[0].source_id,
        ),
    )
    chosen: list[tuple[CandidateMoment, VideoWindow]] = []
    total_duration = 0.0
    for candidate, window in ranked:
        duration = window.end_seconds - window.start_seconds
        if len(chosen) >= policy.max_clips:
            break
        if total_duration + duration > policy.max_total_duration_seconds:
            continue
        separated = all(
            window.end_seconds + policy.min_gap_seconds <= other.start_seconds
            or other.end_seconds + policy.min_gap_seconds <= window.start_seconds
            for _, other in chosen
        )
        if not separated:
            continue
        chosen.append((candidate, window))
        total_duration += duration

    result = []
    for candidate, window in sorted(chosen, key=lambda pair: pair[1].start_seconds):
        result.append({
            **window.to_dict(),
            "candidate_score": candidate.score,
            "peak_message_count": candidate.peak_message_count,
            "selection_reason": (
                "Highest-ranked eligible chat-activity candidate within the "
                "configured clip-count, duration, and separation limits."
            ),
            "human_review_required": True,
            "render_approved": False,
        })
    return result
