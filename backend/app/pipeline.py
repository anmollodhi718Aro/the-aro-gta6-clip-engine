"""One-command offline pipeline from permitted chat events to a scored review pack.

This command never downloads, renders, uploads, or publishes media. A measured
clock-anchor file and explicit chat-analysis permission are required.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from .candidate_quality import score_rows
from .cli import analyze_file
from .clip_pack import load_clock_sync, map_candidates_to_media, write_clip_pack
from .detection import DetectorConfig


def run_pipeline(
    events_path: str | Path,
    anchors_path: str | Path,
    output_dir: str | Path,
    *,
    config: DetectorConfig | None = None,
) -> dict[str, Any]:
    """Create a complete offline review pack without touching existing outputs."""
    source = Path(events_path).expanduser()
    anchors = Path(anchors_path).expanduser()
    destination = Path(output_dir).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"chat event JSON does not exist: {source}")
    if not anchors.is_file():
        raise FileNotFoundError(f"clock-anchor JSON does not exist: {anchors}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(exist_ok=False)

    try:
        plan_path = destination / "clip_plan.json"
        status = analyze_file(source, plan_path, config or DetectorConfig())
        if status != 0:
            raise ValueError("chat analysis failed; see the analysis error above")
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if not isinstance(plan, dict) or not isinstance(plan.get("candidates"), list):
            raise ValueError("analysis produced an invalid clip plan")

        clock = load_clock_sync(anchors)
        if plan.get("source_id") != clock.source_id:
            raise ValueError("chat plan source_id does not match measured clock anchors")
        mapped = map_candidates_to_media(
            plan["candidates"], clock_sync=clock, source_id=plan["source_id"],
        )
        pack_dir = destination / "clip_pack"
        csv_path, markdown_path = write_clip_pack(mapped, pack_dir)
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        scored = score_rows(rows)
        scored_path = destination / "quality_scored_candidates.csv"
        fields = list(scored[0]) if scored else [
            "source_id", "score", "peak_message_count", "peak_window_start",
            "clip_start_utc", "clip_end_utc", "start_seconds", "end_seconds",
            "duration_seconds", "renderable", "sync_method",
            "sync_max_residual_seconds", "sync_drift_ppm", "review_note",
            "quality_score", "activity_points", "duration_points", "sync_points",
            "quality_reasons",
        ]
        with scored_path.open("x", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in scored:
                saved = dict(row)
                if isinstance(saved.get("quality_reasons"), list):
                    saved["quality_reasons"] = " | ".join(saved["quality_reasons"])
                writer.writerow(saved)

        summary = {
            "source_id": plan["source_id"],
            "candidate_count": len(scored),
            "renderable_count": sum(bool(row["renderable"]) for row in mapped),
            "clock_sync_method": "measured_multi_anchor_fit",
            "clock_max_residual_seconds": clock.max_residual_seconds,
            "clock_drift_ppm": clock.drift_ppm,
            "outputs": [
                "clip_plan.json",
                "clip_pack/clip_candidates.csv",
                "clip_pack/clip_candidates.md",
                "quality_scored_candidates.csv",
            ],
            "rendering_performed": False,
            "upload_performed": False,
            "publishing_enabled": False,
            "human_review_required": True,
        }
        summary["review_csv"] = "quality_scored_candidates.csv"
        summary["review_markdown"] = "clip_pack/clip_candidates.md"
        summary_path = destination / "pipeline_summary.json"
        with summary_path.open("x", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
            handle.write("\\n")
        return summary
    except Exception:
        # This directory was created exclusively by this invocation. Remove
        # only its partial outputs; never alter a pre-existing owner directory.
        shutil.rmtree(destination, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a local scored clip-review pack from permitted chat events and measured clock anchors."
    )
    parser.add_argument("events", type=Path, help="JSON chat event batch with a valid analyze_chat permission record")
    parser.add_argument("--clock-anchors-json", required=True, type=Path, help="at least three measured same-source chat/media anchors")
    parser.add_argument("--output-dir", type=Path, default=Path("aro_pipeline_run"), help="new output directory; existing directories are never overwritten")
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
        summary = run_pipeline(
            args.events, args.clock_anchors_json, args.output_dir, config=config,
        )
        print(json.dumps(summary, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"Pipeline stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
