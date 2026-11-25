"""Dry-run-first rendering for exactly one explicitly selected local video."""
from __future__ import annotations

import argparse
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


def _selected_file_identity(path: Path) -> tuple[int, int, int, int, int, int]:
    """Return a stable identity for one regular, non-symlink selected file."""
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValueError("selected source must remain a regular non-symlink file")
    return (
        metadata.st_dev, metadata.st_ino, metadata.st_size,
        metadata.st_mtime_ns, metadata.st_ctime_ns, metadata.st_mode,
    )


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

    output_error = _validate_output_destination(source, destination)
    if output_error:
        report["error"] = output_error
        return report

    # Reject invalid bounds before source identity checks or FFprobe work.
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

    try:
        start, end = _validated_clip_bounds(start_seconds, end_seconds)
    except ValueError as exc:
        report["error"] = str(exc)
        return report

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
        report["processing_started"] = True
        rendered = render_clip(
            source,
            destination,
            start,
            end,
            rights_confirmed=True,
            ffmpeg_binary=ffmpeg_binary,
        )
        rendered_preflight = inspect_one_video(rendered, ffprobe_binary=ffprobe_binary)
        report["rendered_preflight"] = rendered_preflight
        if rendered_preflight.get("status") != "PASS":
            report.update(status="FAIL", error="rendered output failed FFprobe verification")
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
            report.update(status="FAIL", error="rendered output duration is outside the expected clip bounds")
            return report
        report.update(
            status="RENDERED",
            output_path=str(rendered),
            rendered_duration_seconds=float(rendered_duration),
            message="one local clip rendered and passed FFprobe verification; manual review required",
        )
    except (OSError, PermissionError, RuntimeError, ValueError) as exc:
        report.update(status="FAIL", error=str(exc))
    return report


def _create_stable_source_snapshot(source: Path, snapshot: Path) -> None:
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
        with os.fdopen(os.dup(descriptor), "rb") as source_handle:
            with snapshot.open("xb") as snapshot_handle:
                snapshot_created = True
                snapshot_stat = os.fstat(snapshot_handle.fileno())
                snapshot_identity = (snapshot_stat.st_dev, snapshot_stat.st_ino, stat.S_IFMT(snapshot_stat.st_mode))
                while True:
                    chunk = source_handle.read(1024 * 1024)
                    if not chunk:
                        break
                    snapshot_handle.write(chunk)
                    copied += len(chunk)
                snapshot_handle.flush()
                os.fsync(snapshot_handle.fileno())
        after_fd = os.fstat(descriptor)
        after_path = source.lstat()
        if (identity(after_fd) != identity(before_fd)
                or identity(after_path) != identity(before_path)
                or copied != before_fd.st_size):
            raise RuntimeError("selected source changed while its stable snapshot was copied")
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
) -> dict[str, Any]:
    """Preflight and render one immutable snapshot of the selected source.

    The original path is copied once from a verified file descriptor using
    bounded disk I/O. FFprobe and FFmpeg then consume those exact snapshot
    bytes, eliminating the pathname replacement race between the two tools.
    """
    source = Path(video_path).expanduser()
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

    try:
        with tempfile.TemporaryDirectory(prefix="aro-single-clip-") as temporary_directory:
            snapshot = Path(temporary_directory) / (source.name or "selected-video.mp4")
            _create_stable_source_snapshot(source, snapshot)
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
            report["source_path"] = str(source)
            report["source_snapshot_verified"] = True
            report["source_snapshot_created"] = True
            return report
    except (OSError, RuntimeError, ValueError) as exc:
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
            "error": f"selected source snapshot failed closed: {exc}",
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or render exactly one explicitly selected local video clip."
    )
    parser.add_argument("video", type=Path, help="One selected local authorized video file.")
    parser.add_argument("--start", type=float, required=True, help="Clip start time in seconds.")
    parser.add_argument("--end", type=float, required=True, help="Clip end time in seconds.")
    parser.add_argument("--output", type=Path, default=Path("rendered_clips/single_selected_clip.mp4"))
    parser.add_argument("--report", type=Path, default=Path("single_clip_render_report.json"))
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--execute", action="store_true", help="Actually render; default is a dry-run plan.")
    parser.add_argument("--confirm-rights", action="store_true", help="Confirm processing rights for this exact selected source.")
    args = parser.parse_args()

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
        with report_path.open("x", encoding="utf-8") as handle:
            report = render_selected_clip(
                args.video,
                args.output,
                args.start,
                args.end,
                execute=args.execute,
                rights_confirmed=args.confirm_rights,
                ffprobe_binary=args.ffprobe,
                ffmpeg_binary=args.ffmpeg,
            )
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Report could not be reserved/written without overwrite: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] in {"PLANNED", "RENDERED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
