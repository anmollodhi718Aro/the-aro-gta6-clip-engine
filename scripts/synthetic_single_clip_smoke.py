"""End-to-end smoke test for the one-selected-clip pipeline using generated media only.

This creates a short local test pattern and tone, renders one selected segment
through the production single-clip pipeline, verifies the report, then removes
all temporary media. It never reads external footage or uploads/publishes.
"""
from __future__ import annotations

import argparse
import json
import shutil
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

        if report.get("status") != "RENDERED":
            raise RuntimeError(
                "single-clip pipeline did not return RENDERED: "
                + json.dumps(report, ensure_ascii=True, allow_nan=False)
            )
        if not output.is_file() or output.stat().st_size <= 0:
            raise RuntimeError("pipeline reported success but the synthetic output is missing or empty")
        if report.get("upload_performed") is not False or report.get("publishing_enabled") is not False:
            raise RuntimeError("smoke test unexpectedly enabled upload or publishing")
        digest = report.get("output_sha256")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)):
            raise RuntimeError("pipeline did not return a valid output SHA-256")
        return {
            "status": "PASS",
            "media": "synthetic test pattern and tone only",
            "source_duration_seconds": 8,
            "selected_clip_seconds": 4,
            "output_size_bytes": output.stat().st_size,
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
    except (OSError, subprocess.SubprocessError, RuntimeError, ValueError) as exc:
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
