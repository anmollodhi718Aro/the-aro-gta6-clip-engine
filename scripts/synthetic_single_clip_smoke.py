"""End-to-end smoke test for the one-selected-clip pipeline using generated media only.

This creates a short local test pattern and tone, renders one selected segment
through the production single-clip pipeline, verifies the report, then removes
all temporary media. It never reads external footage or uploads/publishes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from backend.app.single_clip_render import render_selected_clip


def _require_executable(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        raise FileNotFoundError(f"Required executable was not found on PATH: {name}")
    return resolved



def _hash_verified_output(
    path: str | Path, *, distinct_from: str | Path | None = None
) -> tuple[str, int]:
    """Hash one stable regular output file without following a symlink.

    When distinct_from is supplied, compare the opened output descriptor with
    the source inode. This closes the path-swap window between a prior
    samefile() check and opening the output for hashing.
    """
    candidate = Path(path)
    before_path = candidate.lstat()
    if not stat.S_ISREG(before_path.st_mode):
        raise RuntimeError("synthetic output must be a regular non-symlink file")

    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(candidate, flags)
    try:
        before_fd = os.fstat(descriptor)
        identity = lambda item: (
            item.st_dev, item.st_ino, item.st_size,
            item.st_mtime_ns, item.st_ctime_ns, stat.S_IFMT(item.st_mode),
        )
        if not stat.S_ISREG(before_fd.st_mode) or identity(before_fd) != identity(before_path):
            raise RuntimeError("synthetic output changed while opening it for verification")
        if distinct_from is not None:
            source_stat = Path(distinct_from).lstat()
            if (not stat.S_ISREG(source_stat.st_mode)
                    or (before_fd.st_dev, before_fd.st_ino)
                    == (source_stat.st_dev, source_stat.st_ino)):
                raise RuntimeError("synthetic output must not alias its source")
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
        after_fd = os.fstat(descriptor)
        after_path = candidate.lstat()
        if (identity(after_fd) != identity(before_fd)
                or identity(after_path) != identity(before_fd)
                or size != before_fd.st_size):
            raise RuntimeError("synthetic output changed during SHA-256 verification")
        if size <= 0:
            raise RuntimeError("synthetic output is empty")
        return digest.hexdigest(), size
    finally:
        os.close(descriptor)


def run_smoke_test(*, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe") -> dict:
    ffmpeg_path = _require_executable(ffmpeg)
    ffprobe_path = _require_executable(ffprobe)

    with tempfile.TemporaryDirectory(prefix="aro-single-clip-smoke-") as temp:
        root = Path(temp)
        source = root / "synthetic-source.mp4"
        output = root / "synthetic-rendered-clip.mp4"

        command = [
            ffmpeg_path,
            "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
            "-t", "8", "-shortest",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-movflags", "+faststart",
            str(source),
        ]
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)

        report = render_selected_clip(
            source,
            output,
            1.0,
            5.0,
            execute=True,
            rights_confirmed=True,
            ffprobe_binary=ffprobe_path,
            ffmpeg_binary=ffmpeg_path,
        )

        if not isinstance(report, dict):
            raise RuntimeError("single-clip pipeline returned a malformed report; expected an object")
        if report.get("status") != "RENDERED":
            try:
                report_summary = json.dumps(report, ensure_ascii=True, allow_nan=False)
            except (TypeError, ValueError):
                # A malformed internal report must still produce the CLI's
                # structured FAIL response instead of leaking a traceback.
                report_summary = "<renderer report is not valid JSON>"
            raise RuntimeError(
                "single-clip pipeline did not return RENDERED: " + report_summary
            )
        if not output.exists():
            raise RuntimeError("pipeline reported success but the synthetic output is missing")
        # A renderer must produce a distinct clip, not merely relabel the
        # source recording through a hard link or an identical pathname.
        if os.path.samefile(source, output):
            raise RuntimeError("synthetic output must not alias its source")
        if report.get("upload_performed") is not False or report.get("publishing_enabled") is not False:
            raise RuntimeError("smoke test unexpectedly enabled upload or publishing")
        output_probe = subprocess.run(
            [ffprobe_path, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(output)],
            check=True, capture_output=True, text=True, timeout=30,
        )
        try:
            probe_payload = json.loads(output_probe.stdout)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("FFprobe returned malformed portrait stream metadata") from exc
        if not isinstance(probe_payload, dict):
            raise RuntimeError("FFprobe portrait metadata must be a JSON object")
        probed_streams = probe_payload.get("streams")
        if not isinstance(probed_streams, list) or not probed_streams or any(
            not isinstance(stream, dict)
            or stream.get("width") != 1080
            or stream.get("height") != 1920
            for stream in probed_streams
        ):
            raise RuntimeError("independent FFprobe check did not confirm 1080x1920 portrait output")
        digest = report.get("output_sha256")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)):
            raise RuntimeError("pipeline did not return a valid output SHA-256")

        # Independently hash the exact output inode. Do not follow symlinks or
        # accept a path that changes while its bytes are being verified.
        actual_digest, output_size_bytes = _hash_verified_output(
            output, distinct_from=source
        )
        if output_size_bytes <= 0:
            raise RuntimeError("pipeline reported success but the synthetic output is empty")
        if actual_digest != digest:
            raise RuntimeError("renderer output SHA-256 does not match the rendered MP4 bytes")

        return {
            "status": "PASS",
            "media": "synthetic test pattern and tone only",
            "source_duration_seconds": 8,
            "selected_clip_seconds": 4,
            "output_size_bytes": output_size_bytes,
            "output_sha256": digest,
            "upload_performed": False,
            "publishing_enabled": False,
            "manual_review_required": True,
            "artifacts_retained": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate synthetic media and exercise the one-selected-clip renderer end to end."
    )
    parser.add_argument("--ffmpeg", default="ffmpeg", help="FFmpeg executable or PATH name.")
    parser.add_argument("--ffprobe", default="ffprobe", help="FFprobe executable or PATH name.")
    args = parser.parse_args()
    try:
        result = run_smoke_test(ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError, OverflowError) as exc:
        print(json.dumps({
            "status": "FAIL",
            "error": f"{type(exc).__name__}: {exc}",
            "upload_performed": False,
            "publishing_enabled": False,
        }, indent=2, ensure_ascii=True, allow_nan=False), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
