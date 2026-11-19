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
            stream.write("\\n")
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def analyze_file(input_path: Path, output_path: Path, config: DetectorConfig) -> int:
    try:
        payload: dict[str, Any] = json.loads(input_path.read_text(encoding="utf-8"))
        permission = PermissionRecord.from_dict(payload["permission"])
        events = [ChatEvent.from_dict(item) for item in payload.get("events", [])]
        candidates = detect_chat_spikes(events, permission, config)
        output = {
            "source_id": permission.source_id,
            "candidate_count": len(candidates),
            "candidates": [candidate.to_dict() for candidate in candidates],
            "publishing_enabled": False,
        }
        _write_json_atomically(output_path, output)
        print(f"Wrote {len(candidates)} candidate(s) to {output_path}")
        return 0
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
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
