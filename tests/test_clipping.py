"""Safety and behavior tests for local FFmpeg clipping."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.clipping import ClipRenderError, render_clip


class ClipRenderTests(unittest.TestCase):
    def test_requires_explicit_rights_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            source.write_bytes(b"synthetic")
            with self.assertRaises(PermissionError):
                render_clip(source, Path(folder) / "clip.mp4", 0, 2, rights_confirmed=False)

    def test_rejects_invalid_duration(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            source.write_bytes(b"synthetic")
            with self.assertRaises(ValueError):
                render_clip(source, Path(folder) / "clip.mp4", 3, 2, rights_confirmed=True)

    def test_rejects_long_clip(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            source.write_bytes(b"synthetic")
            with self.assertRaises(ValueError):
                render_clip(source, Path(folder) / "clip.mp4", 0, 181, rights_confirmed=True)

    def test_refuses_to_overwrite_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")
            output.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                render_clip(source, output, 0, 2, rights_confirmed=True)

    def test_uses_argument_list_without_shell_and_creates_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                output.write_bytes(b"synthetic mp4")
                return None

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg) as run:
                result = render_clip(source, output, 1, 4, rights_confirmed=True)
            self.assertEqual(result, output.resolve())
            self.assertEqual(output.read_bytes(), b"synthetic mp4")
            args, kwargs = run.call_args
            self.assertIsInstance(args[0], list)
            self.assertTrue(kwargs["check"])
            self.assertEqual(args[0][args[0].index("-t") + 1], "3.000")
            self.assertNotIn("shell", kwargs)

    def test_reports_missing_ffmpeg(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            source.write_bytes(b"synthetic")
            with patch("backend.app.clipping.subprocess.run", side_effect=FileNotFoundError):
                with self.assertRaises(ClipRenderError):
                    render_clip(source, Path(folder) / "clip.mp4", 0, 2, rights_confirmed=True)


if __name__ == "__main__":
    unittest.main()
