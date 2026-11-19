"""Tests for transcript-to-SRT formatting and subtitle quality checks."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.subtitle_studio import (
    SubtitleSegment, build_subtitles, main, render_srt, validate_segments,
)


class SubtitleStudioTests(unittest.TestCase):
    def test_formats_srt_and_marks_human_review(self):
        result = build_subtitles({"segments": [
            {"start": "00:00:01,000", "end": "00:00:03,000", "text": "Welcome to THE ARO"}
        ]})
        self.assertIn("1\n00:00:01,000 --> 00:00:03,000\nWelcome to THE ARO", result["srt"])
        self.assertTrue(result["quality_passed"])
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["transcription_performed"])

    def test_flags_overlap_and_reading_speed(self):
        segments = [
            SubtitleSegment(0, 500, "A very long subtitle that is difficult to read quickly"),
            SubtitleSegment(400, 900, "Second line"),
        ]
        codes = {issue["code"] for issue in validate_segments(segments)}
        self.assertIn("overlap", codes)
        self.assertIn("reading_speed", codes)

    def test_rejects_invalid_timestamp(self):
        with self.assertRaisesRegex(ValueError, "invalid SRT timestamp"):
            build_subtitles({"segments": [
                {"start": "00:61:00,000", "end": "00:61:01,000", "text": "Bad"}
            ]})

    def test_rejects_empty_text_and_non_positive_duration(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            SubtitleSegment.from_dict({"start": "00:00:00,000", "end": "00:00:01,000", "text": " "})
        with self.assertRaisesRegex(ValueError, "after"):
            SubtitleSegment.from_dict({"start": "00:00:01,000", "end": "00:00:01,000", "text": "x"})

    def test_rejects_out_of_order_segments(self):
        with self.assertRaisesRegex(ValueError, "chronological"):
            build_subtitles({"segments": [
                {"start": "00:00:02,000", "end": "00:00:03,000", "text": "Later"},
                {"start": "00:00:01,000", "end": "00:00:02,000", "text": "Earlier"},
            ]})

    def test_empty_segments_are_valid_empty_output(self):
        result = build_subtitles({"segments": []})
        self.assertEqual(result["srt"], "")
        self.assertTrue(result["quality_passed"])

    def test_cli_publishes_srt_and_report_without_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            transcript = root / "transcript.json"
            output = root / "captions.srt"
            report = root / "quality.json"
            transcript.write_text(json.dumps({"segments": [
                {"start": "00:00:01,000", "end": "00:00:03,000", "text": "Hello"}
            ]}), encoding="utf-8")
            with patch("sys.argv", ["subtitle_studio", str(transcript), "--output", str(output), "--report", str(report)]):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(), 0)
            self.assertIn("Hello", output.read_text(encoding="utf-8"))
            self.assertTrue(json.loads(report.read_text(encoding="utf-8"))["quality_passed"])
            with patch("sys.argv", ["subtitle_studio", str(transcript), "--output", str(output), "--report", str(report)]):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(), 2)
            self.assertEqual(len(list(root.glob("*.srt"))), 1)
            self.assertEqual(len(list(root.glob("*.json"))), 2)

    def test_cli_rolls_back_new_srt_if_report_already_exists(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            transcript = root / "transcript.json"
            output = root / "captions.srt"
            report = root / "quality.json"
            transcript.write_text(json.dumps({"segments": [
                {"start": "00:00:01,000", "end": "00:00:03,000", "text": "Hello"}
            ]}), encoding="utf-8")
            report.write_text("owner data", encoding="utf-8")
            with patch("sys.argv", ["subtitle_studio", str(transcript), "--output", str(output), "--report", str(report)]):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(), 2)
            self.assertFalse(output.exists())
            self.assertEqual(report.read_text(encoding="utf-8"), "owner data")
            self.assertEqual(sorted(path.name for path in root.iterdir()), ["quality.json", "transcript.json"])

    def test_cli_rejects_same_path_for_srt_and_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            transcript = root / "transcript.json"
            shared = root / "same.txt"
            transcript.write_text('{"segments": []}', encoding="utf-8")
            with patch("sys.argv", ["subtitle_studio", str(transcript), "--output", str(shared), "--report", str(shared)]):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(main(), 2)
            self.assertFalse(shared.exists())


if __name__ == "__main__":
    unittest.main()
