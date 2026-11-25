"""Inventory every local video file before any batch rendering.

This preflight is read-only: it never renders, uploads, deletes, or modifies media.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mpeg", ".mpg"}
PROBE_TIMEOUT_SECONDS = 30


def _probe_video(path: Path, ffprobe_binary: str) -> dict[str, Any]:
    command = [
        ffprobe_binary, "-v", "error", "-show_entries",
        "format=duration,format_name:stream=codec_type,codec_name,width,height",
        "-of", "json", str(path),
    ]
    try:
        result = subprocess.run(
            command, check=True, capture_output=True, text=True,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"ffprobe executable not found: {ffprobe_binary}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ffprobe timed out while inspecting this file") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "ffprobe rejected the media file").strip()
        raise RuntimeError(detail) from exc

    try:
        payload = json.loads(result.stdout)
        media_format = payload["format"]
        duration = float(media_format["duration"])
        streams = payload.get("streams", [])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("ffprobe returned incomplete or invalid metadata") from exc

    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration must be finite and greater than zero")
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    if not video_streams:
        raise ValueError("file has no video stream")

    return {
        "duration_seconds": duration,
        "format_name": str(media_format.get("format_name", "unknown")),
        "video_streams": [
            {
                "codec": str(stream.get("codec_name", "unknown")),
                "width": stream.get("width"),
                "height": stream.get("height"),
            }
            for stream in video_streams
        ],
    }


def inspect_media_directory(
    directory: str | Path,
    *,
    recursive: bool = True,
    ffprobe_binary: str = "ffprobe",
) -> dict[str, Any]:
    """Inspect all supported local video files; preserve per-file failures."""
    root = Path(directory).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"media directory does not exist: {root}")
    if root.is_symlink() or not root.is_dir():
        raise ValueError("media input must be a real directory, not a symlink")

    candidates: list[Path] = []
    traversal_errors: list[str] = []

    def on_walk_error(error: OSError) -> None:
        traversal_errors.append(str(error))

    if recursive:
        for current, dirs, files in os.walk(root, followlinks=False, onerror=on_walk_error):
            current_path = Path(current)
            symlink_dirs = sorted(name for name in dirs if (current_path / name).is_symlink())
            for name in symlink_dirs:
                skipped = (current_path / name).relative_to(root).as_posix()
                traversal_errors.append(
                    f"symbolic-link directory skipped (not traversed): {skipped}"
                )
            dirs[:] = sorted(name for name in dirs if name not in symlink_dirs)
            candidates.extend(current_path / name for name in files)
    else:
        try:
            candidates = [entry for entry in root.iterdir() if entry.is_file() or entry.is_symlink()]
        except OSError as exc:
            traversal_errors.append(str(exc))

    video_files = sorted(
        (path for path in candidates if path.suffix.lower() in VIDEO_EXTENSIONS),
        key=lambda path: path.relative_to(root).as_posix().casefold(),
    )
    results: list[dict[str, Any]] = []

    for path in video_files:
        relative = path.relative_to(root).as_posix()
        item: dict[str, Any] = {
            "path": relative,
            "status": "FAIL",
            "size_bytes": None,
            "duration_seconds": None,
            "format_name": None,
            "video_streams": [],
            "error": None,
        }
        try:
            if path.is_symlink():
                raise ValueError("symbolic links are not accepted as media inputs")
            before = path.stat()
            if not path.is_file():
                raise ValueError("candidate is not a regular file")
            item["size_bytes"] = before.st_size
            if before.st_size <= 0:
                raise ValueError("file is empty")
            metadata = _probe_video(path.resolve(), ffprobe_binary)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns, before.st_ino) != (
                after.st_size, after.st_mtime_ns, after.st_ino
            ):
                raise RuntimeError("file changed while it was being inspected")
            item.update(metadata)
            item["status"] = "PASS"
        except (OSError, ValueError, RuntimeError) as exc:
            item["error"] = str(exc)
        results.append(item)

    passed = sum(item["status"] == "PASS" for item in results)
    failed = len(results) - passed
    return {
        "schema_version": 1,
        "media_directory": str(root.resolve()),
        "recursive": recursive,
        "files_discovered": len(results),
        "passed": passed,
        "failed": failed,
        "traversal_errors": traversal_errors,
        "results": results,
        "processing_started": False,
        "publishing_enabled": False,
        "manual_review_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only inventory and FFprobe validation of every local video in a directory."
    )
    parser.add_argument("media_directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("media_inventory_report.json"))
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--top-level-only", action="store_true")
    args = parser.parse_args()

    try:
        report = inspect_media_directory(
            args.media_directory,
            recursive=not args.top_level_only,
            ffprobe_binary=args.ffprobe,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents accidentally replacing a prior report.
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
        print(
            f"Inventory: discovered={report['files_discovered']} "
            f"PASS={report['passed']} FAIL={report['failed']} "
            f"report={args.output}"
        )
        return 1 if report["failed"] or report["traversal_errors"] else 0
    except (OSError, ValueError) as exc:
        print(f"Media inventory stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
