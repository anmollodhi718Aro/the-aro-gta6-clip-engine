"""Human-approved batch rendering from a measured clip-candidate CSV.

Dry-run is the default. Rendering requires explicit row approvals, a local
media file, an execution flag, and rights confirmation for that media.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

from .clipping import MAX_CLIP_SECONDS, render_clip
from .output_manager import create_run_directory, make_run_id, write_json_atomic


REQUIRED_COLUMNS = {"start_seconds", "end_seconds", "renderable"}


def parse_approvals(value: str) -> set[int]:
    try:
        approved = {int(item.strip()) for item in value.split(",") if item.strip()}
    except ValueError as exc:
        raise ValueError("approvals must be comma-separated positive row numbers") from exc
    if not approved or any(number < 1 for number in approved):
        raise ValueError("at least one positive candidate row number must be approved")
    return approved


def _load_candidates(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or []))
            raise ValueError(f"candidate CSV is missing required columns: {', '.join(missing)}")
        return list(reader)


def _validated_bounds(row: dict[str, str], row_number: int) -> tuple[float, float]:
    try:
        start = float(row["start_seconds"])
        end = float(row["end_seconds"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"candidate row {row_number} has invalid numeric bounds") from exc
    if not math.isfinite(start) or not math.isfinite(end):
        raise ValueError(f"candidate row {row_number} has non-finite bounds")
    if start < 0 or end <= start or end - start > MAX_CLIP_SECONDS:
        raise ValueError(f"candidate row {row_number} has bounds outside renderer limits")
    return start, end


def run_batch(
    csv_path: str | Path,
    media_path: str | Path,
    output_dir: str | Path,
    approved_rows: set[int],
    *,
    execute: bool = False,
    rights_confirmed: bool = False,
    run_id: str | None = None,
) -> list[dict[str, Any]]:
    """Plan or execute approved rows inside a collision-safe per-run folder."""
    source_csv = Path(csv_path).expanduser()
    media = Path(media_path).expanduser()
    output_root = Path(output_dir).expanduser()
    safe_run_id = make_run_id(run_id)
    if not source_csv.is_file():
        raise FileNotFoundError(f"candidate CSV does not exist: {source_csv}")
    if not media.is_file():
        raise FileNotFoundError(f"local media file does not exist: {media}")
    if execute and not rights_confirmed:
        raise PermissionError("execution requires explicit local-media rights confirmation")

    candidates = _load_candidates(source_csv)
    if any(number > len(candidates) for number in approved_rows):
        raise ValueError("an approved row number is outside the candidate CSV")

    run_dir = create_run_directory(output_root, safe_run_id) if execute else output_root / safe_run_id
    report: list[dict[str, Any]] = []
    for number, row in enumerate(candidates, start=1):
        item: dict[str, Any] = {
            "run_id": safe_run_id,
            "candidate_row": number,
            "source_id": row.get("source_id", ""),
            "output_path": "",
            "status": "not_approved",
            "message": "not selected for rendering",
        }
        if number not in approved_rows:
            report.append(item)
            continue
        if str(row.get("renderable", "")).strip().lower() not in {"true", "1", "yes"}:
            item.update(status="blocked", message="candidate is not marked renderable in the review CSV")
            report.append(item)
            continue
        try:
            start, end = _validated_bounds(row, number)
            output_path = run_dir / f"clip_{number:03d}.mp4"
            item["output_path"] = str(output_path)
            if not execute:
                item.update(status="planned", message=f"would render {end - start:.3f} seconds after approval")
            else:
                render_clip(
                    media,
                    output_path,
                    start,
                    end,
                    rights_confirmed=rights_confirmed,
                )
                item.update(status="rendered", message="local clip rendered; manual review still required")
        except (OSError, ValueError, PermissionError, RuntimeError) as exc:
            item.update(status="failed", message=str(exc))
        report.append(item)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or render explicitly approved candidates from a local review CSV."
    )
    parser.add_argument("candidate_csv", type=Path)
    parser.add_argument("--media", required=True, type=Path, help="local media file; remote URLs are not supported")
    parser.add_argument("--output-dir", type=Path, default=Path("rendered_clips"), help="root folder for separate render runs")
    parser.add_argument("--run-id", help="optional safe, unique run folder name; generated when omitted")
    parser.add_argument("--approve", required=True, help="comma-separated 1-based row numbers approved by a human")
    parser.add_argument("--execute", action="store_true", help="perform local rendering; default is dry-run")
    parser.add_argument("--confirm-rights", action="store_true", help="confirm authorization for this exact local media file")
    parser.add_argument("--report", type=Path, help="optional report path; defaults inside this run folder")
    args = parser.parse_args()

    try:
        if args.execute and not args.confirm_rights:
            raise PermissionError("--execute requires --confirm-rights")
        approvals = parse_approvals(args.approve)
        run_id = make_run_id(args.run_id)
        results = run_batch(
            args.candidate_csv,
            args.media,
            args.output_dir,
            approvals,
            execute=args.execute,
            rights_confirmed=args.confirm_rights,
            run_id=run_id,
        )
        report_path = args.report or (args.output_dir.expanduser() / run_id / "batch_render_report.json")
        write_json_atomic(report_path, results)
        counts: dict[str, int] = {}
        for result in results:
            counts[result["status"]] = counts.get(result["status"], 0) + 1
        print(f"Run: {run_id} | Report: {report_path} | " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
        return 1 if any(item["status"] == "failed" for item in results) else 0
    except (OSError, ValueError, PermissionError) as exc:
        print(f"Batch render stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
