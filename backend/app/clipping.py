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


def _fsync_parent_directory(path: str | Path) -> None:
    """Persist a newly published output name where directory fsync is supported."""
    if os.name == "nt":
        return
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    descriptor = os.open(Path(path).parent, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


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
    if type(rights_confirmed) is not bool:
        raise TypeError("rights_confirmed must be an explicit boolean")
    if rights_confirmed is not True:
        raise PermissionError("media processing requires explicit rights confirmation")
    if not isinstance(ffmpeg_binary, str) or not ffmpeg_binary.strip():
        raise ValueError("ffmpeg_binary must be a non-empty executable name or path")
    if "\x00" in ffmpeg_binary:
        raise ValueError("ffmpeg_binary must not contain NUL characters")
    for name, value in (("input_path", input_path), ("output_path", output_path)):
        if not isinstance(value, (str, Path)):
            raise ValueError(f"{name} must be a non-empty string or pathlib.Path")
        if isinstance(value, str) and not value.strip():
            raise ValueError(f"{name} must be a non-empty string or pathlib.Path")

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

    def source_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int, int]:
        return (
            metadata.st_dev, metadata.st_ino, metadata.st_size,
            metadata.st_mtime_ns, metadata.st_ctime_ns, stat.S_IFMT(metadata.st_mode),
        )

    validated_source_identity = source_identity(source_metadata)
    if validated_source_identity != source_identity(resolved_metadata):
        raise RuntimeError("selected media path changed during source validation")

    requested_destination = Path(output_path).expanduser()
    # Resolve only the parent directory. Resolving the final component can
    # follow a dangling symlink inserted after the check above and redirect the
    # new render outside the requested output path. Keep the final name lexical:
    # os.link() will then fail safely if a symlink appears before publication.
    if requested_destination.is_symlink():
        raise FileExistsError(f"output path is a symbolic link: {requested_destination}")
    destination_parent = requested_destination.parent.resolve()
    destination = destination_parent / requested_destination.name
    if destination.is_symlink():
        raise FileExistsError(f"output path is a symbolic link: {destination}")

    if source == destination:
        raise ValueError("output path must differ from input path")
    if destination.suffix.lower() != ".mp4":
        raise ValueError("output path must use the .mp4 extension")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f"output already exists: {destination}")
    # bool is a subclass of int in Python, so math.isfinite(True) succeeds.
    # Reject booleans explicitly rather than silently treating them as 1s/0s.
    if isinstance(start_seconds, bool) or isinstance(end_seconds, bool):
        raise ValueError("clip bounds must be numeric values, not booleans")
    try:
        bounds_are_finite = math.isfinite(start_seconds) and math.isfinite(end_seconds)
    except (TypeError, OverflowError) as exc:
        raise ValueError("clip bounds must be finite numeric values") from exc
    if not bounds_are_finite:
        raise ValueError("clip bounds must be finite numeric values")
    if start_seconds < 0 or end_seconds <= start_seconds:
        raise ValueError("clip bounds must satisfy 0 <= start < end")
    duration = end_seconds - start_seconds
    if duration > MAX_CLIP_SECONDS:
        raise ValueError(f"clip duration cannot exceed {MAX_CLIP_SECONDS:g} seconds")

    destination.parent.mkdir(parents=True, exist_ok=True)
    # Keep FFmpeg's staging path inside a private directory. Unlinking a
    # mkstemp placeholder before FFmpeg opens it creates a pathname race in a
    # shared output directory, even when the filename was initially unique.
    temporary_directory = tempfile.TemporaryDirectory(
        prefix=f".{destination.stem}-", dir=destination.parent
    )
    temporary_output = Path(temporary_directory.name) / "render.mp4"

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
        # Preserve the full source frame on a 9:16 canvas without cropping HUD/gameplay.
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(temporary_output),
    ]

    # Allow slow local CPUs proportionally more time for longer clips. The cap
    # keeps a stalled encoder from running indefinitely; short clips retain a
    # bounded three-minute timeout.
    ffmpeg_timeout_seconds = min(1800, max(180, math.ceil(duration * 10)))

    try:
        # Re-check the selected pathname immediately before FFmpeg opens it.
        # This narrows the preflight-to-render replacement window and rejects
        # a symlink or non-regular replacement instead of following it.
        current_source = requested_source.lstat()
        if (
            not stat.S_ISREG(current_source.st_mode)
            or source_identity(current_source) != validated_source_identity
        ):
            raise RuntimeError("selected media path changed after source validation")
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, timeout=ffmpeg_timeout_seconds)
        except FileNotFoundError as exc:
            raise ClipRenderError(f"FFmpeg executable not found: {ffmpeg_binary}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ClipRenderError("FFmpeg clip render timed out") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "").strip()
            raise ClipRenderError(detail or "FFmpeg failed to render the clip") from exc

        # Detect in-place edits while FFmpeg was reading the source. A
        # stable inode alone is insufficient: writers can change bytes without
        # replacing the pathname. Never publish a render from a changing input.
        try:
            completed_source = requested_source.lstat()
        except OSError as exc:
            raise ClipRenderError(
                "selected media path disappeared or changed during FFmpeg rendering; output was not published"
            ) from exc
        if (
            not stat.S_ISREG(completed_source.st_mode)
            or source_identity(completed_source) != validated_source_identity
        ):
            raise ClipRenderError(
                "selected media file changed during FFmpeg rendering; output was not published"
            )

        if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
            raise ClipRenderError("FFmpeg completed without creating a valid output file")

        # Make the completed media bytes durable before exposing the final
        # destination name. A successful FFmpeg exit alone does not guarantee
        # that buffered file contents have reached stable storage.
        try:
            with temporary_output.open("r+b") as rendered_file:
                os.fsync(rendered_file.fileno())
        except OSError as exc:
            raise ClipRenderError(
                f"rendered clip could not be synchronized before publication: {exc}"
            ) from exc

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

        # The hard link is now visible. Persist its directory entry before
        # returning success; if this fails, preserve the output and surface an
        # explicit error so the caller records that manual inspection is needed.
        try:
            _fsync_parent_directory(destination)
        except OSError as exc:
            raise ClipRenderError(
                "clip was published but its parent directory could not be synchronized; "
                f"output is preserved for inspection at {destination}: {exc}"
            ) from exc
    finally:
        temporary_directory.cleanup()

    return destination
