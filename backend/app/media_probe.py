"""Read metadata from a local media file using ffprobe, never a URL."""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    duration_seconds: float
    format_name: str


def probe_media(path: str | Path, *, ffprobe_binary: str = "ffprobe") -> MediaInfo:
    """Return validated duration metadata for an existing local media file."""
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"local media file does not exist: {source}")
    command = [
        ffprobe_binary, "-v", "error", "-show_entries",
        "format=duration,format_name:stream=codec_type", "-of", "json", str(source),
    ]
    try:
        result = subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"ffprobe executable not found: {ffprobe_binary}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ffprobe metadata inspection timed out") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError((exc.stderr or "ffprobe failed").strip()) from exc
    try:
        payload = json.loads(result.stdout)
        media_format = payload["format"]
        duration = float(media_format["duration"])
        format_name = str(media_format.get("format_name", "unknown"))
        streams = payload.get("streams", [])
        if not isinstance(streams, list) or not any(
            isinstance(stream, dict) and stream.get("codec_type") == "video"
            for stream in streams
        ):
            raise ValueError("local media file does not contain a video stream")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and "does not contain a video stream" in str(exc):
            raise
        raise ValueError("ffprobe returned incomplete or invalid media metadata") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("media duration must be finite and positive")
    return MediaInfo(source, duration, format_name)
