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
from .media_probe import probe_media


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


def load_failed_rows(
    report_path: str | Path,
    csv_path: str | Path,
    media_path: str | Path | None = None,
) -> set[int]:
    """Select only failed rows whose candidate and optional media identity still match."""
    report_file = Path(report_path).expanduser()
    with report_file.open("r", encoding="utf-8") as handle:
        previous = json.load(handle)
    if not isinstance(previous, list):
        raise ValueError("retry report must contain a JSON list of candidate results")

    candidates = _load_candidates(Path(csv_path).expanduser())
    current_media_identity = None
    if media_path is not None:
        media = Path(media_path).expanduser().resolve()
        if not media.is_file():
            raise FileNotFoundError(f"local media file does not exist: {media}")
        media_stat = media.stat()
        current_media_identity = {
            "path": str(media),
            "size_bytes": media_stat.st_size,
            "mtime_ns": media_stat.st_mtime_ns,
        }
    failed: set[int] = set()
    for item in previous:
        if not isinstance(item, dict) or item.get("status") != "failed":
            continue
        row_number = item.get("candidate_row")
        if isinstance(row_number, bool) or not isinstance(row_number, int) or row_number < 1 or row_number > len(candidates):
            raise ValueError("retry report contains an invalid failed candidate row")
        if row_number in failed:
            raise ValueError("retry report contains duplicate failed candidate rows")
        source = candidates[row_number - 1]
        if current_media_identity is not None:
            previous_media_identity = item.get("media_identity")
            if not isinstance(previous_media_identity, dict):
                raise ValueError(f"retry report does not record local media identity for candidate row {row_number}")
            if previous_media_identity != current_media_identity:
                raise ValueError(f"local media file changed or differs from the previous render for candidate row {row_number}")
        if str(item.get("source_id", "")) != source.get("source_id", ""):
            raise ValueError(f"candidate row {row_number} no longer matches the retry report")
        try:
            old_start = float(item["start_seconds"])
            old_end = float(item["end_seconds"])
            new_start = float(source["start_seconds"])
            new_end = float(source["end_seconds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"retry report lacks valid measured bounds for candidate row {row_number}") from exc
        if (not all(math.isfinite(value) for value in (old_start, old_end, new_start, new_end))
                or old_start != new_start or old_end != new_end):
            raise ValueError(f"candidate row {row_number} bounds changed since the previous run")
        if str(source.get("renderable", "")).strip().lower() not in {"true", "1", "yes"}:
            raise ValueError(f"candidate row {row_number} is no longer marked renderable")
        failed.add(row_number)

    if not failed:
        raise ValueError("retry report contains no safely retryable failed render rows")
    return failed


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
    run_directory: str | Path | None = None,
    media_duration_seconds: float | None = None,
    ffprobe_binary: str = "ffprobe",
    vertical: bool = False,
) -> list[dict[str, Any]]:
    """Plan or execute approved rows inside a collision-safe per-run folder."""
    source_csv = Path(csv_path).expanduser()
    media = Path(media_path).expanduser()
    output_root = Path(output_dir).expanduser()
    safe_run_id = make_run_id(run_id)
    if not source_csv.is_file():
        raise FileNotFoundError(f"candidate CSV does not exist: {source_csv}")
    media = media.resolve()
    if not media.is_file():
        raise FileNotFoundError(f"local media file does not exist: {media}")
    media_stat = media.stat()
    media_identity = {
        "path": str(media),
        "size_bytes": media_stat.st_size,
        "mtime_ns": media_stat.st_mtime_ns,
    }
    if execute and not rights_confirmed:
        raise PermissionError("execution requires explicit local-media rights confirmation")

    candidates = _load_candidates(source_csv)
    if execute and media_duration_seconds is None:
        media_duration_seconds = probe_media(media, ffprobe_binary=ffprobe_binary).duration_seconds
    if execute and (isinstance(media_duration_seconds, bool) or not isinstance(media_duration_seconds, (int, float)) or not math.isfinite(media_duration_seconds) or media_duration_seconds <= 0):
        raise ValueError("actual media duration must be a finite positive number")
    if any(number > len(candidates) for number in approved_rows):
        raise ValueError("an approved row number is outside the candidate CSV")

    run_dir = (Path(run_directory).expanduser() if run_directory is not None else
               create_run_directory(output_root, safe_run_id) if execute else output_root / safe_run_id)
    report: list[dict[str, Any]] = []
    for number, row in enumerate(candidates, start=1):
        item: dict[str, Any] = {
            "run_id": safe_run_id,
            "candidate_row": number,
            "source_id": row.get("source_id", ""),
            "media_identity": media_identity,
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
            if execute and end > float(media_duration_seconds):
                raise ValueError(f"candidate row {number} ends at {end:.3f}s, beyond actual media duration {float(media_duration_seconds):.3f}s")
            if execute:
                item["media_duration_seconds"] = float(media_duration_seconds)
            item["start_seconds"] = start
            item["end_seconds"] = end
            if vertical:
                item["output_format"] = "1080x1920 (9:16)"
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
                    vertical=vertical,
                )
                # A successful FFmpeg process is not sufficient evidence that
                # the resulting MP4 is readable or has the requested duration.
                output_info = probe_media(output_path, ffprobe_binary=ffprobe_binary)
                actual_duration = output_info.duration_seconds
                expected_duration = end - start
                if abs(actual_duration - expected_duration) > 0.5:
                    raise RuntimeError(
                        f"rendered output duration ({actual_duration:.3f}s) "
                        f"does not match selected range ({expected_duration:.3f}s)"
                    )
                item["output_duration_seconds"] = actual_duration
                item.update(status="rendered", message="local clip rendered and ffprobe-verified; manual review still required")
        except (OSError, ValueError, PermissionError, RuntimeError) as exc:
            item.update(status="failed", message=str(exc))
        report.append(item)
    return report


def batch_exit_code(results: list[dict[str, Any]]) -> int:
    """Return non-zero when an explicitly selected row failed or was blocked."""
    return 1 if any(item.get("status") in {"failed", "blocked"} for item in results) else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run or render explicitly approved candidates from a local review CSV."
    )
    parser.add_argument("candidate_csv", type=Path)
    parser.add_argument("--media", required=True, type=Path, help="local media file; remote URLs are not supported")
    parser.add_argument("--output-dir", type=Path, default=Path("rendered_clips"), help="root folder for separate render runs")
    parser.add_argument("--run-id", help="optional safe, unique run folder name; generated when omitted")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--approve", help="comma-separated 1-based row numbers approved by a human")
    selection.add_argument("--retry-report", type=Path, help="previous batch JSON report; retries only failed rows whose source, media file identity and bounds still match")
    parser.add_argument("--vertical", action="store_true", help="render 1080x1920 (9:16), preserving the full frame over a blurred background")
    parser.add_argument("--execute", action="store_true", help="perform local rendering; default is dry-run")
    parser.add_argument("--confirm-rights", action="store_true", help="confirm authorization for this exact local media file")
    parser.add_argument("--report", type=Path, help="optional report path; defaults inside this run folder")
    parser.add_argument("--ffprobe", default="ffprobe", help="ffprobe executable used to inspect the local media duration")
    args = parser.parse_args()

    try:
        if args.execute and not args.confirm_rights:
            raise PermissionError("--execute requires --confirm-rights")
        approvals = (parse_approvals(args.approve) if args.approve is not None
                     else load_failed_rows(args.retry_report, args.candidate_csv, args.media))
        run_id = make_run_id(args.run_id)
        run_dir = create_run_directory(args.output_dir, run_id)
        results = run_batch(
            args.candidate_csv,
            args.media,
            args.output_dir,
            approvals,
            execute=args.execute,
            rights_confirmed=args.confirm_rights,
            run_id=run_id,
            run_directory=run_dir,
            ffprobe_binary=args.ffprobe,
            vertical=args.vertical,
        )
        report_path = args.report or (run_dir / "batch_render_report.json")
        write_json_atomic(report_path, results)
        counts: dict[str, int] = {}
        for result in results:
            counts[result["status"]] = counts.get(result["status"], 0) + 1
        print(f"Run: {run_id} | Report: {report_path} | " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
        return batch_exit_code(results)
    except (OSError, ValueError, PermissionError, RuntimeError) as exc:
        print(f"Batch render stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
