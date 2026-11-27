"""Map reviewed chat candidates to local-video offsets using measured clocks.

No timestamps are guessed. Either a measured media-origin timestamp or a
multi-anchor clock calibration from the exact same source is required.
This module never downloads, renders, or publishes video.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .clock_sync import ClockAnchor, ClockSync, fit_clock_sync
from .clipping import MAX_CLIP_SECONDS
from .models import parse_datetime


FIELDS = [
    "source_id", "score", "peak_message_count", "peak_window_start",
    "clip_start_utc", "clip_end_utc", "start_seconds", "end_seconds",
    "duration_seconds", "renderable", "sync_method",
    "sync_max_residual_seconds", "sync_drift_ppm", "review_note",
]


def load_clock_sync(path: str | Path, *, max_residual_seconds: float | None = None,
                    max_drift_ppm: float | None = None) -> ClockSync:
    """Load operator-measured anchors and fit a bounded, source-specific clock."""
    source = Path(path).expanduser()
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("anchors"), list):
        raise ValueError("clock anchor JSON must contain an anchors array")
    anchors = []
    for index, row in enumerate(payload["anchors"], start=1):
        if not isinstance(row, dict):
            raise ValueError(f"anchors[{index - 1}] must be an object")
        try:
            anchors.append(ClockAnchor(
                source_id=row["source_id"],
                chat_time=parse_datetime(row["chat_time"]),
                media_seconds=row["media_seconds"],
            ))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid clock anchor {index}: {exc}") from exc
    residual_limit = payload.get("max_residual_seconds", 1.0) if max_residual_seconds is None else max_residual_seconds
    drift_limit = payload.get("max_drift_ppm", 1000.0) if max_drift_ppm is None else max_drift_ppm
    return fit_clock_sync(
        anchors,
        max_residual_seconds=residual_limit,
        max_drift_ppm=drift_limit,
    )


def map_candidates_to_media(
    candidates: list[dict[str, Any]],
    media_origin_utc: str | datetime | None = None,
    *,
    clock_sync: ClockSync | None = None,
    source_id: str | None = None,
) -> list[dict[str, Any]]:
    """Map chat time to media seconds using one measured origin or a fitted clock."""
    if (media_origin_utc is None) == (clock_sync is None):
        raise ValueError("provide exactly one of media_origin_utc or clock_sync")
    if source_id is not None:
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("source_id must be a non-empty string when provided")
        source_id = source_id.strip()
    origin = (
        parse_datetime(media_origin_utc).astimezone(timezone.utc)
        if media_origin_utc is not None else None
    )
    if clock_sync and source_id and source_id != clock_sync.source_id:
        raise ValueError("clip plan source_id does not match the calibrated clock source")

    mapped: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        try:
            start = parse_datetime(candidate["clip_start"]).astimezone(timezone.utc)
            end = parse_datetime(candidate["clip_end"]).astimezone(timezone.utc)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"candidate {index} has invalid clip timestamps: {exc}") from exc
        if end <= start:
            raise ValueError(f"candidate {index} has clip_end <= clip_start")

        raw_candidate_source = candidate.get("source_id")
        if raw_candidate_source is None:
            candidate_source = source_id or ""
        else:
            if not isinstance(raw_candidate_source, str):
                raise ValueError(f"candidate {index} source_id must be a string")
            candidate_source = raw_candidate_source.strip()
        if clock_sync:
            # A calibrated clock is valid only for the exact source measured
            # by its anchors. Missing or whitespace-only IDs fail closed.
            if not candidate_source:
                raise ValueError(
                    f"candidate {index} is missing source_id required by the calibrated clock"
                )
            if candidate_source != clock_sync.source_id:
                raise ValueError(f"candidate {index} belongs to a different clock source")
            start_seconds = clock_sync.map_chat_time(start)
            end_seconds = clock_sync.map_chat_time(end)
            sync_method = "measured_multi_anchor_fit"
            residual = round(clock_sync.max_residual_seconds, 6)
            drift = round(clock_sync.drift_ppm, 6)
        else:
            assert origin is not None
            start_seconds = (start - origin).total_seconds()
            end_seconds = (end - origin).total_seconds()
            sync_method = "measured_single_origin"
            residual = 0.0
            drift = 0.0

        duration = end_seconds - start_seconds
        note = "ready for human review"
        renderable = True
        if end_seconds <= 0:
            renderable = False
            note = "candidate ends before the local recording starts"
        elif start_seconds < 0:
            renderable = False
            note = "candidate begins before the local recording; partial clipping is disabled"
        elif duration <= 0:
            renderable = False
            note = "mapped clip duration is not positive"
        elif duration > MAX_CLIP_SECONDS:
            renderable = False
            note = f"duration exceeds the {MAX_CLIP_SECONDS:g}-second renderer limit"

        mapped.append({
            "source_id": candidate_source,
            "score": int(candidate.get("score", 0)),
            "peak_message_count": int(candidate.get("peak_message_count", 0)),
            "peak_window_start": str(candidate.get("peak_window_start", "")),
            "clip_start_utc": start.isoformat(),
            "clip_end_utc": end.isoformat(),
            "start_seconds": round(start_seconds, 3),
            "end_seconds": round(end_seconds, 3),
            "duration_seconds": round(duration, 3),
            "renderable": renderable,
            "sync_method": sync_method,
            "sync_max_residual_seconds": residual,
            "sync_drift_ppm": drift,
            "review_note": note,
        })
    return mapped


def _write_texts_no_overwrite(files: dict[Path, str]) -> None:
    """Stage all text outputs, then publish without replacing existing files."""
    staged: list[tuple[Path, Path]] = []
    published: list[tuple[Path, Path]] = []
    try:
        for target, content in files.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="", dir=target.parent,
                prefix=f".{target.name}.", suffix=".tmp", delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            staged.append((temporary, target))

        for temporary, target in staged:
            os.link(temporary, target)
            published.append((temporary, target))
    except Exception:
        for temporary, target in reversed(published):
            try:
                if target.exists() and os.path.samefile(temporary, target):
                    target.unlink()
            except OSError:
                pass
        raise
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def write_clip_pack(rows: list[dict[str, Any]], output_dir: str | Path) -> tuple[Path, Path]:
    destination = Path(output_dir).expanduser()
    destination.mkdir(parents=True, exist_ok=True)
    csv_path = destination / "clip_candidates.csv"
    markdown_path = destination / "clip_candidates.md"

    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)

    lines = [
        "# GTA 6 Clip Candidate Review", "",
        "These are edit notes only. Review source rights, context, and timing before rendering or publishing.", "",
        "| # | Score | Start (s) | End (s) | Duration (s) | Sync method | Status |",
        "|---:|---:|---:|---:|---:|---|---|",
    ]
    for number, row in enumerate(rows, start=1):
        status = "Review-ready" if row["renderable"] else row["review_note"]
        lines.append(
            f"| {number} | {row['score']} | {row['start_seconds']:.3f} | "
            f"{row['end_seconds']:.3f} | {row['duration_seconds']:.3f} | "
            f"{row['sync_method']} | {status} |"
        )
    lines.extend([
        "", "## Review notes", "",
        "- Chat activity is a signal, not proof that a moment is entertaining or suitable.",
        "- Multi-anchor clock calibration is limited to the measured interval; it never extrapolates.",
        "- No video is downloaded, rendered, uploaded, or published by this command.",
        "- Confirm creator permission and all applicable game, music, and third-party rights.", "",
    ])
    _write_texts_no_overwrite({
        csv_path: csv_buffer.getvalue(),
        markdown_path: "\n".join(lines),
    })
    return csv_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Map reviewed chat candidates to a local recording with a measured clock."
    )
    parser.add_argument("plan", type=Path, help="JSON candidate plan produced by the analysis CLI")
    sync_group = parser.add_mutually_exclusive_group(required=True)
    sync_group.add_argument(
        "--media-origin-utc",
        help="Measured timezone-aware UTC timestamp corresponding to local media offset 0",
    )
    sync_group.add_argument(
        "--clock-anchors-json", type=Path,
        help="JSON file with at least three measured {source_id, chat_time, media_seconds} anchors",
    )
    parser.add_argument("--max-anchor-residual", type=float, default=None)
    parser.add_argument("--max-clock-drift-ppm", type=float, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("clip_pack"))
    args = parser.parse_args()
    try:
        payload = json.loads(args.plan.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("candidates"), list):
            raise ValueError("plan must be an object containing a candidates array")
        plan_source_id = payload.get("source_id")
        if plan_source_id is not None and (
            not isinstance(plan_source_id, str) or not plan_source_id.strip()
        ):
            raise ValueError("plan source_id must be a non-empty string when provided")
        if args.clock_anchors_json:
            sync = load_clock_sync(
                args.clock_anchors_json,
                max_residual_seconds=args.max_anchor_residual,
                max_drift_ppm=args.max_clock_drift_ppm,
            )
            rows = map_candidates_to_media(
                payload["candidates"], clock_sync=sync,
                source_id=plan_source_id,
            )
        else:
            rows = map_candidates_to_media(
                payload["candidates"], args.media_origin_utc,
                source_id=plan_source_id,
            )
        csv_path, markdown_path = write_clip_pack(rows, args.output_dir)
        ready = sum(1 for row in rows if row["renderable"])
        print(f"Wrote {len(rows)} candidate(s), {ready} review-ready, to {csv_path} and {markdown_path}")
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Clip pack stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
