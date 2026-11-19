"""Local FFmpeg clip rendering for media the operator is authorized to use.

This module performs no downloads, scraping, or publishing. It only reads a
local file after an explicit authorization attestation and permission check.
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .models import PermissionRecord


class ClipError(RuntimeError):
    """Raised when a local clip cannot safely be rendered."""


def probe_duration(input_path: Path, ffprobe_bin: str = "ffprobe") -> float:
    result = subprocess.run(
        [
            ffprobe_bin, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(input_path),
        ],
        check=True, capture_output=True, text=True, timeout=30,
    )
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise ClipError("ffprobe did not return a valid media duration") from exc
    if duration <= 0:
        raise ClipError("input media has no valid duration")
    return duration


def render_clip(
    input_path: Path,
    output_path: Path,
    start_seconds: float,
    duration_seconds: float,
    permission: PermissionRecord,
    *,
    confirm_authorized: bool = False,
    vertical: bool = False,
    ffmpeg_bin: str = "ffmpeg",
    ffprobe_bin: str = "ffprobe",
) -> Path:
    """Render one MP4 clip from an authorized local source file."""
    source = input_path.expanduser().resolve()
    destination = output_path.expanduser().resolve()

    if not confirm_authorized:
        raise PermissionError("pass --confirm-authorized only if you own or are licensed to use this footage")
    if not permission.allows("render_video", datetime.now(timezone.utc)):
        raise PermissionError("valid, unrevoked render_video permission is required")
    if not source.is_file():
        raise ClipError(f"input video does not exist: {source}")
    if source == destination:
        raise ClipError("output path must differ from input path")
    if destination.suffix.lower() != ".mp4":
        raise ClipError("output file must use the .mp4 extension")
    if destination.exists():
        raise ClipError("output already exists; choose a new filename")
    if start_seconds < 0 or duration_seconds <= 0:
        raise ClipError("start must be non-negative and duration must be positive")
    if duration_seconds > 600:
        raise ClipError("single-clip duration is limited to 600 seconds")

    media_duration = probe_duration(source, ffprobe_bin)
    if start_seconds >= media_duration or start_seconds + duration_seconds > media_duration:
        raise ClipError("requested clip range extends beyond the source video")

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-ss", str(start_seconds),
        "-i", str(source), "-t", str(duration_seconds),
        "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "23", "-c:a", "aac",
        "-movflags", "+faststart",
    ]
    if vertical:
        command.extend([
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        ])
    command.append(str(destination))

    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=1800)
    except FileNotFoundError as exc:
        raise ClipError("FFmpeg was not found; install FFmpeg and ensure it is on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()[-1200:]
        raise ClipError(f"FFmpeg failed: {detail or 'unknown encoding error'}") from exc
    return destination
