"""Dry-run-first rendering for exactly one explicitly selected local video."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from .clipping import MAX_CLIP_SECONDS, render_clip
from .media_single_preflight import inspect_one_video


def render_selected_clip(
    video_path: str | Path,
    output_path: str | Path,
    start_seconds: float,
    end_seconds: float,
    *,
    execute: bool = False,
    rights_confirmed: bool = False,
    ffprobe_binary: str = "ffprobe",
    ffmpeg_binary: str = "ffmpeg",
) -> dict[str, Any]:
    """Plan or render one clip from one selected local video.

    No directory enumeration, batch processing, upload, or publishing occurs.
    A render requires both an explicit execution flag and rights confirmation.
    """
    source = Path(video_path).expanduser()
    destination = Path(output_path).expanduser()
    report: dict[str, Any] = {
        "status": "FAIL",
        "source_path": str(source),
        "output_path": str(destination),
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "processing_started": False,
        "upload_performed": False,
        "publishing_enabled": False,
    }

    preflight = inspect_one_video(source, ffprobe_binary=ffprobe_binary)
    report["source_preflight"] = preflight
    if preflight.get("status") != "PASS":
        report["error"] = "selected source did not pass single-video metadata preflight"
        return report

    if isinstance(start_seconds, bool) or isinstance(end_seconds, bool):
        report["error"] = "clip bounds must be finite numbers"
        return report
    try:
        start = float(start_seconds)
        end = float(end_seconds)
    except (TypeError, ValueError):
        report["error"] = "clip bounds must be finite numbers"
        return report
    if not math.isfinite(start) or not math.isfinite(end):
        report["error"] = "clip bounds must be finite numbers"
        return report
    if start < 0 or end <= start or end - start > MAX_CLIP_SECONDS:
        report["error"] = f"clip bounds must satisfy 0 <= start < end and duration <= {MAX_CLIP_SECONDS:g}s"
        return report

    duration = preflight.get("duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        report["error"] = "source preflight did not provide a valid media duration"
        return report
    if end > duration:
        report["error"] = "selected clip end exceeds the probed source duration"
        return report

    report["start_seconds"] = start
    report["end_seconds"] = end
    report["duration_seconds"] = end - start
    if not execute:
        report.update(status="PLANNED", message="single clip is valid; no rendering was started")
        return report
    if not rights_confirmed:
        report.update(status="BLOCKED", error="render execution requires --confirm-rights")
        return report

    try:
        report["processing_started"] = True
        rendered = render_clip(
            source,
            destination,
            start,
            end,
            rights_confirmed=True,
            ffmpeg_binary=ffmpeg_binary,
        )
        rendered_preflight = inspect_one_video(rendered, ffprobe_binary=ffprobe_binary)
        report["rendered_preflight"] = rendered_preflight
        if rendered_preflight.get("status") != "PASS":
            report.update(status="FAIL", error="rendered output failed FFprobe verification")
            return report
        rendered_duration = rendered_preflight.get("duration_seconds")
        if (isinstance(rendered_duration, bool)
                or not isinstance(rendered_duration, (int, float))
                or not math.isfinite(rendered_duration)
                or rendered_duration <= 0
                or rendered_duration > (end - start) + 1.0):
            report.update(status="FAIL", error="rendered output duration is outside the expected clip bounds")
            return report
        report.update(
            status="RENDERED",
            output_path=str(rendered),
            rendered_duration_seconds=float(rendered_duration),
            message="one local clip rendered and passed FFprobe verification; manual review required",
        )
    except (OSError, PermissionError, RuntimeError, ValueError) as exc:
        report.update(status="FAIL", error=str(exc))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or render exactly one explicitly selected local video clip."
    )
    parser.add_argument("video", type=Path, help="One selected local authorized video file.")
    parser.add_argument("--start", type=float, required=True, help="Clip start time in seconds.")
    parser.add_argument("--end", type=float, required=True, help="Clip end time in seconds.")
    parser.add_argument("--output", type=Path, default=Path("rendered_clips/single_selected_clip.mp4"))
    parser.add_argument("--report", type=Path, default=Path("single_clip_render_report.json"))
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--execute", action="store_true", help="Actually render; default is a dry-run plan.")
    parser.add_argument("--confirm-rights", action="store_true", help="Confirm processing rights for this exact selected source.")
    args = parser.parse_args()

    report = render_selected_clip(
        args.video,
        args.output,
        args.start,
        args.end,
        execute=args.execute,
        rights_confirmed=args.confirm_rights,
        ffprobe_binary=args.ffprobe,
        ffmpeg_binary=args.ffmpeg,
    )
    try:
        report_path = args.report.expanduser()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except OSError as exc:
        print(f"Report could not be written without overwrite: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] in {"PLANNED", "RENDERED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
