"""CLI for rendering a locally supplied, permission-cleared video segment."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any
from .clipping import render_local_clip
from .models import PermissionRecord

def main() -> int:
    parser = argparse.ArgumentParser(description="Render a local video segment. No download or publishing is performed.")
    parser.add_argument("input", type=Path, help="operator-supplied local video file")
    parser.add_argument("--output", type=Path, required=True, help="new .mp4 output path")
    parser.add_argument("--permission-json", type=Path, required=True, help="permission record JSON")
    parser.add_argument("--source-id", required=True, help="must match the permission source_id")
    parser.add_argument("--start-seconds", type=float, required=True)
    parser.add_argument("--duration-seconds", type=float, required=True)
    parser.add_argument("--confirm-local-render", action="store_true",
                        help="confirm this local render is intended and media rights have been checked")
    args = parser.parse_args()
    if not args.confirm_local_render:
        parser.error("--confirm-local-render is required")
    try:
        payload: dict[str, Any] = json.loads(args.permission_json.read_text(encoding="utf-8"))
        permission = PermissionRecord.from_dict(payload)
        result = render_local_clip(
            args.input, args.output, source_id=args.source_id, permission=permission,
            start_seconds=args.start_seconds, duration_seconds=args.duration_seconds,
            confirmed=args.confirm_local_render,
        )
        print(f"Rendered {result.output_path} ({result.duration_seconds:.2f}s, video codec: {result.video_codec})")
        return 0
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, PermissionError, RuntimeError) as exc:
        print(f"Render stopped: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
