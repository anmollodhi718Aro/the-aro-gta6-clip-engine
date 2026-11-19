"""Tests for safe local ffprobe metadata inspection."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.media_probe import probe_media


class MediaProbeTests(unittest.TestCase):
    def test_parses_local_media_duration_and_format(self):
        with tempfile.TemporaryDirectory() as folder:
            media = Path(folder) / "sample.mp4"
            media.write_bytes(b"synthetic")
            with patch("backend.app.media_probe.subprocess.run") as run:
                run.return_value.stdout = '{"format":{"duration":"123.5","format_name":"mov,mp4"}}'
                info = probe_media(media)
            self.assertEqual(info.duration_seconds, 123.5)
            self.assertEqual(info.format_name, "mov,mp4")
            command = run.call_args.args[0]
            self.assertIsInstance(command, list)
            self.assertEqual(command[-1], str(media.resolve()))

    def test_rejects_non_local_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            probe_media("missing-local-video.mp4")

    def test_rejects_invalid_or_non_positive_duration(self):
        with tempfile.TemporaryDirectory() as folder:
            media = Path(folder) / "sample.mp4"
            media.write_bytes(b"synthetic")
            for raw in ('{"format":{"duration":"nan"}}',
                        '{"format":{"duration":"0"}}',
                        '{"format":{"duration":"-1"}}',
                        '{"format":{}}'):
                with self.subTest(raw=raw), patch("backend.app.media_probe.subprocess.run") as run:
                    run.return_value.stdout = raw
                    with self.assertRaises(ValueError):
                        probe_media(media)

    def test_reports_missing_ffprobe(self):
        with tempfile.TemporaryDirectory() as folder:
            media = Path(folder) / "sample.mp4"
            media.write_bytes(b"synthetic")
            with patch("backend.app.media_probe.subprocess.run", side_effect=FileNotFoundError):
                with self.assertRaisesRegex(RuntimeError, "ffprobe executable not found"):
                    probe_media(media)


if __name__ == "__main__":
    unittest.main()
