"""Build and validate subtitle files from an operator-supplied transcript.

This module does not transcribe audio or access media. It formats timed text
segments supplied by the operator and reports timing/text quality issues.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .output_manager import write_texts_no_overwrite


_TIMESTAMP = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
_TAGS = re.compile(r"<[^>]*>")


def _parse_time(value: str) -> int:
    match = _TIMESTAMP.fullmatch(value)
    if not match:
        raise ValueError(f"invalid SRT timestamp: {value!r}")
    hours, minutes, seconds, millis = map(int, match.groups())
    if minutes >= 60 or seconds >= 60:
        raise ValueError(f"invalid SRT timestamp: {value!r}")
    return (((hours * 60 + minutes) * 60 + seconds) * 1000) + millis


def _format_time(milliseconds: int) -> str:
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


@dataclass(frozen=True)
class SubtitleSegment:
    start_ms: int
    end_ms: int
    text: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SubtitleSegment":
        start = _parse_time(str(value["start"]))
        end = _parse_time(str(value["end"]))
        text = str(value.get("text", "")).strip()
        if not text:
            raise ValueError("subtitle text cannot be empty")
        if end <= start:
            raise ValueError("subtitle end must be after start")
        return cls(start, end, text)


def validate_segments(
    segments: list[SubtitleSegment],
    *,
    max_chars_per_line: int = 42,
    max_lines: int = 2,
    max_cps: float = 20.0,
) -> list[dict[str, Any]]:
    """Return actionable warnings; do not silently rewrite transcript content."""
    if max_chars_per_line < 1 or max_lines < 1 or max_cps <= 0:
        raise ValueError("subtitle quality limits must be positive")
    issues: list[dict[str, Any]] = []
    previous_start = -1
    previous_end = -1
    for index, segment in enumerate(segments, start=1):
        if segment.start_ms < previous_start:
            issues.append({"index": index, "code": "non_monotonic_start",
                           "message": "segment starts before the previous segment"})
        if segment.start_ms < previous_end:
            issues.append({"index": index, "code": "overlap",
                           "message": "segment overlaps the previous segment"})
        lines = segment.text.splitlines() or [segment.text]
        if len(lines) > max_lines:
            issues.append({"index": index, "code": "too_many_lines",
                           "message": f"subtitle has {len(lines)} lines; limit is {max_lines}"})
        if any(len(line) > max_chars_per_line for line in lines):
            issues.append({"index": index, "code": "line_too_long",
                           "message": f"one or more lines exceed {max_chars_per_line} characters"})
        duration_seconds = (segment.end_ms - segment.start_ms) / 1000
        visible_chars = len(re.sub(r"\s+", " ", _TAGS.sub("", segment.text)).strip())
        cps = visible_chars / duration_seconds
        if cps > max_cps:
            issues.append({"index": index, "code": "reading_speed",
                           "message": f"reading speed {cps:.1f} chars/sec exceeds {max_cps:.1f}"})
        previous_start, previous_end = segment.start_ms, segment.end_ms
    return issues


def render_srt(segments: list[SubtitleSegment]) -> str:
    """Render validated-format segments to SRT; quality warnings remain separate."""
    blocks = []
    for index, segment in enumerate(segments, start=1):
        blocks.append(
            f"{index}\n{_format_time(segment.start_ms)} --> "
            f"{_format_time(segment.end_ms)}\n{segment.text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def build_subtitles(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("segments")
    if not isinstance(raw, list):
        raise ValueError("input must contain a segments array")
    segments = [SubtitleSegment.from_dict(item) for item in raw]
    for previous, current in zip(segments, segments[1:]):
        if current.start_ms < previous.start_ms:
            raise ValueError("segments must be supplied in chronological order")
    issues = validate_segments(segments)
    return {
        "srt": render_srt(segments),
        "segment_count": len(segments),
        "quality_passed": not issues,
        "issues": issues,
        "transcription_performed": False,
        "human_review_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Format an operator-supplied timed transcript as SRT and run subtitle checks."
    )
    parser.add_argument("transcript", type=Path, help="JSON file containing timed segments")
    parser.add_argument("--output", type=Path, default=Path("subtitles.srt"))
    parser.add_argument("--report", type=Path, default=Path("subtitle_quality.json"))
    args = parser.parse_args()
    try:
        if args.output.expanduser().resolve() == args.report.expanduser().resolve():
            raise ValueError("subtitle output and quality report must use different file paths")
        payload = json.loads(args.transcript.read_text(encoding="utf-8"))
        result = build_subtitles(payload)
        report = {key: value for key, value in result.items() if key != "srt"}
        # Publish the SRT and its quality report as one no-overwrite operation.
        # If either destination exists or publication fails, newly-created
        # sibling outputs are rolled back rather than leaving a mismatched pair.
        write_texts_no_overwrite({
            args.output: result["srt"],
            args.report: json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        })
        print(json.dumps(report, indent=2))
        return 0 if result["quality_passed"] else 1
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Subtitle build stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
