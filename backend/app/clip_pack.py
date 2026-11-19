"""Convert reviewed chat candidates into video-relative clip edit notes.

The operator must supply a measured UTC timestamp for media offset zero.
This module never downloads, renders, or publishes video.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .clipping import MAX_CLIP_SECONDS
from .models import parse_datetime


FIELDS = [
    "source_id", "score", "peak_message_count", "peak_window_start",
    "clip_start_utc", "clip_end_utc", "start_seconds", "end_seconds",
    "duration_seconds", "renderable", "review_note",
]


def map_candidates_to_media(
    candidates: list[dict[str, Any]], media_origin_utc: str | datetime
) -> list[dict[str, Any]]:
    """Map UTC candidate timestamps to local-media offsets using measured sync."""
    origin = parse_datetime(media_origin_utc)
    mapped: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        try:
            start = parse_datetime(candidate["clip_start"])
            end = parse_datetime(candidate["clip_end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"candidate {index} has invalid clip timestamps: {exc}") from exc
        if end <= start:
            raise ValueError(f"candidate {index} has clip_end <= clip_start")

        start_seconds = (start - origin).total_seconds()
        end_seconds = (end - origin).total_seconds()
        duration = end_seconds - start_seconds
        note = "ready for human review"
        renderable = True
        if end_seconds <= 0:
            renderable = False
            note = "candidate ends before the local recording starts"
        elif start_seconds < 0:
            renderable = False
            note = "candidate begins before the local recording; partial clipping is disabled"
        elif duration > MAX_CLIP_SECONDS:
            renderable = False
            note = f"duration exceeds the {MAX_CLIP_SECONDS:g}-second renderer limit"

        mapped.append({
            "source_id": str(candidate.get("source_id", "")),
            "score": int(candidate.get("score", 0)),
            "peak_message_count": int(candidate.get("peak_message_count", 0)),
            "peak_window_start": str(candidate.get("peak_window_start", "")),
            "clip_start_utc": start.isoformat(),
            "clip_end_utc": end.isoformat(),
            "start_seconds": round(start_seconds, 3),
            "end_seconds": round(end_seconds, 3),
            "duration_seconds": round(duration, 3),
            "renderable": renderable,
            "review_note": note,
        })
    return mapped


def write_clip_pack(rows: list[dict[str, Any]], output_dir: str | Path) -> tuple[Path, Path]:
    destination = Path(output_dir).expanduser()
    destination.mkdir(parents=True, exist_ok=True)
    csv_path = destination / "clip_candidates.csv"
    markdown_path = destination / "clip_candidates.md"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# GTA 6 Clip Candidate Review",
        "",
        "These are edit notes only. Review the source, rights, context, and timing before rendering or publishing.",
        "",
        "| # | Score | Start (s) | End (s) | Duration (s) | Status |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for number, row in enumerate(rows, start=1):
        status = "Review-ready" if row["renderable"] else row["review_note"]
        lines.append(
            f"| {number} | {row['score']} | {row['start_seconds']:.3f} | "
            f"{row['end_seconds']:.3f} | {row['duration_seconds']:.3f} | {status} |"
        )
    lines.extend([
        "",
        "## Review notes",
        "",
        "- Chat activity is a signal, not proof that a moment is entertaining or suitable.",
        "- Offsets are valid only for the exact recording whose UTC media origin was measured.",
        "- No video is downloaded, rendered, uploaded, or published by this command.",
        "- Confirm creator permission and all applicable game, music, and third-party rights.",
        "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Map reviewed chat candidates to a local recording using a measured UTC media origin."
    )
    parser.add_argument("plan", type=Path, help="JSON candidate plan produced by the analysis CLI")
    parser.add_argument(
        "--media-origin-utc",
        required=True,
        help="Measured timezone-aware UTC timestamp corresponding to local media offset 0",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("clip_pack"))
    args = parser.parse_args()
    try:
        payload = json.loads(args.plan.read_text(encoding="utf-8"))
        candidates = payload.get("candidates")
        if not isinstance(candidates, list):
            raise ValueError("plan must contain a candidates array")
        rows = map_candidates_to_media(candidates, args.media_origin_utc)
        csv_path, markdown_path = write_clip_pack(rows, args.output_dir)
        ready = sum(1 for row in rows if row["renderable"])
        print(f"Wrote {len(rows)} candidate(s), {ready} review-ready, to {csv_path} and {markdown_path}")
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Clip pack stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
