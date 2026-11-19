"""Safety and behavior tests for local FFmpeg clipping."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.app.clipping import ClipRenderError, render_clip
from backend.app.media_probe import MediaInfo


class ClipRenderTests(unittest.TestCase):
    def _valid_probe(self, duration: float, *, width: int = 1920, height: int = 1080):
        return MediaInfo(Path("verified.mp4"), duration, "mp4", width, height)

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

    def test_rejects_non_finite_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            source.write_bytes(b"synthetic")
            with self.assertRaises(ValueError):
                render_clip(source, Path(folder) / "clip.mp4", float("nan"), 2, rights_confirmed=True)

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

    def test_uses_argument_list_without_shell_and_creates_verified_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                temporary_output = Path(command[-1])
                self.assertNotEqual(temporary_output, output)
                temporary_output.write_bytes(b"synthetic mp4")
                return None

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg) as run, \
                 patch("backend.app.clipping.probe_media", return_value=self._valid_probe(3.0)) as probe:
                result = render_clip(source, output, 1, 4, rights_confirmed=True)
            self.assertEqual(result, output.resolve())
            self.assertEqual(output.read_bytes(), b"synthetic mp4")
            args, kwargs = run.call_args
            self.assertIsInstance(args[0], list)
            self.assertTrue(kwargs["check"])
            self.assertEqual(args[0][args[0].index("-t") + 1], "3.000")
            self.assertNotIn("shell", kwargs)
            probe.assert_called_once()
            self.assertFalse(list(Path(folder).glob(".clip-*.mp4")))

    def test_rejects_rendered_duration_mismatch_and_cleans_temporary_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")
            with patch("backend.app.clipping.subprocess.run", side_effect=lambda command, **kwargs: Path(command[-1]).write_bytes(b"mp4")), \
                 patch("backend.app.clipping.probe_media", return_value=self._valid_probe(8.0)):
                with self.assertRaisesRegex(ClipRenderError, "duration does not match"):
                    render_clip(source, output, 0, 3, rights_confirmed=True)
            self.assertFalse(output.exists())
            self.assertFalse(list(Path(folder).glob(".clip-*.mp4")))

    def test_rejects_vertical_output_with_wrong_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "vertical.mp4"
            source.write_bytes(b"synthetic")
            with patch("backend.app.clipping.subprocess.run", side_effect=lambda command, **kwargs: Path(command[-1]).write_bytes(b"mp4")), \
                 patch("backend.app.clipping.probe_media", return_value=self._valid_probe(5.0, width=1920, height=1080)):
                with self.assertRaisesRegex(ClipRenderError, "exactly 1080x1920"):
                    render_clip(source, output, 0, 5, rights_confirmed=True, vertical=True)
            self.assertFalse(output.exists())

    def test_rejects_output_when_ffprobe_cannot_verify_video(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")
            with patch("backend.app.clipping.subprocess.run", side_effect=lambda command, **kwargs: Path(command[-1]).write_bytes(b"mp4")), \
                 patch("backend.app.clipping.probe_media", side_effect=ValueError("no video stream")):
                with self.assertRaisesRegex(ClipRenderError, "ffprobe validation"):
                    render_clip(source, output, 0, 2, rights_confirmed=True)
            self.assertFalse(output.exists())
            self.assertFalse(list(Path(folder).glob(".clip-*.mp4")))

    def test_concurrent_output_collision_preserves_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"first render")
                output.write_bytes(b"second render owns destination")

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg), \
                 patch("backend.app.clipping.probe_media", return_value=self._valid_probe(2.0)):
                with self.assertRaisesRegex(FileExistsError, "created by another render"):
                    render_clip(source, output, 0, 2, rights_confirmed=True)
            self.assertEqual(output.read_bytes(), b"second render owns destination")
            self.assertFalse(list(Path(folder).glob(".clip-*.mp4")))

    def test_ffmpeg_failure_does_not_delete_concurrent_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                output.write_bytes(b"another render output")
                raise subprocess.CalledProcessError(1, command, stderr="synthetic failure")

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg):
                with self.assertRaisesRegex(ClipRenderError, "synthetic failure"):
                    render_clip(source, output, 0, 2, rights_confirmed=True)
            self.assertEqual(output.read_bytes(), b"another render output")
            self.assertFalse(list(Path(folder).glob(".clip-*.mp4")))

    def test_vertical_mode_uses_full_frame_9_by_16_layout(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "vertical.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"vertical mp4")

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg) as run, \
                 patch("backend.app.clipping.probe_media", return_value=self._valid_probe(19.0, width=1080, height=1920)):
                result = render_clip(source, output, 1, 20, rights_confirmed=True, vertical=True)

            self.assertEqual(result, output.resolve())
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("-map") + 1], "[v]")
            self.assertIn("-filter_complex", command)
            graph = command[command.index("-filter_complex") + 1]
            self.assertIn("scale=1080:1920", graph)
            self.assertIn("boxblur=20:10", graph)
            self.assertIn("overlay=", graph)
            self.assertIn("yuv420p", command)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg and ffprobe are not both installed on this runner")
    def test_renders_a_generated_synthetic_video(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "synthetic.mp4"
            output = Path(folder) / "clip.mp4"
            subprocess.run(
                [shutil.which("ffmpeg"), "-nostdin", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=160x120:d=3", "-pix_fmt", "yuv420p", str(source)],
                check=True, capture_output=True, timeout=60,
            )
            result = render_clip(source, output, 0.5, 2.0, rights_confirmed=True)
            self.assertTrue(result.is_file())
            self.assertGreater(result.stat().st_size, 0)

    def test_reports_missing_ffmpeg(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            source.write_bytes(b"synthetic")
            with patch("backend.app.clipping.subprocess.run", side_effect=FileNotFoundError):
                with self.assertRaises(ClipRenderError):
                    render_clip(source, Path(folder) / "clip.mp4", 0, 2, rights_confirmed=True)


if __name__ == "__main__":
    unittest.main()
