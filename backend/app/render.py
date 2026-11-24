"""Local, review-only FFmpeg renderer for explicitly authorized media files."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


MAX_CLIP_SECONDS = 180


class RenderError(RuntimeError):
    """Raised when a local clip cannot be rendered safely."""


def render_clip(
    input_path: Path,
    output_path: Path,
    *,
    start_seconds: float,
    duration_seconds: float,
    rights_confirmed: bool,
    ffmpeg: str = "ffmpeg",
    timeout_seconds: int = 300,
) -> Path:
    """Render a local clip. This function never downloads or publishes media."""
    if not rights_confirmed:
        raise PermissionError("explicit confirmation of media rights is required")
    if start_seconds < 0:
        raise ValueError("start_seconds cannot be negative")
    if duration_seconds <= 0 or duration_seconds > MAX_CLIP_SECONDS:
        raise ValueError(f"duration_seconds must be between 0 and {MAX_CLIP_SECONDS}")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    source = Path(input_path).expanduser()
    target = Path(output_path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"input media file does not exist: {source}")
    if source.resolve() == target.resolve():
        raise ValueError("output path must differ from the input path")
    if target.suffix.lower() != ".mp4":
        raise ValueError("output file must use the .mp4 extension")
    if not target.parent.is_dir():
        raise FileNotFoundError(f"output directory does not exist: {target.parent}")
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {target}")

    executable = shutil.which(ffmpeg)
    if executable is None:
        raise RenderError(f"FFmpeg executable not found: {ffmpeg}")

    # Reserve a unique temporary filename in the destination filesystem.
    # Publish it to the requested path only after FFmpeg succeeds.
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{target.stem}.", suffix=".mp4", dir=target.parent, delete=False
    )
    temporary = Path(handle.name)
    handle.close()

    command = [
        executable,
        "-hide_banner",
        "-loglevel", "error",
        "-nostdin",
        "-y",
        "-ss", str(start_seconds),
        "-i", str(source),
        "-t", str(duration_seconds),
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(temporary),
    ]

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or "no FFmpeg error details").strip()
            raise RenderError(f"FFmpeg failed: {detail[-1000:]}")
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RenderError("FFmpeg reported success but produced no usable output")

        # os.link is atomic and fails rather than overwriting a path created
        # concurrently by another process.
        os.link(temporary, target)
        return target
    except subprocess.TimeoutExpired as exc:
        raise RenderError("FFmpeg timed out; temporary output was removed") from exc
    except OSError as exc:
        raise RenderError(f"FFmpeg could not complete the render: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)
