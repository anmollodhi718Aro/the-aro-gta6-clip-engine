"""Permission-gated rendering of operator-supplied local media files.

This module never downloads media or publishes rendered clips.
"""
from __future__ import annotations
import json
import math
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from .models import PermissionRecord

@dataclass(frozen=True)
class RenderResult:
    output_path: Path
    duration_seconds: float
    video_codec: str

def render_local_clip(
    input_path: Path, output_path: Path, *, source_id: str,
    permission: PermissionRecord, start_seconds: float, duration_seconds: float,
    confirmed: bool = False, ffmpeg_binary: str = "ffmpeg",
    ffprobe_binary: str = "ffprobe", timeout_seconds: int = 300,
) -> RenderResult:
    """Render a reviewed time range from a local file after an explicit rights gate."""
    if not confirmed:
        raise PermissionError("explicit local-render confirmation is required")
    if not source_id.strip() or source_id != permission.source_id:
        raise PermissionError("media source does not match the permission record")
    if not permission.allows("clip_media", datetime.now(timezone.utc)):
        raise PermissionError("clip_media permission is missing, expired, revoked, or out of scope")
    if not math.isfinite(start_seconds) or start_seconds < 0:
        raise ValueError("start_seconds must be a finite non-negative number")
    if not math.isfinite(duration_seconds) or not 0 < duration_seconds <= 600:
        raise ValueError("duration_seconds must be greater than 0 and at most 600")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    source = Path(input_path).expanduser().resolve(strict=True)
    destination = Path(output_path).expanduser().resolve()
    if not source.is_file():
        raise ValueError("input media must be a regular local file")
    if source == destination:
        raise ValueError("input and output paths must be different")
    if destination.suffix.lower() != ".mp4":
        raise ValueError("output must use the .mp4 extension")
    if not destination.parent.is_dir():
        raise ValueError("output directory must already exist")
    if destination.exists():
        raise FileExistsError("output already exists; refusing to overwrite")
    if shutil.which(ffmpeg_binary) is None or shutil.which(ffprobe_binary) is None:
        raise FileNotFoundError("FFmpeg and FFprobe must both be installed and available on PATH")
    # Render into a private temporary directory on the destination filesystem.
    # Publish with os.link(), which atomically fails if destination already exists.
    # Never clean up destination on failure: it may belong to another process.
    with tempfile.TemporaryDirectory(prefix=".aro-render-", dir=destination.parent) as staging:
        staged_output = Path(staging) / "render.mp4"
        command = [
            ffmpeg_binary, "-hide_banner", "-nostdin", "-v", "error", "-n",
            "-protocol_whitelist", "file", "-ss", f"{start_seconds:.3f}",
            "-i", str(source), "-t", f"{duration_seconds:.3f}",
            "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264",
            "-c:a", "aac", "-movflags", "+faststart", "-f", "mp4", str(staged_output),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"FFmpeg render failed: {completed.stderr[-1000:]}")
        probe = subprocess.run(
            [ffprobe_binary, "-v", "error", "-protocol_whitelist", "file",
             "-show_entries", "format=duration:stream=codec_type,codec_name",
             "-of", "json", str(staged_output)],
            capture_output=True, text=True, timeout=timeout_seconds, check=False,
        )
        if probe.returncode != 0:
            raise RuntimeError(f"FFprobe validation failed: {probe.stderr[-1000:]}")
        metadata = json.loads(probe.stdout)
        streams = metadata.get("streams", [])
        video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
        actual_duration = float(metadata.get("format", {}).get("duration", 0))
        if video is None or not math.isfinite(actual_duration) or actual_duration <= 0:
            raise RuntimeError("rendered file has no valid video stream or duration")
        if actual_duration > duration_seconds + 1.5:
            raise RuntimeError("rendered duration exceeds the requested clip window")
        os.link(staged_output, destination)
        return RenderResult(destination, actual_duration, str(video.get("codec_name", "unknown")))
