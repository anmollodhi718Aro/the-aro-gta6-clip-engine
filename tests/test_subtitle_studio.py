"""Tests for transcript-to-SRT formatting and subtitle quality checks."""
import unittest

from backend.app.subtitle_studio import (
    SubtitleSegment, build_subtitles, render_srt, validate_segments,
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


if __name__ == "__main__":
    unittest.main()
