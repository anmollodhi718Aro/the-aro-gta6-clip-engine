"""Prepare a human-selected local clip list without requiring chat or OAuth.

The generated CSV is compatible with backend.app.batch_render. This command
never downloads media, renders clips, uploads, or publishes anything.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from .clipping import MAX_CLIP_SECONDS

FIELDS = [
    "source_id", "score", "peak_message_count", "peak_window_start",
    "clip_start_utc", "clip_end_utc", "start_seconds", "end_seconds",
    "duration_seconds", "renderable", "sync_method",
    "sync_max_residual_seconds", "sync_drift_ppm", "review_note",
]


def build_manual_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate manually selected time ranges and convert them to render rows."""
    if not isinstance(payload, dict):
        raise ValueError("input JSON must be an object")
    source_id = payload.get("source_id")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string identifying the local recording")
    clips = payload.get("clips")
    if not isinstance(clips, list) or not clips:
        raise ValueError("clips must be a non-empty array")
    if len(clips) > 50:
        raise ValueError("at most 50 manual clip ranges are allowed per file")

    rows = []
    for number, clip in enumerate(clips, start=1):
        if not isinstance(clip, dict):
            raise ValueError(f"clips[{number - 1}] must be an object")
        start = clip.get("start_seconds")
        end = clip.get("end_seconds")
        if (isinstance(start, bool) or isinstance(end, bool)
                or not isinstance(start, (int, float))
                or not isinstance(end, (int, float))
                or not math.isfinite(start) or not math.isfinite(end)):
            raise ValueError(f"clip {number} start_seconds and end_seconds must be finite numbers")
        if start < 0 or end <= start:
            raise ValueError(f"clip {number} must satisfy 0 <= start_seconds < end_seconds")

        # The renderer and CSV contract use millisecond precision. Validate
        # after quantization too, otherwise a tiny positive range can round to
        # identical start/end values and fail later in the render pipeline.
        rounded_start = round(float(start), 3)
        rounded_end = round(float(end), 3)
        if rounded_end <= rounded_start:
            raise ValueError(
                f"clip {number} must span at least 0.001 seconds at millisecond precision"
            )
        duration = rounded_end - rounded_start
        if duration > MAX_CLIP_SECONDS:
            raise ValueError(f"clip {number} exceeds the {MAX_CLIP_SECONDS:g}-second maximum")
        note = clip.get("note", "manually selected; review before rendering")
        if not isinstance(note, str):
            raise ValueError(f"clip {number} note must be a string")
        rows.append({
            "source_id": source_id.strip(),
            "score": 0,
            "peak_message_count": 0,
            "peak_window_start": "",
            "clip_start_utc": "",
            "clip_end_utc": "",
            "start_seconds": rounded_start,
            "end_seconds": rounded_end,
            "duration_seconds": duration,
            "renderable": "true",
            "sync_method": "manual_local_media_time",
            "sync_max_residual_seconds": "",
            "sync_drift_ppm": "",
            "review_note": note,
        })
    return rows


def write_manual_csv(rows: list[dict[str, Any]], output: str | Path) -> Path:
    """Publish the CSV atomically and refuse to replace an existing file."""
    destination = Path(output).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=destination.parent,
            prefix=f".{destination.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, destination)
        return destination
    except FileExistsError:
        raise FileExistsError(f"output already exists; refusing to overwrite: {destination}") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a batch-render CSV from manually selected offsets in a local authorized video."
    )
    parser.add_argument("input", type=Path, help="JSON with source_id and clips[{start_seconds,end_seconds,note?}]")
    parser.add_argument("--output", type=Path, default=Path("manual_clips.csv"))
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        rows = build_manual_rows(payload)
        path = write_manual_csv(rows, args.output)
        print(f"Wrote {len(rows)} manually selected clip(s) to {path}")
        print("Next: inspect the CSV, then use backend.app.batch_render dry-run before any render.")
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Manual clip preparation stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
