"""Command-line entry point for rendering one authorized local video clip."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .models import PermissionRecord
from .video_clipper import ClipError, render_clip


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a clip from a local video file you own or are licensed to use."
    )
    parser.add_argument("input", type=Path, help="local source video")
    parser.add_argument("output", type=Path, help="new .mp4 output path")
    parser.add_argument("--start", type=float, required=True, help="clip start in seconds")
    parser.add_argument("--duration", type=float, required=True, help="clip length in seconds")
    parser.add_argument("--permission", type=Path, required=True, help="JSON permission record with render_video scope")
    parser.add_argument("--confirm-authorized", action="store_true", help="attest that you own or are licensed to use this footage")
    parser.add_argument("--vertical", action="store_true", help="center-crop to 9:16, 1080x1920")
    args = parser.parse_args()

    try:
        payload: dict[str, Any] = json.loads(args.permission.read_text(encoding="utf-8"))
        permission_data = payload.get("permission", payload)
        permission = PermissionRecord.from_dict(permission_data)
        output = render_clip(
            args.input, args.output, args.start, args.duration, permission,
            confirm_authorized=args.confirm_authorized, vertical=args.vertical,
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, PermissionError, ClipError) as exc:
        print(f"Clip failed: {exc}", file=sys.stderr)
        return 2

    print(f"Clip rendered: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
