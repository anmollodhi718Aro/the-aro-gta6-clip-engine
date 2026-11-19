"""Tests for safe local ffprobe metadata inspection."""
import subprocess
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
            self.assertEqual(run.call_args.kwargs["timeout"], 30)
            self.assertTrue(run.call_args.kwargs["check"])
            self.assertTrue(run.call_args.kwargs["capture_output"])

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

    def test_reports_ffprobe_timeout(self):
        with tempfile.TemporaryDirectory() as folder:
            media = Path(folder) / "sample.mp4"
            media.write_bytes(b"synthetic")
            with patch(
                "backend.app.media_probe.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="ffprobe", timeout=30),
            ):
                with self.assertRaisesRegex(RuntimeError, "timed out"):
                    probe_media(media)

    def test_reports_ffprobe_nonzero_exit_without_leaking_traceback(self):
        with tempfile.TemporaryDirectory() as folder:
            media = Path(folder) / "sample.mp4"
            media.write_bytes(b"synthetic")
            error = subprocess.CalledProcessError(
                1, ["ffprobe"], stderr="invalid media container",
            )
            with patch("backend.app.media_probe.subprocess.run", side_effect=error):
                with self.assertRaisesRegex(RuntimeError, "invalid media container"):
                    probe_media(media)


if __name__ == "__main__":
    unittest.main()
