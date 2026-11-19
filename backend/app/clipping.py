"""Local-only FFmpeg clipping with rights and collision-safe output handling."""

from __future__ import annotations

import math
import os
import subprocess
import tempfile
from pathlib import Path

from .media_probe import probe_media


MAX_CLIP_SECONDS = 180.0


class ClipRenderError(RuntimeError):
    """Raised when FFmpeg cannot produce or safely publish a valid clip."""


def render_clip(
    input_path: str | Path,
    output_path: str | Path,
    start_seconds: float,
    end_seconds: float,
    *,
    rights_confirmed: bool,
    ffmpeg_binary: str = "ffmpeg",
    ffprobe_binary: str = "ffprobe",
    vertical: bool = False,
) -> Path:
    """Render and probe a bounded MP4 before publishing it without overwriting.

    Vertical mode creates a 1080x1920 canvas with a blurred, cover-scaled
    background and the complete source frame fitted in front. The temporary
    output is not published unless ffprobe confirms a readable video stream
    and a duration close to the requested clip interval.
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
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"output already exists: {destination}")
    if not math.isfinite(start_seconds) or not math.isfinite(end_seconds):
        raise ValueError("clip bounds must be finite numbers")
    if start_seconds < 0 or end_seconds <= start_seconds:
        raise ValueError("clip bounds must satisfy 0 <= start < end")
    duration = end_seconds - start_seconds
    if duration > MAX_CLIP_SECONDS:
        raise ValueError(f"clip duration cannot exceed {MAX_CLIP_SECONDS:g} seconds")

    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}-", suffix=".mp4", dir=destination.parent
    )
    os.close(descriptor)
    temporary_output = Path(temporary_name)
    temporary_output.unlink()

    command = [
        ffmpeg_binary,
        "-nostdin",
        "-hide_banner",
        "-loglevel", "error",
        "-n",
        "-ss", f"{start_seconds:.3f}",
        "-i", str(source),
        "-t", f"{duration:.3f}",
    ]

    if vertical:
        filter_graph = (
            "[0:v]split=2[bg][fg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=20:10[bg];"
            "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]"
        )
        command.extend(["-filter_complex", filter_graph])

    command.extend([
        "-map", "[v]" if vertical else "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
    ])
    if vertical:
        command.extend(["-pix_fmt", "yuv420p"])
    command.extend([
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(temporary_output),
    ])

    try:
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)
        except FileNotFoundError as exc:
            raise ClipRenderError(f"FFmpeg executable not found: {ffmpeg_binary}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ClipRenderError("FFmpeg clip render timed out") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "").strip()
            raise ClipRenderError(detail or "FFmpeg failed to render the clip") from exc

        if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
            raise ClipRenderError("FFmpeg completed without creating a valid output file")

        try:
            output_info = probe_media(temporary_output, ffprobe_binary=ffprobe_binary)
        except (OSError, RuntimeError, ValueError) as exc:
            raise ClipRenderError(f"FFprobe could not verify the rendered MP4: {exc}") from exc

        # Allow small container/frame-timestamp rounding differences while
        # rejecting truncated or unexpectedly extended output.
        duration_tolerance = max(0.25, min(1.0, duration * 0.02))
        if abs(output_info.duration_seconds - duration) > duration_tolerance:
            raise ClipRenderError(
                "rendered MP4 duration does not match the requested clip "
                f"({output_info.duration_seconds:.3f}s reported, {duration:.3f}s expected)"
            )

        try:
            os.link(temporary_output, destination)
        except FileExistsError:
            raise FileExistsError(
                f"output was created by another render: {destination}; existing file preserved"
            ) from None
        except OSError as exc:
            raise ClipRenderError(
                "could not safely publish the clip without overwriting an existing output"
            ) from exc
    finally:
        temporary_output.unlink(missing_ok=True)

    return destination
