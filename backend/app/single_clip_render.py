"""Dry-run-first rendering for exactly one explicitly selected local video."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import stat
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .clipping import MAX_CLIP_SECONDS, render_clip
from .media_single_preflight import inspect_one_video



def _reject_nul_candidate_csv_lines(handle):
    """Reject binary NUL bytes while streaming the complete candidate CSV.

    DictReader accepts NUL characters as ordinary field content. Check each
    physical line before CSV parsing so headers, selected rows, unselected
    trailing rows, and multiline quoted fields all fail closed.
    """
    for line in handle:
        if "\x00" in line:
            raise csv.Error("NUL character found in candidate CSV")
        yield line


def load_selected_candidate(csv_path: str | Path, row_number: int) -> dict[str, Any]:
    """Load one explicitly numbered, review-ready candidate from a clip-pack CSV.

    Row numbers are one-based data rows (the header is not counted). This
    function only reads review metadata; it never selects or opens media.
    """
    if isinstance(row_number, bool) or not isinstance(row_number, int) or row_number < 1:
        raise ValueError("candidate row must be a positive one-based integer")
    if not isinstance(csv_path, (str, Path)) or (
        isinstance(csv_path, str) and not csv_path.strip()
    ):
        raise ValueError("candidate CSV path must be a non-empty string or pathlib.Path")
    try:
        path = Path(csv_path).expanduser()
        # A NUL in the filesystem path is not valid on supported platforms.
        # Reject it explicitly before open(), which otherwise raises a raw
        # ValueError outside the normal candidate-file read-error boundary.
        if "\x00" in str(path):
            raise ValueError("candidate CSV path must not contain NUL characters")
        # Accept an optional UTF-8 BOM from spreadsheet exports while keeping
        # the generated clip-pack CSV format unchanged.
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            # DictReader is permissive by default: malformed quoting may be
            # accepted, extra cells are stored under the None key, and short
            # rows silently receive None values. Make all three conditions
            # explicit failures, and parse the complete file so malformed
            # trailing rows cannot hide behind an earlier selected row.
            # Use a unique mapping key so a user-supplied CSV header cannot collide
            # with DictReader's overflow-cell bucket.
            extra_fields_key = object()
            reader = csv.DictReader(
                _reject_nul_candidate_csv_lines(handle),
                restkey=extra_fields_key,
                restval=None,
                strict=True,
            )
            required = {"source_id", "start_seconds", "end_seconds", "duration_seconds", "renderable"}
            headers = reader.fieldnames
            if not headers or not required.issubset(set(headers)):
                raise ValueError("candidate CSV is missing required review columns")
            if any(header is None or not str(header).strip() for header in headers) or len(headers) != len(set(headers)):
                raise ValueError("candidate CSV contains blank or duplicate column names")
            selected = None
            for number, row in enumerate(reader, start=1):
                if row.get(extra_fields_key) is not None:
                    raise ValueError(f"candidate row {number} has more values than its header")
                if any(row.get(column) is None for column in required):
                    raise ValueError(f"candidate row {number} is missing required values")
                if number == row_number:
                    selected = row
    except (OSError, csv.Error, UnicodeError, RuntimeError) as exc:
        raise ValueError(f"candidate CSV could not be read: {exc}") from exc
    if selected is None:
        raise ValueError(f"candidate row {row_number} does not exist")
    if str(selected.get("renderable", "")).strip().lower() != "true":
        raise ValueError(f"candidate row {row_number} is not marked renderable")
    source_id = str(selected.get("source_id", "")).strip()
    if not source_id:
        raise ValueError(f"candidate row {row_number} has no source_id")
    try:
        start = float(selected["start_seconds"])
        end = float(selected["end_seconds"])
        duration = float(selected["duration_seconds"])
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"candidate row {row_number} has invalid clip bounds") from exc
    if not all(math.isfinite(value) for value in (start, end, duration)):
        raise ValueError(f"candidate row {row_number} has non-finite clip bounds")
    if start < 0 or end <= start or end - start > MAX_CLIP_SECONDS:
        raise ValueError(f"candidate row {row_number} has clip bounds outside renderer limits")
    if duration <= 0 or abs((end - start) - duration) > 0.05:
        raise ValueError(f"candidate row {row_number} duration does not match its clip bounds")
    return {
        "row_number": row_number,
        "source_id": source_id,
        "start_seconds": start,
        "end_seconds": end,
        "duration_seconds": duration,
    }


def _validate_output_destination(source: Path, destination: Path) -> str | None:
    """Validate a new MP4 destination without following a destination symlink."""
    try:
        if destination.is_symlink():
            return "output path is a symbolic link; symbolic-link destinations are rejected"
        if source.resolve() == destination.resolve():
            return "output path must differ from the selected source"
        if destination.suffix.lower() != ".mp4":
            return "output path must use the .mp4 extension"
        if destination.exists() or destination.is_symlink():
            return "output already exists; existing files are never overwritten"
    except (OSError, RuntimeError, ValueError) as exc:
        # Path.resolve() can raise RuntimeError for symlink loops and ValueError
        # for malformed paths; report these as validation failures, not crashes.
        return f"output path could not be validated: {exc}"
    return None



def sha256_selected_source(path: str | Path) -> str:
    """Hash one selected regular file through a stable, non-following descriptor."""
    if not isinstance(path, (str, Path)) or (
        isinstance(path, str) and not path.strip()
    ):
        raise ValueError("selected source path must be a non-empty string or pathlib.Path")
    source = Path(path).expanduser()
    try:
        before_path = source.lstat()
        if stat.S_ISLNK(before_path.st_mode) or not stat.S_ISREG(before_path.st_mode):
            raise ValueError("selected source must be a regular non-symlink file")
        flags = os.O_RDONLY
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        # A path can be replaced between lstat() and open(). Nonblocking
        # open prevents a raced FIFO/device from hanging the inventory hash
        # before fstat() gets a chance to reject non-regular files.
        if hasattr(os, "O_NONBLOCK"):
            flags |= os.O_NONBLOCK
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(source, flags)
    except OSError as exc:
        raise ValueError(f"selected source could not be opened for hashing: {exc}") from exc

    try:
        before_fd = os.fstat(descriptor)
        identity = lambda item: (
            item.st_dev, item.st_ino, item.st_size,
            item.st_mtime_ns, item.st_ctime_ns, stat.S_IFMT(item.st_mode),
        )
        if not stat.S_ISREG(before_fd.st_mode) or identity(before_fd) != identity(before_path):
            raise ValueError("selected source changed while opening for hashing")
        digest = hashlib.sha256()
        bytes_read = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            bytes_read += len(chunk)
        after_fd = os.fstat(descriptor)
        after_path = source.lstat()
        if (
            identity(after_fd) != identity(before_fd)
            or identity(after_path) != identity(before_fd)
            or stat.S_ISLNK(after_path.st_mode)
            or bytes_read != before_fd.st_size
        ):
            raise ValueError("selected source changed while it was being hashed")
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def _selected_file_identity(path: Path) -> tuple[int, int, int, int, int, int]:
    """Return a stable identity for one regular, non-symlink selected file."""
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError("selected source must remain a regular non-symlink file")
    return (
        metadata.st_dev, metadata.st_ino, metadata.st_size,
        metadata.st_mtime_ns, metadata.st_ctime_ns, metadata.st_mode,
    )


def _rendered_output_identity(path: str | Path) -> tuple[int, int, int, int, int, int]:
    """Identify output inode and content-relevant metadata without following symlinks."""
    candidate = Path(path)
    metadata = candidate.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError("rendered output must be a regular non-symlink file")
    return (
        metadata.st_dev, metadata.st_ino, metadata.st_size,
        metadata.st_mtime_ns, metadata.st_ctime_ns, stat.S_IFMT(metadata.st_mode),
    )


def _sha256_verified_regular_file(path: str | Path) -> tuple[str, int, tuple[int, int, int, int, int, int]]:
    """Hash bytes read from one stable regular file without following symlinks."""
    candidate = Path(path)
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(candidate, flags)
    try:
        before = os.fstat(descriptor)
        before_path = candidate.lstat()
        identity = (
            before.st_dev, before.st_ino, before.st_size,
            before.st_mtime_ns, before.st_ctime_ns, stat.S_IFMT(before.st_mode),
        )
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before_path.st_mode)
            or identity != (
                before_path.st_dev, before_path.st_ino, before_path.st_size,
                before_path.st_mtime_ns, before_path.st_ctime_ns,
                stat.S_IFMT(before_path.st_mode),
            )
        ):
            raise ValueError("verified output must remain a regular non-symlink file")
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
        after = os.fstat(descriptor)
        after_path = candidate.lstat()
        if (
            (
                after.st_dev, after.st_ino, after.st_size,
                after.st_mtime_ns, after.st_ctime_ns, stat.S_IFMT(after.st_mode),
            ) != identity
            or after.st_size != before.st_size
            or after.st_mtime_ns != before.st_mtime_ns
            or after.st_ctime_ns != before.st_ctime_ns
            or after_path.st_dev != before.st_dev
            or after_path.st_ino != before.st_ino
            or stat.S_ISLNK(after_path.st_mode)
            or size != before.st_size
        ):
            raise RuntimeError("rendered output changed during SHA-256 verification")
        return digest.hexdigest(), size, identity
    finally:
        os.close(descriptor)


def _remove_unverified_output(path: str | Path, identity: tuple[int, int, int] | None) -> bool:
    """Decline automatic deletion when pathname identity cannot be unlinked atomically.

    A separate lstat() followed by unlink() has a replacement race: another
    process can swap the directory entry after the identity check, causing
    unlink() to remove a different file. Python's portable path APIs do not
    provide an inode-conditional unlink, so preserve the output for manual
    review rather than risk deleting a replacement.
    """
    return False



def _rendered_mp4_validation_error(preflight: dict[str, Any]) -> str | None:
    """Require the renderer's promised MP4 container and H.264 video stream."""
    format_names = preflight.get("format_name")
    if not isinstance(format_names, str) or "mp4" not in {
        item.strip().lower() for item in format_names.split(",")
    }:
        return "rendered output is not identified as an MP4 container"
    streams = preflight.get("video_streams")
    if not isinstance(streams, list) or not streams:
        return "rendered output has no verified video stream"
    # Validate every reported video stream, not only the first one. A
    # malformed secondary stream must not be hidden behind a valid first
    # stream when the report claims the complete output passed validation.
    for index, video in enumerate(streams):
        if not isinstance(video, dict):
            return f"rendered output video stream {index} metadata is invalid"
        if not isinstance(video.get("codec"), str) or video["codec"].strip().lower() != "h264":
            return "rendered output video codec is not H.264"
        for dimension in ("width", "height"):
            value = video.get(dimension)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                return f"rendered output has invalid video {dimension}"
        if video["width"] != 1080 or video["height"] != 1920:
            return (
                f"rendered output video stream {index} must be exactly "
                "1080x1920 portrait"
            )
    return None


