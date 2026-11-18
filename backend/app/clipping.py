"""Local-only FFmpeg clip rendering for media the operator is authorized to use."""

from __future__ import annotations

import math
import subprocess
from pathlib import Path


MAX_CLIP_SECONDS = 180.0


class ClipRenderError(RuntimeError):
    """Raised when FFmpeg cannot produce a valid clip."""


def render_clip(
    input_path: str | Path,
    output_path: str | Path,
    start_seconds: float,
    end_seconds: float,
    *,
    rights_confirmed: bool,
    ffmpeg_binary: str = "ffmpeg",
) -> Path:
    """Render a bounded MP4 from a local file; never accepts remote URLs.

    The caller must confirm that the input media is owned or authorized for
    processing. This flag is an application guardrail, not legal verification.
    """
    if not rights_confirmed:
        raise PermissionError("media processing requires explicit rights confirmation")

    source = Path(input_path).expanduser().resolve()
    destination = Path(output_path).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(f"input media file does not exist: {source}")
    if source == destination:
        raise ValueError("output path must differ from input path")
    if destination.suffix.lower() != ".mp4":
        raise ValueError("output path must use the .mp4 extension")
    if destination.exists():
        raise FileExistsError(f"output already exists: {destination}")
    if not math.isfinite(start_seconds) or not math.isfinite(end_seconds):
        raise ValueError("clip bounds must be finite numbers")
    if start_seconds < 0 or end_seconds <= start_seconds:
        raise ValueError("clip bounds must satisfy 0 <= start < end")
    duration = end_seconds - start_seconds
    if duration > MAX_CLIP_SECONDS:
        raise ValueError(f"clip duration cannot exceed {MAX_CLIP_SECONDS:g} seconds")

    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg_binary,
        "-nostdin",
        "-hide_banner",
        "-loglevel", "error",
        "-n",
        "-ss", f"{start_seconds:.3f}",
        "-i", str(source),
        "-t", f"{duration:.3f}",
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(destination),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)
    except FileNotFoundError as exc:
        raise ClipRenderError(f"FFmpeg executable not found: {ffmpeg_binary}") from exc
    except subprocess.TimeoutExpired as exc:
        destination.unlink(missing_ok=True)
        raise ClipRenderError("FFmpeg clip render timed out") from exc
    except subprocess.CalledProcessError as exc:
        destination.unlink(missing_ok=True)
        detail = (exc.stderr or "").strip()
        raise ClipRenderError(detail or "FFmpeg failed to render the clip") from exc

    if not destination.is_file() or destination.stat().st_size == 0:
        destination.unlink(missing_ok=True)
        raise ClipRenderError("FFmpeg completed without creating a valid output file")

    return destination
