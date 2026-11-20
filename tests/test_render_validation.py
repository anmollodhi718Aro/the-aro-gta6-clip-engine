"""Regression tests for validating rendered MP4 outputs before publication."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.render_validation import verify_rendered_media


class RenderedMediaValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name) / "clip with spaces – 日本語.mp4"
        self.output.write_bytes(b"synthetic mp4")

    def tearDown(self):
        self.temp.cleanup()

    def _payload(self, duration="10.0", width=1920, height=1080, format_name="mov,mp4,m4a,3gp,3g2,mj2"):
        return (
            '{"format":{"format_name":"' + format_name + '","duration":"' + str(duration) + '"},'
            '"streams":[{"codec_type":"video","width":' + str(width)
            + ',"height":' + str(height)
            + '},{"codec_type":"audio"}]}'
        )

    def test_accepts_valid_landscape_metadata_and_unicode_path(self):
        with patch("backend.app.render_validation.subprocess.run") as run:
            run.return_value.stdout = self._payload()
            info = verify_rendered_media(self.output, expected_duration_seconds=10)
        self.assertEqual((info.width, info.height), (1920, 1080))
        self.assertTrue(info.has_audio)
        self.assertEqual(run.call_args.args[0][-1], str(self.output.resolve()))
        command = run.call_args.args[0]
        self.assertEqual(command[3], "-show_entries")
        self.assertEqual(command[4], "format=format_name,duration:stream=codec_type,width,height")

    def test_rejects_non_mp4_container_even_when_filename_ends_in_mp4(self):
        with patch("backend.app.render_validation.subprocess.run") as run:
            run.return_value.stdout = self._payload(format_name="matroska,webm")
            with self.assertRaisesRegex(ValueError, "not an MP4 container"):
                verify_rendered_media(self.output, expected_duration_seconds=10)

    def test_requires_1080x1920_for_vertical_output(self):
        with patch("backend.app.render_validation.subprocess.run") as run:
            run.return_value.stdout = self._payload(width=1080, height=1920)
            info = verify_rendered_media(self.output, expected_duration_seconds=10, vertical=True)
        self.assertEqual((info.width, info.height), (1080, 1920))

        with patch("backend.app.render_validation.subprocess.run") as run:
            run.return_value.stdout = self._payload(width=1920, height=1080)
            with self.assertRaisesRegex(ValueError, "must be 1080x1920"):
                verify_rendered_media(self.output, expected_duration_seconds=10, vertical=True)

    def test_rejects_duration_mismatch_and_bounded_tolerance(self):
        cases = [("4", 10), ("0.01", 0.1), ("60.6", 60)]
        for actual, expected in cases:
            with self.subTest(actual=actual, expected=expected), patch(
                "backend.app.render_validation.subprocess.run"
            ) as run:
                run.return_value.stdout = self._payload(duration=actual)
                with self.assertRaisesRegex(ValueError, "differs from expected"):
                    verify_rendered_media(self.output, expected_duration_seconds=expected)

    def test_rejects_incomplete_or_non_finite_metadata(self):
        malformed = [
            "not json",
            '{"format":{"format_name":"mp4","duration":"10"},"streams":[]}',
            '{"format":{"format_name":"mp4","duration":"nan"},"streams":[{"codec_type":"video","width":1,"height":1}]}',
            '{"format":{"duration":"10"},"streams":[{"codec_type":"video","width":1,"height":1}]}',
        ]
        for raw in malformed:
            with self.subTest(raw=raw), patch(
                "backend.app.render_validation.subprocess.run"
            ) as run:
                run.return_value.stdout = raw
                with self.assertRaises(ValueError):
                    verify_rendered_media(self.output, expected_duration_seconds=10)

    def test_require_audio_rejects_silent_mp4_but_default_allows_it(self):
        silent_payload = self._payload().replace(',{"codec_type":"audio"}', '')
        with patch("backend.app.render_validation.subprocess.run") as run:
            run.return_value.stdout = silent_payload
            info = verify_rendered_media(self.output, expected_duration_seconds=10)
        self.assertFalse(info.has_audio)

        with patch("backend.app.render_validation.subprocess.run") as run:
            run.return_value.stdout = silent_payload
            with self.assertRaisesRegex(ValueError, "must contain an audio stream"):
                verify_rendered_media(
                    self.output, expected_duration_seconds=10, require_audio=True
                )

    def test_rejects_empty_output_without_running_ffprobe(self):
        self.output.write_bytes(b"")
        with patch("backend.app.render_validation.subprocess.run") as run:
            with self.assertRaisesRegex(ValueError, "missing or empty"):
                verify_rendered_media(self.output, expected_duration_seconds=10)
        run.assert_not_called()

    def test_reports_missing_ffprobe(self):
        with patch("backend.app.render_validation.subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RuntimeError, "ffprobe executable not found"):
                verify_rendered_media(self.output, expected_duration_seconds=10)


if __name__ == "__main__":
    unittest.main()
