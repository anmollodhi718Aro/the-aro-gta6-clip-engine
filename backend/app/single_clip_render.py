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
from pathlib import Path
from typing import Any

from .clipping import MAX_CLIP_SECONDS, render_clip
from .media_single_preflight import inspect_one_video



def load_selected_candidate(csv_path: str | Path, row_number: int) -> dict[str, Any]:
    """Load one explicitly numbered, review-ready candidate from a clip-pack CSV.

    Row numbers are one-based data rows (the header is not counted). This
    function only reads review metadata; it never selects or opens media.
    """
    if isinstance(row_number, bool) or not isinstance(row_number, int) or row_number < 1:
        raise ValueError("candidate row must be a positive one-based integer")
    path = Path(csv_path).expanduser()
    try:
        # Accept an optional UTF-8 BOM from spreadsheet exports while keeping
        # the generated clip-pack CSV format unchanged.
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"source_id", "start_seconds", "end_seconds", "duration_seconds", "renderable"}
            headers = reader.fieldnames
            if not headers or not required.issubset(set(headers)):
                raise ValueError("candidate CSV is missing required review columns")
            if any(not str(header).strip() for header in headers) or len(headers) != len(set(headers)):
                raise ValueError("candidate CSV contains blank or duplicate column names")
            selected = None
            for number, row in enumerate(reader, start=1):
                if number == row_number:
                    if None in row:
                        raise ValueError(f"candidate row {row_number} has more values than its header")
                    if any(row.get(column) is None for column in required):
                        raise ValueError(f"candidate row {row_number} is missing required values")
                    selected = row
                    break
    except (OSError, csv.Error) as exc:
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
    source = Path(path).expanduser()
    try:
        before_path = source.lstat()
        if stat.S_ISLNK(before_path.st_mode) or not stat.S_ISREG(before_path.st_mode):
            raise ValueError("selected source must be a regular non-symlink file")
        flags = os.O_RDONLY
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
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
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after_fd = os.fstat(descriptor)
        after_path = source.lstat()
        if (
            identity(after_fd) != identity(before_fd)
            or identity(after_path) != identity(before_fd)
            or stat.S_ISLNK(after_path.st_mode)
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


def _rendered_output_identity(path: str | Path) -> tuple[int, int, int] | None:
    """Identify an output created by render_clip without following symlinks."""
    candidate = Path(path)
    metadata = candidate.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError("rendered output must be a regular non-symlink file")
    return metadata.st_dev, metadata.st_ino, stat.S_IFMT(metadata.st_mode)


def _sha256_verified_regular_file(path: str | Path) -> tuple[str, int, tuple[int, int, int]]:
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
        identity = (before.st_dev, before.st_ino, stat.S_IFMT(before.st_mode))
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before_path.st_mode)
            or identity != (before_path.st_dev, before_path.st_ino, stat.S_IFMT(before_path.st_mode))
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
            (after.st_dev, after.st_ino, stat.S_IFMT(after.st_mode)) != identity
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

    output_error = _validate_output_destination(source, destination)
    if output_error:
        report["error"] = output_error
        return report

    try:
        source_identity_before = _selected_file_identity(source)
    except (OSError, ValueError) as exc:
        report["error"] = f"selected source could not be safely identified: {exc}"
        return report

    preflight = inspect_one_video(source, ffprobe_binary=ffprobe_binary)
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
        rendered = render_clip(
            source,
            destination,
            start,
            end,
            rights_confirmed=True,
            ffmpeg_binary=ffmpeg_binary,
        )
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
        rendered_preflight = inspect_one_video(rendered, ffprobe_binary=ffprobe_binary)
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
    except OSError as exc:
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
            while True:
                persisted_chunk = os.read(snapshot_descriptor, 1024 * 1024)
                if not persisted_chunk:
                    break
                persisted_digest.update(persisted_chunk)
            snapshot_after = os.fstat(snapshot_descriptor)
            snapshot_path_after = snapshot.lstat()
            if (
                snapshot_after.st_dev != snapshot_before.st_dev
                or snapshot_after.st_ino != snapshot_before.st_ino
                or snapshot_after.st_size != snapshot_before.st_size
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
    except Exception:
        if snapshot_created:
            try:
                current_snapshot = snapshot.lstat()
                if snapshot_identity is not None and (
                        current_snapshot.st_dev, current_snapshot.st_ino,
                        stat.S_IFMT(current_snapshot.st_mode),
                    ) == snapshot_identity:
                    snapshot.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        os.close(descriptor)


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
            "expected_source_sha256": expected_source_sha256,
            "source_sha256": None,
            "upload_performed": False,
            "publishing_enabled": False,
            "error": f"selected source snapshot failed closed: {exc}",
        }


