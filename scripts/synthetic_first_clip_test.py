"""Generate and render a fully synthetic MP4 to smoke-test the local renderer.

This test never downloads, reads, or uses GTA footage or third-party media.
It requires ffmpeg and ffprobe on PATH and writes to a new output directory.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make repository packages importable when this file is launched as a script.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.app.batch_render import run_batch
from backend.app.media_probe import probe_media


def _run(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Required executable not found: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Command timed out: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise RuntimeError(f"{command[0]} failed: {detail}") from exc


def run(output_root: Path, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe") -> dict[str, object]:
    if shutil.which(ffmpeg) is None:
        raise RuntimeError(f"ffmpeg executable not found: {ffmpeg}")
    if shutil.which(ffprobe) is None:
        raise RuntimeError(f"ffprobe executable not found: {ffprobe}")

    output_root = output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("synthetic-first-clip-%Y%m%dT%H%M%SZ")
    run_dir = output_root / run_id
    run_dir.mkdir(exist_ok=False)

    source = run_dir / "synthetic_source.mp4"
    candidates = run_dir / "synthetic_candidates.csv"
    renders = run_dir / "renders"

    # Generated test pattern and tone are original synthetic signals, not game footage.
    _run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=8",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=8",
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", str(source),
    ])

    media_info = probe_media(source, ffprobe_binary=ffprobe, require_audio=True)
    with candidates.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "source_id", "start_seconds", "end_seconds", "renderable",
        ])
        writer.writeheader()
        writer.writerow({
            "source_id": "synthetic-generated-fixture",
            "start_seconds": "1.0",
            "end_seconds": "5.0",
            "renderable": "true",
        })

    report = run_batch(
        candidates, source, renders, {1},
        execute=True, rights_confirmed=True, ffprobe_binary=ffprobe,
        require_audio=True,
    )
    rendered_path = Path(str(report[0].get("output_path", "")))
    if report[0].get("status") != "rendered" or not rendered_path.is_file():
        raise RuntimeError(f"Synthetic render did not complete: {report[0]}")

    rendered_info = probe_media(rendered_path, ffprobe_binary=ffprobe, require_audio=True)
    summary: dict[str, object] = {
        "test": "synthetic-first-clip",
        "status": "passed",
        "source_type": "locally-generated synthetic test pattern and tone",
        "gta6_footage_used": False,
        "third_party_media_used": False,
        "source_duration_seconds": media_info.duration_seconds,
        "rendered_duration_seconds": rendered_info.duration_seconds,
        "rendered_file": str(rendered_path),
        "publishing_enabled": False,
        "manual_review_required": True,
    }
    (run_dir / "result.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a short MP4 from locally generated synthetic media; no GTA footage is used."
    )
    parser.add_argument("--output-dir", type=Path, default=Path("synthetic_test_runs"))
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    try:
        result = run(args.output_dir, args.ffmpeg, args.ffprobe)
    except (OSError, RuntimeError, ValueError, PermissionError) as exc:
        print(f"Synthetic first-clip test failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
