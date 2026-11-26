"""CLI for analyzing a JSON file of authorized chat events."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from .detection import DetectorConfig, detect_chat_spikes
from .models import ChatEvent, PermissionRecord


def _write_json_atomically(output_path: Path, payload: dict[str, Any]) -> None:
    """Replace a clip plan only after a complete JSON document is on disk."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            json.dump(payload, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def analyze_file(input_path: Path, output_path: Path, config: DetectorConfig) -> int:
    try:
        # Do not follow a final-component output symlink: resolving it would
        # redirect the atomic replacement to an unrelated target file.
        if output_path.is_symlink():
            raise ValueError("output path must not be a symbolic link")
        # Never let a clip-plan destination replace its own source JSON, including
        # aliases that resolve to the same file through relative paths or symlinks.
        if input_path.resolve() == output_path.resolve():
            raise ValueError("output path must differ from the input JSON file")
        # Keep the lexical destination for the atomic replace. Resolving the
        # final component here would follow a symlink created after the check
        # above and could redirect the write to an unrelated target.
        output_destination = output_path.absolute()
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input JSON must contain an object at the top level")
        if "permission" not in payload:
            raise ValueError("input JSON is missing permission")
        raw_events = payload.get("events", [])
        if not isinstance(raw_events, list):
            raise ValueError("input JSON events must be a list")
        permission = PermissionRecord.from_dict(payload["permission"])
        events = [ChatEvent.from_dict(item) for item in raw_events]
        candidates = detect_chat_spikes(events, permission, config)
        output = {
            "source_id": permission.source_id,
            "candidate_count": len(candidates),
            "candidates": [candidate.to_dict() for candidate in candidates],
            "publishing_enabled": False,
        }
        _write_json_atomically(output_destination, output)
        print(f"Wrote {len(candidates)} candidate(s) to {output_path}")
        return 0
    except (OSError, RuntimeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Analysis stopped: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze authorized chat events for highlight candidates.")
    parser.add_argument("input", type=Path, help="JSON file with permission and events")
    parser.add_argument("--output", type=Path, default=Path("clip_plan.json"))
    parser.add_argument("--window-seconds", type=int, default=10)
    parser.add_argument("--baseline-windows", type=int, default=3)
    parser.add_argument("--spike-multiplier", type=float, default=2.0)
    parser.add_argument("--min-messages", type=int, default=5)
    args = parser.parse_args()
    try:
        config = DetectorConfig(
            window_seconds=args.window_seconds,
            baseline_windows=args.baseline_windows,
            spike_multiplier=args.spike_multiplier,
            min_messages=args.min_messages,
        )
    except ValueError as exc:
        parser.error(str(exc))
    return analyze_file(args.input, args.output, config)


if __name__ == "__main__":
    raise SystemExit(main())
