"""Safety and integration tests for the local FFmpeg renderer."""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.render import RenderError, render_clip


class RenderUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.source = self.folder / "source video.mp4"
        self.source.write_bytes(b"authorized test fixture")
        self.output = self.folder / "clip.mp4"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def render(self, **overrides):
        options = {
            "start_seconds": 2,
            "duration_seconds": 12,
            "rights_confirmed": True,
        }
        options.update(overrides)
        return render_clip(self.source, self.output, **options)

    def test_requires_explicit_rights_confirmation(self) -> None:
        with self.assertRaises(PermissionError):
            self.render(rights_confirmed=False)

    def test_rejects_invalid_time_bounds(self) -> None:
        for start, duration in [(-1, 5), (0, 0), (0, 181), (float('nan'), 5), (0, float('inf'))]:
            with self.subTest(start=start, duration=duration):
                with self.assertRaises(ValueError):
                    self.render(start_seconds=start, duration_seconds=duration)

    def test_refuses_to_overwrite(self) -> None:
        self.output.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            self.render()
        self.assertEqual(self.output.read_bytes(), b"keep")

    @patch("backend.app.render.os.link")
    @patch("backend.app.render.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("backend.app.render.subprocess.run")
    def test_concurrent_destination_creation_is_never_overwritten(
        self, run, _which, link
    ) -> None:
        def fake_run(command, **kwargs):
            Path(command[-1]).write_bytes(b"rendered review clip")
            return subprocess.CompletedProcess(command, 0, "", "")

        def concurrent_creator(_source, destination):
            Path(destination).write_bytes(b"concurrent owner file")
            raise FileExistsError("destination was created concurrently")

        run.side_effect = fake_run
        link.side_effect = concurrent_creator

        with self.assertRaises(RenderError):
            self.render()

        self.assertEqual(self.output.read_bytes(), b"concurrent owner file")
        self.assertEqual(list(self.folder.glob(".clip.*.mp4")), [])

    def test_rejects_same_input_and_output(self) -> None:
        with self.assertRaises(ValueError):
            render_clip(
                self.source, self.source, start_seconds=0, duration_seconds=5,
                rights_confirmed=True,
            )

    @patch("backend.app.render.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("backend.app.render.subprocess.run")
    def test_uses_argument_list_and_creates_review_file(self, run, _which) -> None:
        def fake_run(command, **kwargs):
            Path(command[-1]).write_bytes(b"mp4 fixture")
            return subprocess.CompletedProcess(command, 0, "", "")
        run.side_effect = fake_run

        result = self.render()
        self.assertEqual(result, self.output)
        command = run.call_args.args[0]
        self.assertIsInstance(command, list)
        self.assertIn("-y", command)
        self.assertTrue(Path(command[-1]).name.startswith(".clip."))
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertIn("-map", command)
        self.assertEqual(run.call_args.kwargs["timeout"], 300)

    @patch("backend.app.render.shutil.which", return_value=None)
    def test_fails_closed_when_ffmpeg_is_missing(self, _which) -> None:
        with self.assertRaises(RenderError):
            self.render()
        self.assertFalse(self.output.exists())

    @patch("backend.app.render.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("backend.app.render.subprocess.run")
    def test_removes_temporary_file_after_timeout(self, run, _which) -> None:
        def fake_run(command, **kwargs):
            Path(command[-1]).write_bytes(b"partial")
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        run.side_effect = fake_run
        with self.assertRaises(RenderError):
            self.render()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.folder.glob(".clip.*.mp4")), [])

    @patch("backend.app.render.shutil.which", return_value="/usr/bin/ffmpeg")
    @patch("backend.app.render.subprocess.run")
    def test_removes_partial_output_after_ffmpeg_failure(self, run, _which) -> None:
        def fake_run(command, **kwargs):
            Path(command[-1]).write_bytes(b"partial")
            return subprocess.CompletedProcess(command, 1, "", "synthetic failure")
        run.side_effect = fake_run
        with self.assertRaises(RenderError):
            self.render()
        self.assertFalse(self.output.exists())


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/FFprobe not installed")
class RenderEndToEndTests(unittest.TestCase):
    def test_synthetic_video_renders_and_has_expected_duration(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "synthetic.mp4"
            output = root / "review-clip.mp4"
            generated = subprocess.run(
                [
                    shutil.which("ffmpeg"), "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i", "testsrc=size=160x120:rate=15",
                    "-t", "3", "-pix_fmt", "yuv420p", "-c:v", "libx264",
                    "-y", str(source),
                ],
                capture_output=True, text=True, timeout=60, shell=False,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)

            render_clip(
                source, output, start_seconds=0.5, duration_seconds=1.0,
                rights_confirmed=True,
            )
            probe = subprocess.run(
                [
                    shutil.which("ffprobe"), "-v", "error", "-show_entries",
                    "format=duration", "-of", "json", str(output),
                ],
                capture_output=True, text=True, timeout=30, shell=False,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            duration = float(json.loads(probe.stdout)["format"]["duration"])
            self.assertGreaterEqual(duration, 0.8)
            self.assertLessEqual(duration, 1.3)
            self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