def _validated_clip_bounds(start_seconds: Any, end_seconds: Any) -> tuple[float, float]:
    """Normalize finite numeric clip bounds before any source snapshot I/O."""
    if isinstance(start_seconds, bool) or isinstance(end_seconds, bool):
        raise ValueError("clip bounds must be finite numbers")
    try:
        start = float(start_seconds)
        end = float(end_seconds)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("clip bounds must be finite numbers") from exc
    if not math.isfinite(start) or not math.isfinite(end):
        raise ValueError("clip bounds must be finite numbers")
    if start < 0 or end <= start or end - start > MAX_CLIP_SECONDS:
        raise ValueError(
            f"clip bounds must satisfy 0 <= start < end and duration <= {MAX_CLIP_SECONDS:g}s"
        )
    return start, end


def _render_selected_clip_from_snapshot(
    video_path: str | Path,
    output_path: str | Path,
    start_seconds: float,
    end_seconds: float,
    *,
    execute: bool = False,
    rights_confirmed: bool = False,
    ffprobe_binary: str = "ffprobe",
    ffmpeg_binary: str = "ffmpeg",
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    """Plan or render one clip from one selected local video.

    No directory enumeration, batch processing, upload, or publishing occurs.
    A render requires both an explicit execution flag and rights confirmation.
    """
    source = Path(video_path).expanduser()
    destination = Path(output_path).expanduser()
    report: dict[str, Any] = {
        "status": "FAIL",
        "source_path": str(source),
        "output_path": str(destination),
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "processing_started": False,
        "source_identity_verified": False,
        "upload_performed": False,
        "publishing_enabled": False,
    }
    if type(execute) is not bool or type(rights_confirmed) is not bool:
        report["error"] = "execute and rights_confirmed must be explicit booleans"
        return report

    # Reject invalid bounds before filesystem identity checks or FFprobe work.
    try:
        start, end = _validated_clip_bounds(start_seconds, end_seconds)
    except ValueError as exc:
        report["error"] = str(exc)
        return report

    # An execution request without explicit rights confirmation must stop
    # before opening, hashing, probing, or snapshotting the selected media.
    # Path-only argument validation above does not inspect media contents.
    if execute and not rights_confirmed:
        report.update(
            status="BLOCKED",
            error="render execution requires --confirm-rights",
            message="execution was blocked before media inspection because rights confirmation was not supplied",
        )
        return report

    output_error = _validate_output_destination(source, destination)
    if output_error:
        report["error"] = output_error
        return report

    try:
        source_identity_before = _selected_file_identity(source)
    except (OSError, ValueError) as exc:
        report["error"] = f"selected source could not be safely identified: {exc}"
        return report

    try:
        preflight = inspect_one_video(source, ffprobe_binary=ffprobe_binary)
    except Exception as exc:
        report.update(
            source_preflight_error=f"{type(exc).__name__}: {exc}",
            source_inspection_required=True,
            error="selected source FFprobe preflight raised an exception",
            message=(
                "Source metadata verification could not be completed. "
                "Inspect the selected source and FFprobe availability before retrying; no render was started."
            ),
        )
        return report
    if not isinstance(preflight, dict):
        report.update(
            source_preflight_error=(
                "FFprobe returned malformed source metadata: expected an object, "
                f"received {type(preflight).__name__}"
            ),
            source_inspection_required=True,
            error="selected source FFprobe preflight returned malformed metadata",
            message=(
                "Source metadata verification returned an invalid result. "
                "Inspect the selected source and FFprobe availability before retrying; no render was started."
            ),
        )
        return report
    report["source_preflight"] = preflight
    if preflight.get("status") != "PASS":
        report["error"] = "selected source did not pass single-video metadata preflight"
        return report
    try:
        source_identity_after = _selected_file_identity(source)
    except (OSError, ValueError) as exc:
        report["error"] = f"selected source changed or became unsafe during preflight: {exc}"
        return report
    if source_identity_after != source_identity_before:
        report["error"] = "selected source changed during preflight; refusing to render a different file"
        return report
    report["source_identity_verified"] = True

    # Candidate dry-runs must bind their preflight report to the same trusted
    # source digest that was checked against the selected inventory row. The
    # CLI's earlier hash alone is insufficient: the path could be replaced
    # between that hash and FFprobe. Re-hash after preflight and require the
    # original file identity to remain unchanged throughout both operations.
    if not execute and expected_source_sha256 is not None:
        try:
            observed_sha256 = sha256_selected_source(source)
            identity_after_hash = _selected_file_identity(source)
        except (OSError, ValueError) as exc:
            report["error"] = f"selected source could not be re-verified after preflight: {exc}"
            return report
        if identity_after_hash != source_identity_after:
            report["error"] = "selected source changed between candidate hashing and preflight"
            return report
        if observed_sha256 != expected_source_sha256:
            report["error"] = "selected source SHA-256 no longer matches the trusted candidate inventory"
            return report
        report["expected_source_sha256"] = expected_source_sha256
        report["source_sha256"] = observed_sha256

    duration = preflight.get("duration_seconds")
    try:
        valid_duration = (
            not isinstance(duration, bool)
            and isinstance(duration, (int, float))
            and math.isfinite(duration)
            and duration > 0
        )
    except (OverflowError, TypeError, ValueError):
        # A huge integer can overflow during float conversion inside isfinite().
        # Treat malformed preflight metadata as a deterministic validation failure.
        valid_duration = False
    if not valid_duration:
        report["error"] = "source preflight did not provide a valid media duration"
        return report
    if end > duration:
        report["error"] = "selected clip end exceeds the probed source duration"
        return report

    report["start_seconds"] = start
    report["end_seconds"] = end
    report["duration_seconds"] = end - start
    if not execute:
        report.update(status="PLANNED", message="single clip is valid; no rendering was started")
        return report
    if not rights_confirmed:
        report.update(status="BLOCKED", error="render execution requires --confirm-rights")
        return report

    try:
        if _selected_file_identity(source) != source_identity_after:
            report["error"] = "selected source changed after preflight; refusing to render a different file"
            return report
        # Entering render_clip does not prove FFmpeg was launched: that
        # function performs additional path and bounds validation first.
        # Keep the state unknown until render_clip returns successfully.
        report["processing_started"] = None
        try:
            rendered = render_clip(
                source,
                destination,
                start,
                end,
                rights_confirmed=True,
                ffmpeg_binary=ffmpeg_binary,
            )
        except Exception as exc:
            # render_clip may have atomically linked the completed output before
            # a later staging-directory cleanup error. Its exception therefore
            # does not prove that the destination is absent or safe to retry.
            report.update(
                status="FAIL",
                error=f"render invocation did not return a verified output path: {exc}",
                output_inspection_required=True,
                message=(
                    "Render invocation failed after it may have created the destination. "
                    "Inspect the configured output path before retrying; no automatic cleanup was attempted."
                ),
            )
            return report
        report["processing_started"] = True
        try:
            rendered_identity = _rendered_output_identity(rendered)
        except (OSError, ValueError) as exc:
            report.update(
                status="FAIL",
                error=f"rendered output could not be safely identified: {exc}",
                unverified_output_removed=False,
                manual_cleanup_required=True,
            )
            return report
        try:
            rendered_preflight = inspect_one_video(rendered, ffprobe_binary=ffprobe_binary)
        except Exception as exc:
            # FFprobe can fail after FFmpeg has already published the output.
            # Keep the exact output path and require manual inspection; a
            # metadata-tool exception is never evidence that the file is absent.
            report.update(
                status="FAIL",
                output_path=str(rendered),
                rendered_preflight_error=f"{type(exc).__name__}: {exc}",
                output_inspection_required=True,
                manual_cleanup_required=True,
                message=(
                    "Rendered output exists but FFprobe verification raised an exception. "
                    "Inspect this exact output path before retrying; no automatic cleanup was attempted."
                ),
            )
            return report
        if not isinstance(rendered_preflight, dict):
            # A malformed probe payload is not a verified failure of the media
            # itself. Preserve the rendered file for explicit human inspection.
            report.update(
                status="FAIL",
                output_path=str(rendered),
                rendered_preflight_error=(
                    "FFprobe returned malformed metadata: expected an object, "
                    f"received {type(rendered_preflight).__name__}"
                ),
                output_inspection_required=True,
                manual_cleanup_required=True,
                message=(
                    "Rendered output exists but FFprobe returned malformed metadata. "
                    "Inspect this exact output path before retrying; no automatic cleanup was attempted."
                ),
            )
            return report
        report["rendered_preflight"] = rendered_preflight
        if rendered_preflight.get("status") != "PASS":
            removed = _remove_unverified_output(rendered, rendered_identity)
            report.update(
                status="FAIL",
                error="rendered output failed FFprobe verification",
                unverified_output_removed=removed,
                manual_cleanup_required=not removed,
            )
            return report
        mp4_error = _rendered_mp4_validation_error(rendered_preflight)
        if mp4_error:
            removed = _remove_unverified_output(rendered, rendered_identity)
            report.update(
                status="FAIL",
                error=f"rendered output failed MP4/H.264 validation: {mp4_error}",
                unverified_output_removed=removed,
                manual_cleanup_required=not removed,
            )
            return report
        rendered_duration = rendered_preflight.get("duration_seconds")
        expected_duration = end - start
        # A fixed one-second tolerance can accept a nearly empty output for a
        # very short requested clip. Scale tolerance to the requested duration,
        # with a small floor for container/codec timing and a one-second cap.
        duration_tolerance = min(1.0, max(0.05, expected_duration * 0.02))
        try:
            valid_rendered_duration = (
                not isinstance(rendered_duration, bool)
                and isinstance(rendered_duration, (int, float))
                and math.isfinite(rendered_duration)
                and rendered_duration > 0
            )
        except (OverflowError, TypeError, ValueError):
            # Malformed FFprobe metadata must not escape the render boundary.
            # In particular, math.isfinite() can overflow on enormous integers.
            valid_rendered_duration = False
        if (not valid_rendered_duration
                or abs(rendered_duration - expected_duration) > duration_tolerance):
            removed = _remove_unverified_output(rendered, rendered_identity)
            report.update(
                status="FAIL",
                error="rendered output duration is outside the expected clip bounds",
                unverified_output_removed=removed,
                manual_cleanup_required=not removed,
            )
            return report
        try:
            output_sha256, output_size_bytes, verified_output_identity = _sha256_verified_regular_file(rendered)
            if verified_output_identity != rendered_identity:
                raise RuntimeError("rendered output identity changed before final hash verification")
        except (OSError, ValueError, RuntimeError) as exc:
            report.update(
                status="FAIL",
                error=f"rendered output failed final identity/SHA-256 verification: {exc}",
                output_sha256=None,
                output_size_bytes=None,
                manual_cleanup_required=True,
            )
            return report
        report.update(
            status="RENDERED",
            output_path=str(rendered),
            rendered_duration_seconds=float(rendered_duration),
            output_sha256=output_sha256,
            output_size_bytes=output_size_bytes,
            output_identity_verified=True,
            message="one local clip rendered and passed FFprobe plus final identity/SHA-256 verification; manual review required",
        )
    except (OSError, PermissionError, RuntimeError, ValueError) as exc:
        report.update(status="FAIL", error=str(exc))
    return report


class SourceSnapshotCreationError(RuntimeError):
    """A snapshot was created but safe cleanup after a later failure was not confirmed."""

    def __init__(self, message: str, *, snapshot_created: bool, cleanup_required: bool):
        super().__init__(message)
        self.snapshot_created = snapshot_created
        self.cleanup_required = cleanup_required


def _create_stable_source_snapshot(
    source: Path, snapshot: Path, *, expected_sha256: str | None = None
) -> str:
    """Copy one selected regular file from a verified descriptor in bounded chunks.

    Refuse source/destination aliases and never remove a destination that this
    invocation did not create. Cleanup also verifies the created inode before
    unlinking, so a replaced destination is not accidentally deleted.
    """
    source = Path(source)
    snapshot = Path(snapshot)
    try:
        if source.resolve(strict=True) == snapshot.resolve(strict=False):
            raise ValueError("snapshot destination must differ from the selected source")
    except (OSError, RuntimeError, ValueError) as exc:
        # Path.resolve() may raise RuntimeError for symlink loops and ValueError
        # for malformed paths. Keep these inside the snapshot validation boundary.
        raise ValueError(f"source or snapshot path could not be resolved: {exc}") from exc

    before_path = source.lstat()
    if stat.S_ISLNK(before_path.st_mode) or not stat.S_ISREG(before_path.st_mode):
        raise ValueError("selected source must be a regular non-symlink file")
    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(source, flags)
    snapshot_created = False
    snapshot_identity = None
    try:
        before_fd = os.fstat(descriptor)
        identity = lambda item: (
            item.st_dev, item.st_ino, item.st_size,
            item.st_mtime_ns, item.st_ctime_ns, stat.S_IFMT(item.st_mode),
        )
        if not stat.S_ISREG(before_fd.st_mode) or identity(before_fd) != identity(before_path):
            raise RuntimeError("selected source changed while opening its snapshot")
        copied = 0
        digest = hashlib.sha256()
        with os.fdopen(os.dup(descriptor), "rb") as source_handle:
            with snapshot.open("xb") as snapshot_handle:
                snapshot_created = True
                snapshot_stat = os.fstat(snapshot_handle.fileno())
                snapshot_identity = (snapshot_stat.st_dev, snapshot_stat.st_ino, stat.S_IFMT(snapshot_stat.st_mode))
                while True:
                    chunk = source_handle.read(1024 * 1024)
                    if not chunk:
                        break
                    written = snapshot_handle.write(chunk)
                    if written != len(chunk):
                        raise OSError(
                            "short write while creating the source snapshot "
                            f"({written} of {len(chunk)} bytes)"
                        )
                    digest.update(chunk)
                    copied += written
                snapshot_handle.flush()
                os.fsync(snapshot_handle.fileno())
        # Persist the snapshot directory entry as well as file contents. A
        # file-level fsync alone does not guarantee the new name survives a
        # sudden POSIX host crash before the directory metadata is committed.
        _fsync_parent_directory(snapshot)
        after_fd = os.fstat(descriptor)
        after_path = source.lstat()
        if (identity(after_fd) != identity(before_fd)
                or identity(after_path) != identity(before_path)
                or copied != before_fd.st_size):
            raise RuntimeError("selected source changed while its stable snapshot was copied")
        source_sha256 = digest.hexdigest()
        if expected_sha256 is not None and source_sha256 != expected_sha256:
            raise ValueError("selected source SHA-256 does not match trusted inventory during snapshot creation")

        # Verify the bytes persisted on disk, not only the chunks supplied to
        # write(). This catches storage/filesystem anomalies and write wrappers
        # that report a full write without persisting the complete data.
        snapshot_flags = os.O_RDONLY
        if hasattr(os, "O_BINARY"):
            snapshot_flags |= os.O_BINARY
        if hasattr(os, "O_NONBLOCK"):
            # If the private snapshot path is unexpectedly replaced with a FIFO
            # or device, do not let read-back verification block before fstat.
            snapshot_flags |= os.O_NONBLOCK
        if hasattr(os, "O_NOFOLLOW"):
            snapshot_flags |= os.O_NOFOLLOW
        snapshot_descriptor = os.open(snapshot, snapshot_flags)
        try:
            snapshot_before = os.fstat(snapshot_descriptor)
            snapshot_path_before = snapshot.lstat()
            snapshot_identity_now = (
                snapshot_before.st_dev, snapshot_before.st_ino,
                stat.S_IFMT(snapshot_before.st_mode),
            )
            if (
                not stat.S_ISREG(snapshot_before.st_mode)
                or snapshot_identity_now != snapshot_identity
                or snapshot_identity_now != (
                    snapshot_path_before.st_dev, snapshot_path_before.st_ino,
                    stat.S_IFMT(snapshot_path_before.st_mode),
                )
                or snapshot_before.st_size != before_fd.st_size
            ):
                raise RuntimeError("source snapshot identity or size changed before read-back verification")
            persisted_digest = hashlib.sha256()
            persisted_bytes_read = 0
            while True:
                persisted_chunk = os.read(snapshot_descriptor, 1024 * 1024)
                if not persisted_chunk:
                    break
                persisted_digest.update(persisted_chunk)
                persisted_bytes_read += len(persisted_chunk)
            snapshot_after = os.fstat(snapshot_descriptor)
            snapshot_path_after = snapshot.lstat()
            if (
                snapshot_after.st_dev != snapshot_before.st_dev
                or snapshot_after.st_ino != snapshot_before.st_ino
                or snapshot_after.st_size != snapshot_before.st_size
                or persisted_bytes_read != snapshot_before.st_size
                or snapshot_after.st_mtime_ns != snapshot_before.st_mtime_ns
                or snapshot_after.st_ctime_ns != snapshot_before.st_ctime_ns
                or snapshot_path_after.st_dev != snapshot_before.st_dev
                or snapshot_path_after.st_ino != snapshot_before.st_ino
                or stat.S_ISLNK(snapshot_path_after.st_mode)
            ):
                raise RuntimeError("source snapshot changed during read-back verification")
            persisted_sha256 = persisted_digest.hexdigest()
        finally:
            os.close(snapshot_descriptor)

        if persisted_sha256 != source_sha256:
            raise OSError("source snapshot read-back SHA-256 does not match copied source bytes")
        return persisted_sha256
    except Exception as original_error:
        cleanup_error = None
        if snapshot_created:
            try:
                current_snapshot = snapshot.lstat()
                current_identity = (
                    current_snapshot.st_dev,
                    current_snapshot.st_ino,
                    stat.S_IFMT(current_snapshot.st_mode),
                )
                if snapshot_identity is None or current_identity != snapshot_identity:
                    # Never unlink a path that no longer identifies the file
                    # created by this invocation.
                    cleanup_error = RuntimeError(
                        "snapshot path identity changed; the current path was preserved"
                    )
                else:
                    snapshot.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                cleanup_error = exc
        if cleanup_error is not None:
            raise SourceSnapshotCreationError(
                f"{original_error}; snapshot cleanup could not be confirmed: {cleanup_error}",
                snapshot_created=True,
                cleanup_required=True,
            ) from original_error
        raise
    finally:
        os.close(descriptor)


def _safe_path_report_label(value: Any) -> str:
    """Format an untrusted path argument for a failure report without masking the failure."""
    try:
        return str(value)
    except Exception:
        return "<unavailable>"


def render_selected_clip(
    video_path: str | Path,
    output_path: str | Path,
    start_seconds: float,
    end_seconds: float,
    *,
    execute: bool = False,
    rights_confirmed: bool = False,
    ffprobe_binary: str = "ffprobe",
    ffmpeg_binary: str = "ffmpeg",
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    """Preflight and render one immutable snapshot of the selected source.

    The original path is copied once from a verified file descriptor using
    bounded disk I/O. FFprobe and FFmpeg then consume those exact snapshot
    bytes, eliminating the pathname replacement race between the two tools.
    """
    valid_video_path = isinstance(video_path, (str, Path)) and not (
        isinstance(video_path, str) and not video_path.strip()
    )
    valid_output_path = isinstance(output_path, (str, Path)) and not (
        isinstance(output_path, str) and not output_path.strip()
    )
    if not valid_video_path:
        return {
            "status": "FAIL",
            "source_path": _safe_path_report_label(video_path),
            "output_path": _safe_path_report_label(output_path),
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "processing_started": False,
            "source_identity_verified": False,
            "source_snapshot_verified": False,
            "source_snapshot_created": False,
            "upload_performed": False,
            "publishing_enabled": False,
            "error": "video_path must be a non-empty string or pathlib.Path",
        }
    if not valid_output_path:
        return {
            "status": "FAIL",
            "source_path": _safe_path_report_label(video_path),
            "output_path": _safe_path_report_label(output_path),
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "processing_started": False,
            "source_identity_verified": False,
            "source_snapshot_verified": False,
            "source_snapshot_created": False,
            "upload_performed": False,
            "publishing_enabled": False,
            "error": "output_path must be a non-empty string or pathlib.Path",
        }

    source = Path(video_path).expanduser()
    if expected_source_sha256 is not None and (
        not isinstance(expected_source_sha256, str)
        or len(expected_source_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_source_sha256)
    ):
        return {
            "status": "FAIL",
            "source_path": str(source),
            "output_path": str(Path(output_path).expanduser()),
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "processing_started": False,
            "source_identity_verified": False,
            "source_snapshot_verified": False,
            "source_snapshot_created": False,
            "expected_source_sha256": expected_source_sha256,
            "source_sha256": None,
            "upload_performed": False,
            "publishing_enabled": False,
            "error": "expected_source_sha256 must be 64 lowercase hexadecimal characters",
        }
    if type(execute) is not bool or type(rights_confirmed) is not bool:
        return {
            "status": "FAIL",
            "source_path": str(source),
            "output_path": str(Path(output_path).expanduser()),
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "processing_started": False,
            "source_identity_verified": False,
            "source_snapshot_verified": False,
            "upload_performed": False,
            "publishing_enabled": False,
            "error": "execute and rights_confirmed must be explicit booleans",
        }

    # Planning probes the selected original in place; it never duplicates
    # the complete video merely to produce a dry-run report.
    if not execute:
        report = _render_selected_clip_from_snapshot(
            source,
            output_path,
            start_seconds,
            end_seconds,
            execute=False,
            rights_confirmed=rights_confirmed,
            ffprobe_binary=ffprobe_binary,
            ffmpeg_binary=ffmpeg_binary,
            expected_source_sha256=expected_source_sha256,
        )
        report["source_path"] = str(source)
        report["source_snapshot_verified"] = False
        report["source_snapshot_created"] = False
        return report

    # Enforce the explicit rights gate before opening or copying any media.
    if not rights_confirmed:
        return {
            "status": "BLOCKED",
            "source_path": str(source),
            "output_path": str(Path(output_path).expanduser()),
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "processing_started": False,
            "source_identity_verified": False,
            "source_snapshot_verified": False,
            "source_snapshot_created": False,
            "upload_performed": False,
            "publishing_enabled": False,
            "error": "render execution requires --confirm-rights; no source snapshot was created",
        }

    # Reject malformed or excessive bounds before copying a potentially large
    # source file into temporary storage. The lower-level path repeats this
    # validation at the actual preflight/render boundary.
    try:
        _validated_clip_bounds(start_seconds, end_seconds)
    except ValueError as exc:
        return {
            "status": "FAIL",
            "source_path": str(source),
            "output_path": str(Path(output_path).expanduser()),
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "processing_started": False,
            "source_identity_verified": False,
            "source_snapshot_verified": False,
            "source_snapshot_created": False,
            "upload_performed": False,
            "publishing_enabled": False,
            "error": str(exc),
        }

    destination = Path(output_path).expanduser()
    output_error = _validate_output_destination(source, destination)
    if output_error:
        return {
            "status": "FAIL",
            "source_path": str(source),
            "output_path": str(destination),
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "processing_started": False,
            "source_identity_verified": False,
            "source_snapshot_verified": False,
            "source_snapshot_created": False,
            "upload_performed": False,
            "publishing_enabled": False,
            "error": output_error,
        }

    # Reject invalid clip bounds before copying a potentially large source file.
    # The lower-level renderer repeats these checks at its own boundary.
    try:
        if isinstance(start_seconds, bool) or isinstance(end_seconds, bool):
            raise ValueError("clip bounds must be finite numeric values")
        start = float(start_seconds)
        end = float(end_seconds)
        if not math.isfinite(start) or not math.isfinite(end):
            raise ValueError("clip bounds must be finite numeric values")
        if start < 0 or end <= start or end - start > MAX_CLIP_SECONDS:
            raise ValueError(
                f"clip bounds must satisfy 0 <= start < end and duration <= {MAX_CLIP_SECONDS:g}s"
            )
    except (TypeError, ValueError, OverflowError) as exc:
        return {
            "status": "FAIL",
            "source_path": str(source),
            "output_path": str(destination),
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "processing_started": False,
            "source_identity_verified": False,
            "source_snapshot_verified": False,
            "source_snapshot_created": False,
            "upload_performed": False,
            "publishing_enabled": False,
            "error": str(exc),
        }

    snapshot_created = False
    snapshot_sha256: str | None = None
    render_report: dict[str, Any] | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="aro-single-clip-") as temporary_directory:
            snapshot = Path(temporary_directory) / (source.name or "selected-video.mp4")
            snapshot_sha256 = _create_stable_source_snapshot(
                source, snapshot, expected_sha256=expected_source_sha256
            )
            snapshot_created = True
            try:
                report = _render_selected_clip_from_snapshot(
                    snapshot,
                    output_path,
                    start_seconds,
                    end_seconds,
                    execute=True,
                    rights_confirmed=True,
                    ffprobe_binary=ffprobe_binary,
                    ffmpeg_binary=ffmpeg_binary,
                )
            except Exception as exc:
                # Snapshot creation and digest verification already succeeded.
                # Keep that evidence even if FFprobe/FFmpeg or a later render
                # step raises unexpectedly; do not misreport it as absent.
                render_report = {
                    "status": "FAIL",
                    "source_path": str(source),
                    "output_path": str(destination),
                    "start_seconds": start_seconds,
                    "end_seconds": end_seconds,
                    "processing_started": None,
                    "source_identity_verified": True,
                    "source_snapshot_verified": True,
                    "source_snapshot_created": True,
                    "expected_source_sha256": expected_source_sha256,
                    "source_sha256": snapshot_sha256,
                    "upload_performed": False,
                    "publishing_enabled": False,
                    "error": str(exc),
                    "message": "render failed after source snapshot verification; inspect any output file before retrying",
                }
                return render_report
            report["source_path"] = str(source)
            report["source_snapshot_verified"] = True
            report["source_snapshot_created"] = True
            report["source_sha256"] = snapshot_sha256
            render_report = report
            return report
    except Exception as exc:
        if snapshot_created:
            # TemporaryDirectory cleanup can fail after the render result is
            # already known. Preserve snapshot evidence and any known render
            # state instead of falling through to the pre-snapshot failure
            # report. The output may exist and must be inspected manually.
            return {
                # Preserve every known renderer result (especially output hash,
                # size, identity, duration, and preflight evidence) when only
                # temporary snapshot cleanup fails. The overall operation is
                # still FAIL, but discarding verified output evidence would
                # make manual recovery and duplicate-render prevention harder.
                **(render_report or {}),
                "status": "FAIL",
                "source_path": str(source),
                "output_path": str(destination),
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "processing_started": (
                    render_report.get("processing_started")
                    if render_report is not None else None
                ),
                "source_identity_verified": True,
                "source_snapshot_verified": True,
                "source_snapshot_created": True,
                "expected_source_sha256": expected_source_sha256,
                "source_sha256": snapshot_sha256,
                "render_status_before_cleanup_failure": (
                    render_report.get("status") if render_report is not None else None
                ),
                "source_preflight": (
                    render_report.get("source_preflight") if render_report is not None else None
                ),
                "rendered_preflight": (
                    render_report.get("rendered_preflight") if render_report is not None else None
                ),
                "upload_performed": False,
                "publishing_enabled": False,
                "error": f"post-snapshot render or temporary cleanup failed: {exc}",
                "message": "verified source snapshot was created; inspect any output and temporary files before retrying",
            }
        snapshot_cleanup_required = isinstance(exc, SourceSnapshotCreationError)
        return {
            "status": "FAIL",
            "source_path": str(source),
            "output_path": str(destination),
            "start_seconds": start_seconds,
            "end_seconds": end_seconds,
            "processing_started": False,
            "source_identity_verified": False,
            "source_snapshot_verified": False,
            "source_snapshot_created": (
                exc.snapshot_created if snapshot_cleanup_required else False
            ),
            "source_snapshot_cleanup_required": (
                exc.cleanup_required if snapshot_cleanup_required else False
            ),
            "expected_source_sha256": expected_source_sha256,
            "source_sha256": None,
            "upload_performed": False,
            "publishing_enabled": False,
            "error": f"selected source snapshot failed closed: {exc}",
            "message": (
                "a partial source snapshot may remain; inspect the temporary workspace before retrying"
                if snapshot_cleanup_required else
                "source snapshot was not created; no rendering was started"
            ),
        }



def _report_handle_matches_path(handle: Any, report_path: str | Path) -> bool:
    """Verify that the reserved report pathname still names the open report inode.

    The CLI keeps the original descriptor open while rendering. A concurrent
    replacement of the pathname must not cause terminal evidence to be written
    only to an unlinked file while a different file occupies the report path.
    """
    try:
        descriptor_stat = os.fstat(handle.fileno())
        path_stat = Path(report_path).lstat()
    except (OSError, ValueError):
        return False
    return (
        stat.S_ISREG(descriptor_stat.st_mode)
        and stat.S_ISREG(path_stat.st_mode)
        and descriptor_stat.st_dev == path_stat.st_dev
        and descriptor_stat.st_ino == path_stat.st_ino
    )



def _fsync_parent_directory(path: str | Path) -> None:
    """Persist a newly created report's directory entry where supported.

    POSIX filesystems require syncing the containing directory after syncing a
    newly created file if the filename itself must survive a sudden system
    crash. Python's portable file APIs do not expose an equivalent directory
    handle operation on Windows, so Windows retains file-level fsync only.
    """
    if os.name == "nt":
        return
    directory = Path(path).parent
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_exclusive_terminal_fallback(
    report_path: Path, report_text: str, protected_paths: tuple[Path, ...] = ()
) -> Path:
    """Persist a terminal report beside a damaged reservation without overwriting."""
    fallback_path = report_path.with_name(report_path.name + ".terminal-fallback.json")
    try:
        fallback_resolved = fallback_path.resolve()
        protected_resolved = tuple(protected.resolve() for protected in protected_paths)
    except (OSError, RuntimeError, ValueError) as exc:
        # A malformed path or symlink loop must stay inside the fallback
        # failure handler. Otherwise it escapes as a generic report error
        # after rendering may already have completed, hiding the output-review
        # warning from the operator.
        raise OSError(f"terminal fallback path could not be validated safely: {exc}") from exc
    if fallback_resolved in protected_resolved:
        raise OSError("terminal fallback path aliases the selected source or output path")
    fallback_created = False
    try:
        with fallback_path.open("x", encoding="utf-8", newline="\n") as fallback:
            fallback_created = True
            written = fallback.write(report_text)
            if written != len(report_text):
                raise OSError(
                    f"terminal fallback write was incomplete ({written} of {len(report_text)} characters)"
                )
            fallback.flush()
            os.fsync(fallback.fileno())
    except OSError as exc:
        if fallback_created:
            # Exclusive creation succeeded, so a short write/flush/fsync error
            # can leave a partial or non-durable sidecar. Name the exact path;
            # never remove it or imply that no fallback file exists.
            raise OSError(
                f"terminal fallback report may remain at {fallback_path}, "
                f"but its write or file synchronization failed: {exc}"
            ) from exc
        raise
    try:
        _fsync_parent_directory(fallback_path)
    except OSError as exc:
        # The fallback file itself has been flushed and fsynced. A directory
        # sync failure does not undo its creation, so report its exact path
        # instead of misleading the caller into believing no fallback exists.
        print(
            f"Fallback report exists at {fallback_path} and its file contents were fsynced, "
            f"but parent-directory synchronization failed: {exc}. "
            "Inspect this report and any rendered output before retrying.",
            file=sys.stderr,
        )
    return fallback_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or render exactly one explicitly selected local video clip."
    )
    parser.add_argument("video", type=Path, help="One selected local authorized video file.")
    parser.add_argument("--start", type=float, help="Clip start time in seconds.")
    parser.add_argument("--end", type=float, help="Clip end time in seconds.")
    parser.add_argument("--candidate-csv", type=Path, help="Review CSV produced by clip_pack.py.")
    parser.add_argument("--candidate-row", type=int, help="One-based data row to select from --candidate-csv.")
    parser.add_argument("--source-id", help="Explicitly confirm the selected video source ID for a candidate CSV row.")
    parser.add_argument("--source-sha256", help="Expected SHA-256 from the trusted authorized-media inventory for candidate CSV mode.")
    parser.add_argument("--output", type=Path, default=Path("rendered_clips/single_selected_clip.mp4"))
    parser.add_argument("--report", type=Path, default=Path("single_clip_render_report.json"))
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--execute", action="store_true", help="Actually render; default is a dry-run plan.")
    parser.add_argument("--confirm-rights", action="store_true", help="Confirm processing rights for this exact selected source.")
    args = parser.parse_args()

    direct_bounds = args.start is not None and args.end is not None
    candidate_selection = args.candidate_csv is not None and args.candidate_row is not None
    if direct_bounds == candidate_selection or (args.start is None) != (args.end is None) or (args.candidate_csv is None) != (args.candidate_row is None):
        parser.error("provide either both --start/--end or both --candidate-csv/--candidate-row")
    if (args.source_id is not None or args.source_sha256 is not None) and not candidate_selection:
        parser.error("--source-id and --source-sha256 are only valid with --candidate-csv/--candidate-row")
    selected_candidate = None
    if candidate_selection:
        try:
            selected_candidate = load_selected_candidate(args.candidate_csv, args.candidate_row)
        except ValueError as exc:
            parser.error(str(exc))
        if not args.source_id or args.source_id.strip() != selected_candidate["source_id"]:
            parser.error("candidate selection requires --source-id matching the selected CSV row")
        expected_digest = (args.source_sha256 or "").strip().lower()
        if len(expected_digest) != 64 or any(character not in "0123456789abcdef" for character in expected_digest):
            parser.error("candidate selection requires --source-sha256 with 64 hexadecimal characters from the trusted authorized-media inventory")
        start_seconds = selected_candidate["start_seconds"]
        end_seconds = selected_candidate["end_seconds"]
    else:
        start_seconds = args.start
        end_seconds = args.end

    # argparse accepts NaN and infinity as floats. Reject them before creating
    # the durable RUNNING report so persisted reports always contain valid JSON.
    if not math.isfinite(start_seconds) or not math.isfinite(end_seconds):
        parser.error("clip bounds must be finite numeric values")

    # Reserve the exclusive report path before any media inspection or rendering.
    # This prevents a completed render from being followed by a report-collision error.
    try:
        report_path = args.report.expanduser()
        source_path = args.video.expanduser()
        output_path = args.output.expanduser()
        if report_path.resolve() in {source_path.resolve(), output_path.resolve()}:
            print("Report path must differ from the selected source and output paths.", file=sys.stderr)
            return 2
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("x+", encoding="utf-8") as handle:
            # Persist a valid in-progress record before touching media. If the
            # process is interrupted during a long render, the reserved report
            # remains parseable and cannot be mistaken for a completed result.
            initial_report = {
                "status": "RUNNING",
                # Invocation identity makes an interrupted durable reservation
                # traceable without implying that a PID proves process liveness.
                "run_id": uuid.uuid4().hex,
                "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "process_id": os.getpid(),
                "source_path": str(source_path),
                "output_path": str(output_path),
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "execution_requested": bool(args.execute),
                "rights_confirmation_supplied": bool(args.confirm_rights),
                "candidate_selection": selected_candidate,
                "upload_performed": False,
                "publishing_enabled": False,
                "message": "report reserved; final render result has not yet been recorded",
            }
            # Serialize before writing so encoding/serialization errors cannot
            # leave a partially written reservation.
            try:
                initial_report_text = json.dumps(
                    initial_report, indent=2, ensure_ascii=True, allow_nan=False
                ) + "\n"
            except Exception as exc:
                print(
                    f"Initial RUNNING report could not be serialized; media was not inspected: {exc}",
                    file=sys.stderr,
                )
                return 2

            try:
                written = handle.write(initial_report_text)
                if written != len(initial_report_text):
                    raise OSError(
                        f"initial report write was incomplete ({written} of {len(initial_report_text)} characters)"
                    )
                handle.flush()
                os.fsync(handle.fileno())
                _fsync_parent_directory(report_path)
                if not _report_handle_matches_path(handle, report_path):
                    raise OSError("reserved report path no longer identifies the open report file")
            except OSError as write_exc:
                try:
                    fallback_path = _write_exclusive_terminal_fallback(
                        report_path, initial_report_text, (source_path, output_path)
                    )
                except OSError as fallback_exc:
                    print(
                        "Initial RUNNING report write failed; media was not inspected. "
                        f"The reservation may be partial and fallback creation failed: {fallback_exc}. "
                        f"Primary write error: {write_exc}",
                        file=sys.stderr,
                    )
                else:
                    print(
                        "Initial RUNNING report write failed; media was not inspected. "
                        f"Complete reservation was preserved at {fallback_path}. "
                        "Inspect both report paths before retrying.",
                        file=sys.stderr,
                    )
                return 2

            candidate_error = None
            if candidate_selection and not (args.execute and not args.confirm_rights):
                # Reject an unusable destination before hashing the selected
                # media. Candidate hashing reads the complete video, so doing
                # it before this cheap path check would waste I/O on a run that
                # cannot possibly render. Keep both checks after the durable
                # RUNNING report reservation. An unconfirmed execution request
                # must reach the renderer's early BLOCKED gate without hashing.
                output_error = _validate_output_destination(source_path, output_path)
                if output_error:
                    candidate_error = output_error
                else:
                    try:
                        actual_digest = sha256_selected_source(args.video)
                    except (OSError, ValueError) as exc:
                        candidate_error = (
                            f"selected source could not be verified by SHA-256: {exc}"
                        )
                    else:
                        if actual_digest != expected_digest:
                            candidate_error = (
                                "selected video SHA-256 does not match the trusted authorized-media inventory"
                            )
                        else:
                            selected_candidate["verified_source_sha256"] = actual_digest

            if candidate_error is not None:
                report = {
                    **initial_report,
                    "status": "FAIL",
                    "error": candidate_error,
                    "message": "candidate source verification failed; no media rendering was started",
                    "source_snapshot_verified": False,
                    "source_snapshot_created": False,
                    "source_sha256": None,
                }
            else:
                try:
                    report = {**initial_report, **render_selected_clip(
                        args.video,
                        args.output,
                        start_seconds,
                        end_seconds,
                        execute=args.execute,
                        rights_confirmed=args.confirm_rights,
                        ffprobe_binary=args.ffprobe,
                        ffmpeg_binary=args.ffmpeg,
                        expected_source_sha256=expected_digest if candidate_selection else None,
                    )}
                except Exception as exc:
                    # Any ordinary Python exception is a terminal failure, not an
                    # unknown RUNNING state. Preserve RUNNING only for hard process
                    # termination (KeyboardInterrupt/SystemExit or process death).
                    report = {
                        **initial_report,
                        "status": "FAIL",
                        # No structured renderer result was returned, so the
                        # snapshot state is unknown rather than proven absent.
                        "source_snapshot_verified": None,
                        "source_snapshot_created": None,
                        "source_sha256": None,
                        "error": str(exc),
                        # The renderer may have created or published an output
                        # before raising. An exception is not proof that the
                        # destination is absent or safe to overwrite.
                        "output_inspection_required": True,
                        "message": "render operation failed; inspect any output file before retrying",
                    }

            # Preserve the operator's explicit CSV row selection in the
            # terminal report as well as the initial RUNNING reservation.
            if selected_candidate is not None:
                report["candidate_selection"] = selected_candidate

            # Serialize completely before modifying the durable RUNNING record.
            # A serialization error must not truncate the only trustworthy report.
            try:
                terminal_report_text = json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
            except Exception as exc:
                # Rendering may already have completed. Keep the primary RUNNING
                # reservation intact, but persist a small strict-JSON failure
                # record separately so operators are warned not to retry blindly.
                safe_failure_report = {
                    **initial_report,
                    "status": "FAIL",
                    "terminal_report_serialization_failed": True,
                    "render_result_status": (
                        report.get("status") if isinstance(report.get("status"), str) else None
                    ),
                    "output_inspection_required": True,
                    "error": f"terminal report serialization failed ({type(exc).__name__})",
                    "message": (
                        "Terminal report serialization failed. Inspect any output file "
                        "manually before retrying; the primary report remains RUNNING."
                    ),
                }
                try:
                    safe_failure_text = json.dumps(
                        safe_failure_report, indent=2, ensure_ascii=True, allow_nan=False
                    ) + "\n"
                    fallback_path = _write_exclusive_terminal_fallback(
                        report_path, safe_failure_text, (source_path, output_path)
                    )
                except (OSError, TypeError, ValueError) as fallback_exc:
                    print(
                        "Terminal report could not be serialized; the primary RUNNING "
                        "report was preserved, but safe fallback creation failed. "
                        "Inspect any output file manually before retrying. "
                        f"Serialization error: {type(exc).__name__}; "
                        f"fallback error: {fallback_exc}",
                        file=sys.stderr,
                    )
                else:
                    print(
                        "Terminal report could not be serialized; the primary RUNNING "
                        f"report was preserved and a strict-JSON failure record was written to {fallback_path}. "
                        "Inspect any output file manually before retrying.",
                        file=sys.stderr,
                    )
                return 2

            try:
                if not _report_handle_matches_path(handle, report_path):
                    raise OSError("reserved report path was replaced before terminal report update")
                handle.seek(0)
                written = handle.write(terminal_report_text)
                if written != len(terminal_report_text):
                    raise OSError(
                        f"terminal report write was incomplete ({written} of {len(terminal_report_text)} characters)"
                    )
                handle.truncate()
                handle.flush()
                os.fsync(handle.fileno())
                if not _report_handle_matches_path(handle, report_path):
                    raise OSError("reserved report path was replaced during terminal report update")
            except OSError as write_exc:
                # The reserved report may now be partial. Preserve it for
                # diagnosis and write a separate exclusive fallback; never
                # replace a path that may have been created by another actor.
                try:
                    fallback_path = _write_exclusive_terminal_fallback(
                        report_path, terminal_report_text, (source_path, output_path)
                    )
                except OSError as fallback_exc:
                    print(
                        "Terminal report write failed; the reserved report may be "
                        f"partial and fallback creation also failed: {fallback_exc}. "
                        "Inspect any output file manually before retrying. "
                        f"Primary write error: {write_exc}",
                        file=sys.stderr,
                    )
                else:
                    print(
                        "Terminal report write failed; complete terminal report "
                        f"was preserved at exclusive fallback path {fallback_path}. "
                        "Inspect any output file manually before retrying.",
                        file=sys.stderr,
                    )
                return 2
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Report could not be reserved/written without overwrite: {exc}", file=sys.stderr)
        return 2

    # Reuse the exact serialized payload already persisted to disk; avoid a
    # second serialization path that could disagree with or fail after the write.
    print(terminal_report_text, end="")
    return 0 if report["status"] in {"PLANNED", "RENDERED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