def _write_exclusive_terminal_fallback(
    report_path: Path, report_text: str, protected_paths: tuple[Path, ...] = ()
) -> Path:
    """Persist a terminal report beside a damaged reservation without overwriting."""
    fallback_path = report_path.with_name(report_path.name + ".terminal-fallback.json")
    fallback_resolved = fallback_path.resolve()
    if any(fallback_resolved == protected.resolve() for protected in protected_paths):
        raise OSError("terminal fallback path aliases the selected source or output path")
    with fallback_path.open("x", encoding="utf-8", newline="\n") as fallback:
        written = fallback.write(report_text)
        if written != len(report_text):
            raise OSError(
                f"terminal fallback write was incomplete ({written} of {len(report_text)} characters)"
            )
        fallback.flush()
        os.fsync(fallback.fileno())
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
        try:
            actual_digest = sha256_selected_source(args.video)
        except (OSError, ValueError) as exc:
            parser.error(f"selected source could not be verified by SHA-256: {exc}")
        if actual_digest != expected_digest:
            parser.error("selected video SHA-256 does not match the trusted authorized-media inventory")
        selected_candidate["verified_source_sha256"] = actual_digest
        start_seconds = selected_candidate["start_seconds"]
        end_seconds = selected_candidate["end_seconds"]
    else:
        start_seconds = args.start
        end_seconds = args.end

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
                "source_path": str(source_path),
                "output_path": str(output_path),
                "start_seconds": start_seconds,
                "end_seconds": end_seconds,
                "execution_requested": bool(args.execute and args.confirm_rights),
                "candidate_selection": selected_candidate,
                "upload_performed": False,
                "publishing_enabled": False,
                "message": "report reserved; final render result has not yet been recorded",
            }
            # Serialize before writing so encoding/serialization errors cannot
            # leave a partially written reservation.
            try:
                initial_report_text = json.dumps(
                    initial_report, indent=2, ensure_ascii=False
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

            try:
                report = render_selected_clip(
                    args.video,
                    args.output,
                    start_seconds,
                    end_seconds,
                    execute=args.execute,
                    rights_confirmed=args.confirm_rights,
                    ffprobe_binary=args.ffprobe,
                    ffmpeg_binary=args.ffmpeg,
                    expected_source_sha256=expected_digest if candidate_selection else None,
                )
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
                    "message": "render operation failed; inspect any output file before retrying",
                }

            # Preserve the operator's explicit CSV row selection in the
            # terminal report as well as the initial RUNNING reservation.
            if selected_candidate is not None:
                report["candidate_selection"] = selected_candidate

            # Serialize completely before modifying the durable RUNNING record.
            # A serialization error must not truncate the only trustworthy report.
            try:
                terminal_report_text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
            except Exception as exc:
                print(f"Terminal report could not be serialized; reserved RUNNING report preserved: {exc}", file=sys.stderr)
                return 2

            try:
                handle.seek(0)
                written = handle.write(terminal_report_text)
                if written != len(terminal_report_text):
                    raise OSError(
                        f"terminal report write was incomplete ({written} of {len(terminal_report_text)} characters)"
                    )
                handle.truncate()
                handle.flush()
                os.fsync(handle.fileno())
            except OSError as write_exc:
                # The reserved report may now be partial. Preserve it for
                # diagnosis and write a separate exclusive fallback; never
                # replace a path that may have been created by another actor.
                try:
                    fallback_path = _write_exclusive_terminal_fallback(
                        args.report, terminal_report_text, (source_path, output_path)
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
