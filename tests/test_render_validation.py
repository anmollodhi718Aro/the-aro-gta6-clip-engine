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

    def _probe_payload(self, duration="10.0", width=1920, height=1080):
        return (
            '{"format":{"duration":"' + str(duration) + '"},'
            '"streams":[{"codec_type":"video","width":' + str(width)
            + ',"height":' + str(height)
            + '},{"codec_type":"audio"}]}'
        )

    def test_accepts_readable_landscape_output_and_unicode_path(self):
        with patch("backend.app.render_validation.subprocess.run") as run:
            run.return_value.stdout = self._probe_payload()
            info = verify_rendered_media(self.output, expected_duration_seconds=10)
        self.assertEqual(info.width, 1920)
        self.assertEqual(info.height, 1080)
        self.assertTrue(info.has_audio)
        self.assertEqual(run.call_args.args[0][-1], str(self.output.resolve()))

    def test_requires_exact_vertical_dimensions(self):
        with patch("backend.app.render_validation.subprocess.run") as run:
            run.return_value.stdout = self._probe_payload(width=1080, height=1920)
            info = verify_rendered_media(self.output, expected_duration_seconds=10, vertical=True)
        self.assertEqual((info.width, info.height), (1080, 1920))

        with patch("backend.app.render_validation.subprocess.run") as run:
            run.return_value.stdout = self._probe_payload(width=1920, height=1080)
            with self.assertRaisesRegex(ValueError, "must be 1080x1920"):
                verify_rendered_media(self.output, expected_duration_seconds=10, vertical=True)

    def test_rejects_duration_mismatch(self):
        with patch("backend.app.render_validation.subprocess.run") as run:
            run.return_value.stdout = self._probe_payload(duration="4")
            with self.assertRaisesRegex(ValueError, "differs from expected"):
                verify_rendered_media(self.output, expected_duration_seconds=10)

    def test_rejects_unreadable_or_incomplete_probe_metadata(self):
        for raw in ("not json", '{"format":{"duration":"10"},"streams":[]}',
                    '{"format":{"duration":"nan"},"streams":[{"codec_type":"video","width":1,"height":1}]}'):
            with self.subTest(raw=raw), patch("backend.app.render_validation.subprocess.run") as run:
                run.return_value.stdout = raw
                with self.assertRaises(ValueError):
                    verify_rendered_media(self.output, expected_duration_seconds=10)

    def test_rejects_empty_output_before_running_ffprobe(self):
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
