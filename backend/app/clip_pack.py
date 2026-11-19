"""Build review-only clip edit notes using measured chat-to-media clock sync.

No media is downloaded, rendered, uploaded, or published by this module.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from .clock_sync import ClockAnchor, fit_clock_sync
from .clipping import MAX_CLIP_SECONDS
from .models import parse_datetime

FIELDS = [
    "source_id", "score", "peak_message_count", "peak_window_start",
    "clip_start_utc", "clip_end_utc", "start_seconds", "end_seconds",
    "duration_seconds", "renderable", "review_note",
]


def map_candidates_with_sync(
    candidates: list[dict[str, Any]], anchors: list[ClockAnchor],
    *, max_residual_seconds: float = 1.0, max_drift_ppm: float = 1000.0,
) -> list[dict[str, Any]]:
    """Map candidate chat timestamps through a validated, source-bound clock fit."""
    sync = fit_clock_sync(
        anchors, max_residual_seconds=max_residual_seconds,
        max_drift_ppm=max_drift_ppm,
    )
    mapped: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            raise ValueError(f"candidate {index} must be an object")
        source_id = str(candidate.get("source_id", "")).strip()
        if source_id != sync.source_id:
            raise ValueError(
                f"candidate {index} source_id does not match calibrated source {sync.source_id!r}"
            )
        try:
            start = parse_datetime(candidate["clip_start"])
            end = parse_datetime(candidate["clip_end"])
            start_seconds = sync.map_chat_time(start)
            end_seconds = sync.map_chat_time(end)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"candidate {index} cannot be mapped: {exc}") from exc
        if end <= start:
            raise ValueError(f"candidate {index} has clip_end <= clip_start")
        duration = end_seconds - start_seconds
        if duration <= 0:
            raise ValueError(f"candidate {index} maps to a non-positive media duration")

        renderable = True
        note = "ready for human review"
        if duration > MAX_CLIP_SECONDS:
            renderable = False
            note = f"duration exceeds the {MAX_CLIP_SECONDS:g}-second renderer limit"

        mapped.append({
            "source_id": source_id,
            "score": int(candidate.get("score", 0)),
            "peak_message_count": int(candidate.get("peak_message_count", 0)),
            "peak_window_start": str(candidate.get("peak_window_start", "")),
            "clip_start_utc": start.astimezone().isoformat(),
            "clip_end_utc": end.astimezone().isoformat(),
            "start_seconds": round(start_seconds, 3),
            "end_seconds": round(end_seconds, 3),
            "duration_seconds": round(duration, 3),
            "renderable": renderable,
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
        "Edit notes only. Review context, timing, and rights before rendering or publishing.", "",
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
        "", "## Calibration and review notes", "",
        "- Offsets come from at least three measured anchors for this exact source.",
        "- Mapping is rejected outside the calibrated time interval; no extrapolation is used.",
        "- Chat activity is a signal, not proof that a moment is entertaining or suitable.",
        "- No video is downloaded, rendered, uploaded, or published by this command.",
        "- Confirm creator permission and all applicable game, music, and third-party rights.", "",
    ])
    _write_texts_no_overwrite({
        csv_path: csv_buffer.getvalue(),
        markdown_path: "\n".join(lines),
    })
    return csv_path, markdown_path


def _load_anchors(path: Path) -> list[ClockAnchor]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get("anchors") if isinstance(payload, dict) else None
    if not isinstance(raw, list):
        raise ValueError("calibration JSON must contain an anchors array")
    anchors = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"anchor {index} must be an object")
        try:
            anchors.append(ClockAnchor(
                source_id=str(item["source_id"]),
                chat_time=parse_datetime(item["chat_time"]),
                media_seconds=item["media_seconds"],
            ))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid anchor {index}: {exc}") from exc
    return anchors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create review-only clip offsets from measured chat/media calibration anchors."
    )
    parser.add_argument("plan", type=Path, help="JSON candidate plan containing a candidates array")
    parser.add_argument(
        "--calibration", required=True, type=Path,
        help="JSON file containing at least three measured {source_id, chat_time, media_seconds} anchors",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("clip_pack"))
    parser.add_argument("--max-residual-seconds", type=float, default=1.0)
    parser.add_argument("--max-drift-ppm", type=float, default=1000.0)
    args = parser.parse_args()
    try:
        payload = json.loads(args.plan.read_text(encoding="utf-8"))
        candidates = payload.get("candidates") if isinstance(payload, dict) else None
        if not isinstance(candidates, list):
            raise ValueError("plan must contain a candidates array")
        anchors = _load_anchors(args.calibration)
        rows = map_candidates_with_sync(
            candidates, anchors,
            max_residual_seconds=args.max_residual_seconds,
            max_drift_ppm=args.max_drift_ppm,
        )
        csv_path, markdown_path = write_clip_pack(rows, args.output_dir)
        ready = sum(1 for row in rows if row["renderable"])
        print(f"Wrote {len(rows)} candidate(s), {ready} review-ready: {csv_path}, {markdown_path}")
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Clip pack stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
