"""Local-only FFmpeg clipping with rights and collision-safe output handling."""

from __future__ import annotations

import math
import os
import stat
import subprocess
import tempfile
from pathlib import Path


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
) -> Path:
    """Render a bounded MP4 from a local file without overwriting prior output.

    The caller must confirm that the input media is owned or authorized for
    processing. This flag is an application guardrail, not legal verification.
    FFmpeg writes to a unique temporary file on the destination filesystem.
    The verified file is published with an atomic hard link, which fails if
    another render creates the destination first.
    """
    if not rights_confirmed:
        raise PermissionError("media processing requires explicit rights confirmation")

    requested_source = Path(input_path).expanduser()
    # Validate the lexical source before resolve(): resolve() follows symlinks,
    # including links introduced after the read-only preflight has completed.
    try:
        source_metadata = requested_source.lstat()
    except OSError as exc:
        raise FileNotFoundError(f"input media file does not exist: {requested_source}") from exc
    if stat.S_ISLNK(source_metadata.st_mode):
        raise ValueError("symbolic links are not accepted as media inputs")
    if not stat.S_ISREG(source_metadata.st_mode):
        raise ValueError("selected media input must be a regular file")
    source = requested_source.resolve()
    resolved_metadata = source.stat()
    source_identity = (source_metadata.st_dev, source_metadata.st_ino)
    if source_identity != (resolved_metadata.st_dev, resolved_metadata.st_ino):
        raise RuntimeError("selected media path changed during source validation")

    requested_destination = Path(output_path).expanduser()
    # Check the lexical destination before resolve(): resolve() follows dangling
    # symlinks, which could redirect a supposedly new output outside this path.
    if requested_destination.is_symlink():
        raise FileExistsError(f"output path is a symbolic link: {requested_destination}")
    destination = requested_destination.resolve()

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
    # FFmpeg refuses to write to an existing path with -n, so reserve a unique
    # name with mkstemp and remove only that placeholder before invoking FFmpeg.
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
        "-map", "0:v:0",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(temporary_output),
    ]

    try:
        # Re-check the selected pathname immediately before FFmpeg opens it.
        # This narrows the preflight-to-render replacement window and rejects
        # a symlink or non-regular replacement instead of following it.
        current_source = requested_source.lstat()
        if (not stat.S_ISREG(current_source.st_mode)
                or (current_source.st_dev, current_source.st_ino) != source_identity):
            raise RuntimeError("selected media path changed after source validation")
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
