"""End-to-end FFmpeg smoke test using generated synthetic footage only.

Creates a short test pattern in a temporary directory, renders landscape and
vertical clips through the production renderer, and verifies both with ffprobe.
No creator media is opened, downloaded, uploaded, or published.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .clipping import render_clip


def _run(command: list[str], *, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Required media tool not found: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Media smoke-test command timed out: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        raise RuntimeError(detail or f"Media smoke-test command failed: {command[0]}") from exc


def _dimensions(path: Path, ffprobe: str) -> tuple[int, int]:
    result = _run([
        ffprobe, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", str(path),
    ], timeout=30)
    try:
        streams = json.loads(result.stdout)["streams"]
        width, height = int(streams[0]["width"]), int(streams[0]["height"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"ffprobe could not verify video dimensions: {path.name}") from exc
    if width <= 0 or height <= 0:
        raise RuntimeError(f"ffprobe returned invalid video dimensions: {path.name}")
    return width, height


def run_smoke_test() -> list[str]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        missing = " and ".join(name for name, path in (("ffmpeg", ffmpeg), ("ffprobe", ffprobe)) if not path)
        raise RuntimeError(f"{missing} not found on PATH. Install FFmpeg including ffprobe, then reopen the terminal.")

    results: list[str] = []
    with tempfile.TemporaryDirectory(prefix="aro-render-smoke-") as folder:
        root = Path(folder)
        source = root / "synthetic-source.mp4"
        landscape = root / "landscape.mp4"
        vertical = root / "vertical.mp4"

        # Generate original test-pattern footage. This is not game footage.
        _run([
            ffmpeg, "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:duration=4",
            "-f", "lavfi", "-i", "sine=frequency=880:sample_rate=44100:duration=4",
            "-map", "0:v:0", "-map", "1:a:0", "-t", "4",
            "-c:v", "mpeg4", "-q:v", "5", "-c:a", "aac", "-shortest", str(source),
        ])
        results.append("Synthetic 640x360 source generated")

        render_clip(source, landscape, 0.5, 2.5, rights_confirmed=True)
        if _dimensions(landscape, ffprobe) != (640, 360):
            raise RuntimeError("Landscape render did not preserve the 640x360 source dimensions.")
        results.append("Landscape MP4 render verified (640x360)")

        render_clip(source, vertical, 0.5, 2.5, rights_confirmed=True, vertical=True)
        if _dimensions(vertical, ffprobe) != (1080, 1920):
            raise RuntimeError("Vertical render is not 1080x1920.")
        results.append("Vertical Shorts MP4 render verified (1080x1920)")

    return results


def main() -> int:
    print("THE ARO synthetic FFmpeg render smoke test")
    print("Only generated test-pattern footage is used; no creator media is accessed.")
    try:
        for result in run_smoke_test():
            print(f"[PASS] {result}")
    except (OSError, RuntimeError, ValueError, PermissionError) as exc:
        print(f"[FAIL] {exc}")
        return 1
    print("[PASS] Landscape and vertical render preflight completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
