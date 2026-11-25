""""Read-only FFprobe preflight for exactly one owner-selected video file.

This module never enumerates directories, renders media, authenticates, uploads,
publishes, deletes, or modifies the selected video.
"""
from __future__ import annotations

import argparse
import json
import math
import mimetypes
import subprocess
import sys
from pathlib import Path
from typing import Any

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mpeg", ".mpg"}
PROBE_TIMEOUT_SECONDS = 30


def inspect_one_video(video_path: str | Path, *, ffprobe_binary: str = "ffprobe") -> dict[str, Any]:
    """Return one PASS/FAIL report for the exact file selected by the owner."""
    path = Path(video_path).expanduser()
    result: dict[str, Any] = {
        "selected_file": str(path),
        "status": "FAIL",
        "size_bytes": None,
        "duration_seconds": None,
        "format_name": None,
        "video_streams": [],
        "error": None,
        "processing_started": False,
        "upload_performed": False,
        "publishing_enabled": False,
        "manual_review_required": True,
    }
    try:
        if path.is_symlink():
            raise ValueError("symbolic links are not accepted as media inputs")
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            raise ValueError("selected file does not have a supported video extension")
        before = path.stat()
        if not path.is_file():
            raise ValueError("selected path is not a regular file")
        if before.st_size <= 0:
            raise ValueError("selected video file is empty")
        result["size_bytes"] = before.st_size

        command = [
            ffprobe_binary, "-v", "error", "-show_entries",
            "format=duration,format_name:stream=codec_type,codec_name,width,height",
            "-of", "json", str(path),
        ]
        try:
            probe = subprocess.run(
                command, check=True, capture_output=True, text=True,
                timeout=PROBE_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(f"ffprobe executable not found: {ffprobe_binary}") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("ffprobe timed out while inspecting the selected video") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError((exc.stderr or "ffprobe rejected the selected video").strip()) from exc

        try:
            payload = json.loads(probe.stdout)
            if not isinstance(payload, dict):
                raise ValueError("ffprobe root value must be an object")
            media_format = payload.get("format")
            if not isinstance(media_format, dict):
                raise ValueError("ffprobe format metadata must be an object")
            raw_duration = media_format.get("duration")
            if isinstance(raw_duration, bool) or raw_duration is None:
                raise ValueError("ffprobe duration must be a number or numeric string")
            duration = float(raw_duration)
            streams = payload.get("streams", [])
            if not isinstance(streams, list) or any(not isinstance(stream, dict) for stream in streams):
                raise ValueError("ffprobe stream metadata must be a list of objects")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError("ffprobe returned incomplete or invalid metadata") from exc

        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("duration must be finite and greater than zero")
        video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
        if not video_streams:
            raise ValueError("selected file has no video stream")

        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (
            after.st_size, after.st_mtime_ns, after.st_ino
        ):
            raise RuntimeError("selected file changed while it was being inspected")

        mime_type, _ = mimetypes.guess_type(path.name)
        result.update({
            "status": "PASS",
            "duration_seconds": duration,
            "format_name": str(media_format.get("format_name", "unknown")),
            "mime_type": mime_type or "unknown",
            "video_streams": [
                {
                    "codec": str(stream.get("codec_name", "unknown")),
                    "width": stream.get("width"),
                    "height": stream.get("height"),
                }
                for stream in video_streams
            ],
        })
    except (OSError, ValueError, RuntimeError) as exc:
        result["error"] = str(exc)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect exactly one selected local video with FFprobe; no processing or upload."
    )
    parser.add_argument("video", type=Path, help="One selected local video file.")
    parser.add_argument("--output", type=Path, default=Path("single_video_preflight.json"))
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()

    report = inspect_one_video(args.video, ffprobe_binary=args.ffprobe)
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except OSError as exc:
        print(f"Preflight report could not be written: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
