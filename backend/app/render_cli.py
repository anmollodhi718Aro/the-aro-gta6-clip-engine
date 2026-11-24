"""Command-line entry point for local, authorized, review-only rendering."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .render import RenderError, render_clip


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a short local clip from media you own or are authorized to edit."
    )
    parser.add_argument("input", type=Path, help="path to an authorized local video file")
    parser.add_argument("output", type=Path, help="new .mp4 output path")
    parser.add_argument("--start", type=float, required=True, help="clip start offset in seconds")
    parser.add_argument("--duration", type=float, required=True, help="clip duration, maximum 180 seconds")
    parser.add_argument(
        "--confirm-rights",
        action="store_true",
        help="confirm you own or are authorized to edit this media",
    )
    args = parser.parse_args()
    try:
        result = render_clip(
            args.input,
            args.output,
            start_seconds=args.start,
            duration_seconds=args.duration,
            rights_confirmed=args.confirm_rights,
        )
    except (OSError, ValueError, PermissionError, RenderError) as exc:
        print(f"Render stopped: {exc}", file=sys.stderr)
        return 2

    print(f"Created review-only clip: {result}")
    print("Publishing is not available in this command.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
