"""One-command local clip export for an operator-reviewed gameplay recording.

This is the fastest path to a first clip when no chat-event plan is available.
It only trims a local file at manually chosen timestamps.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .clipping import render_clip


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Trim one manually selected section from a local recording using FFmpeg."
    )
    parser.add_argument("media", type=Path, help="path to your local gameplay recording")
    parser.add_argument("--start", required=True, type=float, help="clip start in seconds")
    parser.add_argument("--end", required=True, type=float, help="clip end in seconds")
    parser.add_argument("--output", required=True, type=Path, help="new .mp4 output path")
    parser.add_argument(
        "--confirm-rights",
        action="store_true",
        help="confirm you own or are authorized to edit this exact local recording",
    )
    parser.add_argument("--ffmpeg", default="ffmpeg", help="FFmpeg executable (default: ffmpeg)")
    args = parser.parse_args(argv)

    try:
        if not args.confirm_rights:
            raise PermissionError(
                "add --confirm-rights only after confirming you own or are authorized to edit this recording"
            )
        output = render_clip(
            args.media,
            args.output,
            args.start,
            args.end,
            rights_confirmed=True,
            ffmpeg_binary=args.ffmpeg,
        )
        report = {
            "status": "rendered",
            "input": str(args.media.expanduser().resolve()),
            "output": str(output),
            "start_seconds": args.start,
            "end_seconds": args.end,
            "duration_seconds": round(args.end - args.start, 3),
            "manual_review_required": True,
            "upload_approved": False,
        }
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, PermissionError, RuntimeError) as exc:
        print(f"Quick clip stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
