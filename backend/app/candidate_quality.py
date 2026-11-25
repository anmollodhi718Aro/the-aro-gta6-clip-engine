"""Explainable metadata scoring for human review of clip candidates.

Scores describe data completeness and review suitability, not predicted views,
virality, entertainment value, or permission to publish.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any


ACTIVITY_WEIGHT = 40
DURATION_WEIGHT = 30
SYNC_WEIGHT = 30
IDEAL_MIN_SECONDS = 15.0
IDEAL_MAX_SECONDS = 90.0
MAX_REVIEW_SECONDS = 180.0


def _number(row: dict[str, Any], field: str) -> float:
    raw = row.get(field)
    # bool is an int subclass in Python; accepting True as 1.0 can silently
    # turn malformed candidate metadata into a plausible score.
    if isinstance(raw, bool):
        raise ValueError(f"candidate {field} must be numeric, not boolean")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"candidate is missing a valid {field}") from exc
    if not math.isfinite(value):
        raise ValueError(f"candidate {field} must be finite")
    return value


def score_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Return a transparent 0-100 heuristic breakdown for one mapped row."""
    count = _number(row, "peak_message_count")
    duration = _number(row, "duration_seconds")
    if count < 0:
        raise ValueError("peak_message_count cannot be negative")
    if duration <= 0:
        raise ValueError("duration_seconds must be greater than zero")

    activity_ratio = min(count / 20.0, 1.0)
    if duration < IDEAL_MIN_SECONDS:
        duration_ratio = duration / IDEAL_MIN_SECONDS
    elif duration <= IDEAL_MAX_SECONDS:
        duration_ratio = 1.0
    elif duration < MAX_REVIEW_SECONDS:
        duration_ratio = (MAX_REVIEW_SECONDS - duration) / (
            MAX_REVIEW_SECONDS - IDEAL_MAX_SECONDS
        )
    else:
        duration_ratio = 0.0

    try:
        start = _number(row, "start_seconds")
        end = _number(row, "end_seconds")
        renderable = row.get("renderable") in (True, "True", "true", "1", 1)
        measured_bounds_duration = end - start
        bounds_match_duration = math.isclose(
            measured_bounds_duration, duration, rel_tol=0.0, abs_tol=0.05
        )
        synchronized = (
            renderable
            and start >= 0
            and end > start
            and duration <= MAX_REVIEW_SECONDS
            and measured_bounds_duration <= MAX_REVIEW_SECONDS
            and bounds_match_duration
        )
    except ValueError:
        synchronized = False

    activity_points = round(activity_ratio * ACTIVITY_WEIGHT, 2)
    duration_points = round(duration_ratio * DURATION_WEIGHT, 2)
    sync_points = SYNC_WEIGHT if synchronized else 0
    total = round(activity_points + duration_points + sync_points)

    reasons = [
        f"Chat activity: {count:g} messages in the source peak window "
        f"({activity_points:g}/{ACTIVITY_WEIGHT} points; capped at 20 messages).",
        f"Duration: {duration:g} seconds "
        f"({duration_points:g}/{DURATION_WEIGHT} points; full credit from "
        f"{IDEAL_MIN_SECONDS:g} to {IDEAL_MAX_SECONDS:g} seconds).",
        (
            f"Recording alignment: validated non-negative mapped bounds "
            f"({sync_points}/{SYNC_WEIGHT} points)."
            if synchronized
            else f"Recording alignment: not verified as renderable "
            f"({sync_points}/{SYNC_WEIGHT} points)."
        ),
    ]
    return {
        "quality_score": total,
        "activity_points": activity_points,
        "duration_points": duration_points,
        "sync_points": sync_points,
        "quality_reasons": reasons,
    }


def score_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**row, **score_candidate(row)} for row in rows]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add explainable review-suitability scores to a measured candidate CSV."
    )
    parser.add_argument("candidates", type=Path, help="clip_candidates.csv")
    parser.add_argument("--output", type=Path, default=Path("quality_scored_candidates.csv"))
    args = parser.parse_args()
    try:
        source = args.candidates.expanduser()
        output = args.output.expanduser()
        # Never let a scoring run destroy its own input CSV, including when
        # the same file is addressed through relative paths or symlinks.
        if source.resolve() == output.resolve():
            raise ValueError("output path must differ from the candidate input path")
        with source.open("r", newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError("candidate CSV is empty")
        scored = score_rows(rows)
        output.parent.mkdir(parents=True, exist_ok=True)
        fields = list(scored[0])
        # Exclusive creation prevents silently replacing a prior review pack.
        # It also closes the check-then-open race from an exists() preflight.
        with output.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in scored:
                saved = dict(row)
                saved["quality_reasons"] = " | ".join(saved["quality_reasons"])
                writer.writerow(saved)
        summary = {
            "candidate_count": len(scored),
            "scores_are_predictive": False,
            "human_review_required": True,
            "scoring_weights": {
                "chat_activity": ACTIVITY_WEIGHT,
                "duration_suitability": DURATION_WEIGHT,
                "recording_alignment": SYNC_WEIGHT,
            },
            "output": str(output),
        }
        print(json.dumps(summary, indent=2))
        return 0
    except (OSError, csv.Error, ValueError) as exc:
        print(f"Candidate scoring stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
