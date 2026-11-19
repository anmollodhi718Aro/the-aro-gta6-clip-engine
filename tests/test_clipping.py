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

            info = MediaInfo(Path("temporary.mp4"), 3.0, "mov,mp4")
            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg) as run, \
                    patch("backend.app.clipping.probe_media", return_value=info) as probe:
                result = render_clip(source, output, 1, 4, rights_confirmed=True)
            self.assertEqual(result, output.resolve())
            self.assertEqual(output.read_bytes(), b"synthetic mp4")
            probe.assert_called_once()
            self.assertEqual(probe.call_args.kwargs["ffprobe_binary"], "ffprobe")
            args, kwargs = run.call_args
            self.assertIsInstance(args[0], list)
            self.assertTrue(kwargs["check"])
            self.assertEqual(args[0][args[0].index("-t") + 1], "3.000")
            self.assertNotIn("shell", kwargs)
            self.assertFalse(list(Path(folder).glob(".clip-*.mp4")))

    def test_does_not_publish_when_ffprobe_cannot_read_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"not actually a video")

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg), \
                    patch("backend.app.clipping.probe_media", side_effect=ValueError("no video stream")):
                with self.assertRaisesRegex(ClipRenderError, "could not verify"):
                    render_clip(source, output, 0, 2, rights_confirmed=True)
            self.assertFalse(output.exists())
            self.assertFalse(list(Path(folder).glob(".clip-*.mp4")))

    def test_does_not_publish_when_output_duration_is_wrong(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"synthetic but truncated mp4")

            info = MediaInfo(Path("temporary.mp4"), 0.5, "mov,mp4")
            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg), \
                    patch("backend.app.clipping.probe_media", return_value=info):
                with self.assertRaisesRegex(ClipRenderError, "duration does not match"):
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

            info = MediaInfo(Path("temporary.mp4"), 2.0, "mov,mp4")
            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg), \
                    patch("backend.app.clipping.probe_media", return_value=info):
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

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg), \
                    patch("backend.app.clipping.probe_media") as probe:
                with self.assertRaisesRegex(ClipRenderError, "synthetic failure"):
                    render_clip(source, output, 0, 2, rights_confirmed=True)
            probe.assert_not_called()
            self.assertEqual(output.read_bytes(), b"another render output")
            self.assertFalse(list(Path(folder).glob(".clip-*.mp4")))

    def test_vertical_mode_uses_full_frame_9_by_16_layout(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "vertical.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"vertical mp4")

            info = MediaInfo(Path("temporary.mp4"), 19.0, "mov,mp4")
            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg) as run, \
                    patch("backend.app.clipping.probe_media", return_value=info):
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

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg and FFprobe are not both installed on this runner")
    def test_renders_a_generated_synthetic_video(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "synthetic.mp4"
            output = Path(folder) / "clip.mp4"
            subprocess.run(
                [shutil.which("ffmpeg"), "-nostdin", "-hide_banner", "-loglevel", "error",
                 "-f", "lavfi", "-i", "color=c=black:s=160x120:d=3",
                 "-pix_fmt", "yuv420p", str(source)],
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
