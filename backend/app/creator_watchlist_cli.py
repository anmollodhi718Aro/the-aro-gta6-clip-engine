"""CLI for evidence-backed seven-day creator activity rankings."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .creator_watchlist import SevenDayMetrics, ranking_report


def _parse_datetime(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed


def load_metrics(path: Path) -> list[SevenDayMetrics]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("metrics"), list):
        raise ValueError("input must be an object containing a metrics array")
    rows: list[SevenDayMetrics] = []
    for index, item in enumerate(payload["metrics"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"metrics[{index - 1}] must be an object")
        captured = item.get("captured_at")
        rows.append(
            SevenDayMetrics(
                creator_id=str(item.get("creator_id", "")),
                window_start=_parse_datetime(item.get("window_start"), f"metrics[{index - 1}].window_start"),
                window_end=_parse_datetime(item.get("window_end"), f"metrics[{index - 1}].window_end"),
                views=item.get("views"),
                live_streams=item.get("live_streams"),
                peak_concurrent_viewers=item.get("peak_concurrent_viewers", 0),
                average_concurrent_viewers=item.get("average_concurrent_viewers", 0.0),
                source_url=str(item.get("source_url", "")),
                captured_at=_parse_datetime(captured, f"metrics[{index - 1}].captured_at") if captured else None,
            )
        )
    return rows


def run(input_path: Path, output_path: Path) -> int:
    try:
        report = ranking_report(load_metrics(input_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {report['ranked_count']} evidence-backed creator ranking(s) to {output_path}")
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"Creator ranking stopped: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank supplied GTA creator metrics over one exact seven-day window.")
    parser.add_argument("input", type=Path, help="JSON file containing a metrics array")
    parser.add_argument("--output", type=Path, default=Path("creator_ranking.json"))
    args = parser.parse_args()
    return run(args.input, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
