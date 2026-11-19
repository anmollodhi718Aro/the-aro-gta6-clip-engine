"""Post-render verification for locally generated MP4 files."""

from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RenderedMediaInfo:
    path: Path
    duration_seconds: float
    width: int
    height: int
    has_audio: bool


def verify_rendered_media(
    path: str | Path,
    *,
    expected_duration_seconds: float,
    vertical: bool = False,
    ffprobe_binary: str = "ffprobe",
) -> RenderedMediaInfo:
    """Verify a non-empty MP4 has a readable video stream and expected layout/duration."""
    output = Path(path).expanduser().resolve()
    if not output.is_file() or output.stat().st_size <= 0:
        raise ValueError("rendered output is missing or empty")
    if (
        isinstance(expected_duration_seconds, bool)
        or not isinstance(expected_duration_seconds, (int, float))
        or not math.isfinite(expected_duration_seconds)
        or expected_duration_seconds <= 0
    ):
        raise ValueError("expected render duration must be finite and positive")

    command = [
        ffprobe_binary,
        "-v", "error",
        "-show_entries", "format=duration:stream=codec_type,width,height",
        "-of", "json",
        str(output),
    ]
    try:
        result = subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=30
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"ffprobe executable not found: {ffprobe_binary}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ffprobe output verification timed out") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        raise RuntimeError(detail or "ffprobe could not read rendered output") from exc

    try:
        payload = json.loads(result.stdout)
        duration = float(payload["format"]["duration"])
        streams = payload["streams"]
        video = next(
            stream for stream in streams
            if isinstance(stream, dict) and stream.get("codec_type") == "video"
        )
        width = int(video["width"])
        height = int(video["height"])
        has_audio = any(
            isinstance(stream, dict) and stream.get("codec_type") == "audio"
            for stream in streams
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, StopIteration) as exc:
        raise ValueError("ffprobe returned incomplete rendered-media metadata") from exc

    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("rendered output duration must be finite and positive")
    tolerance = min(0.5, max(0.05, expected_duration_seconds * 0.01))
    if abs(duration - expected_duration_seconds) > tolerance:
        raise ValueError(
            f"rendered output duration {duration:.3f}s differs from expected "
            f"{expected_duration_seconds:.3f}s (tolerance {tolerance:.3f}s)"
        )
    if width <= 0 or height <= 0:
        raise ValueError("rendered output has invalid video dimensions")
    if vertical and (width, height) != (1080, 1920):
        raise ValueError(f"vertical output must be 1080x1920, got {width}x{height}")

    return RenderedMediaInfo(output, duration, width, height, has_audio)
