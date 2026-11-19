"""Batch-render reviewed candidates from a local, rights-authorized media manifest."""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from .media_probe import probe_media
from .media_sync import ClockSync, candidate_media_bounds, render_candidate
from .models import CandidateMoment, parse_datetime

def _candidate(item: dict[str, Any]) -> CandidateMoment:
    return CandidateMoment(
        source_id=str(item["source_id"]),
        peak_window_start=parse_datetime(item["peak_window_start"]),
        clip_start=parse_datetime(item["clip_start"]),
        clip_end=parse_datetime(item["clip_end"]),
        peak_message_count=int(item["peak_message_count"]),
        baseline_average=float(item["baseline_average"]),
        score=int(item["score"]),
        explanation=str(item.get("explanation", "")),
    )

def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-_")
    return cleaned[:60] or "candidate"

def render_manifest(manifest_path: Path, output_dir: Path, *, rights_confirmed: bool,
                    ffprobe_binary: str = "ffprobe", ffmpeg_binary: str = "ffmpeg") -> dict[str, Any]:
    if not rights_confirmed:
        raise PermissionError("batch rendering requires --confirm-rights")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    media_path = Path(payload["media_path"]).expanduser().resolve()
    media = probe_media(media_path, ffprobe_binary=ffprobe_binary)
    sync_data = payload["clock_sync"]
    sync = ClockSync(
        chat_minus_media_seconds=float(sync_data["chat_minus_media_seconds"]),
        uncertainty_seconds=float(sync_data["uncertainty_seconds"]),
        measured_at=parse_datetime(sync_data["measured_at"]),
        method=str(sync_data["method"]),
    )
    media_start = parse_datetime(payload["media_start_utc"])
    candidates = payload["candidates"]
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("manifest must contain a non-empty candidates list")
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for index, raw in enumerate(candidates, start=1):
        candidate = _candidate(raw)
        bounds = candidate_media_bounds(candidate, sync, media_start, media.duration_seconds)
        stem = f"{index:03d}-{_safe_name(candidate.source_id)}-{candidate.peak_window_start.strftime('%Y%m%dT%H%M%S')}"
        target = output_dir / f"{stem}.mp4"
        if target.exists() or target.is_symlink():
            results.append({"candidate": stem, "status": "skipped_existing", "output": str(target)})
            continue
        try:
            rendered = render_candidate(
                candidate, sync, media.path, target,
                media_start_utc=media_start,
                media_duration_seconds=media.duration_seconds,
                rights_confirmed=True, ffmpeg_binary=ffmpeg_binary,
            )
            results.append({"candidate": stem, "status": "rendered",
                            "output": str(rendered), "bounds": bounds.to_dict(),
                            "review_status": "needs_review"})
        except (ValueError, PermissionError, FileExistsError, RuntimeError, OSError) as exc:
            results.append({"candidate": stem, "status": "failed", "error": str(exc)})
    report = {
        "media": media.to_dict(),
        "clock_sync": {"chat_minus_media_seconds": sync.chat_minus_media_seconds,
                       "uncertainty_seconds": sync.uncertainty_seconds,
                       "measured_at": sync.measured_at.isoformat(), "method": sync.method},
        "rendered_count": sum(x["status"] == "rendered" for x in results),
        "failed_count": sum(x["status"] == "failed" for x in results),
        "results": results,
        "publishing_enabled": False,
    }
    report_path = output_dir / "review_manifest.json"
    if report_path.exists() or report_path.is_symlink():
        raise FileExistsError(f"review manifest already exists: {report_path}")
    fd, temp_name = tempfile.mkstemp(prefix=".review-", suffix=".json", dir=output_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temp_name, report_path)
    finally:
        Path(temp_name).unlink(missing_ok=True)
    return report

def main() -> int:
    parser = argparse.ArgumentParser(description="Batch render authorized local-media clip candidates.")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("review_clips"))
    parser.add_argument("--confirm-rights", action="store_true",
                        help="confirm that the local media is authorized for processing")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    try:
        report = render_manifest(args.manifest, args.output_dir,
                                 rights_confirmed=args.confirm_rights,
                                 ffprobe_binary=args.ffprobe, ffmpeg_binary=args.ffmpeg)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, PermissionError, RuntimeError) as exc:
        print(f"Batch render stopped: {exc}", file=sys.stderr)
        return 2
    print(f"Rendered {report['rendered_count']} clip(s); failed {report['failed_count']}.")
    return 0 if report["failed_count"] == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
