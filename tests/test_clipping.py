"""Safety and behavior tests for local FFmpeg clipping."""

import os
import shutil
import subprocess
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

    def test_rejects_symlink_source_before_invoking_ffmpeg(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "source.mov"
            selected = root / "selected.mov"
            target.write_bytes(b"synthetic")
            try:
                selected.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable on this runner")
            with patch("backend.app.clipping.subprocess.run") as run:
                with self.assertRaisesRegex(ValueError, "symbolic links"):
                    render_clip(selected, root / "clip.mp4", 0, 2, rights_confirmed=True)
            run.assert_not_called()

    def test_rejects_invalid_input_and_output_path_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.mov"
            source.write_bytes(b"synthetic")
            with patch("backend.app.clipping.subprocess.run") as run:
                for invalid in (None, 7, [], {}, "", "   "):
                    with self.subTest(argument="input_path", value=invalid):
                        with self.assertRaisesRegex(ValueError, "input_path must be a non-empty"):
                            render_clip(invalid, root / "clip.mp4", 0, 2, rights_confirmed=True)
                    with self.subTest(argument="output_path", value=invalid):
                        with self.assertRaisesRegex(ValueError, "output_path must be a non-empty"):
                            render_clip(source, invalid, 0, 2, rights_confirmed=True)
                run.assert_not_called()

    def test_rejects_invalid_ffmpeg_executable_before_invoking_process(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            source.write_bytes(b"synthetic")
            with patch("backend.app.clipping.subprocess.run") as run:
                for executable in ("", "   ", None, 7, Path("ffmpeg")):
                    with self.subTest(executable=executable):
                        with self.assertRaisesRegex(ValueError, "ffmpeg_binary must be a non-empty"):
                            render_clip(
                                source,
                                Path(folder) / "clip.mp4",
                                0,
                                2,
                                rights_confirmed=True,
                                ffmpeg_binary=executable,
                            )
                run.assert_not_called()

    def test_rejects_nul_in_ffmpeg_executable_before_invoking_process(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            source.write_bytes(b"synthetic")
            with patch("backend.app.clipping.subprocess.run") as run:
                with self.assertRaisesRegex(ValueError, "ffmpeg_binary must not contain NUL"):
                    render_clip(
                        source,
                        Path(folder) / "clip.mp4",
                        0,
                        2,
                        rights_confirmed=True,
                        ffmpeg_binary="ffmpeg\\x00malicious",
                    )
                run.assert_not_called()

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

    def test_rejects_unrepresentable_and_non_numeric_clip_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            source.write_bytes(b"synthetic")
            with patch("backend.app.clipping.subprocess.run") as run:
                invalid_bounds = (
                    (10 ** 400, 2),
                    (0, 10 ** 400),
                    ("1", 2),
                    (0, "2"),
                )
                for start, end in invalid_bounds:
                    with self.subTest(start_type=type(start).__name__, end_type=type(end).__name__):
                        with self.assertRaisesRegex(ValueError, "finite numeric"):
                            render_clip(source, Path(folder) / "clip.mp4", start, end, rights_confirmed=True)
                run.assert_not_called()

    def test_rejects_boolean_clip_bounds_before_invoking_ffmpeg(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            source.write_bytes(b"synthetic")
            with patch("backend.app.clipping.subprocess.run") as run:
                for start, end in ((True, 2), (False, 2), (0, True), (0, False)):
                    with self.subTest(start=start, end=end):
                        with self.assertRaisesRegex(ValueError, "not booleans"):
                            render_clip(source, Path(folder) / "clip.mp4", start, end, rights_confirmed=True)
                run.assert_not_called()

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

    def test_rejects_output_symlink_created_during_parent_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.mov"
            source.write_bytes(b"synthetic")
            output = root / "clip.mp4"
            outside = root / "outside"
            outside.mkdir()
            target = outside / "redirected.mp4"
            original_resolve = Path.resolve

            def create_symlink_during_parent_resolution(path, *args, **kwargs):
                if path == root and not output.exists() and not output.is_symlink():
                    try:
                        output.symlink_to(target)
                    except (OSError, NotImplementedError):
                        self.skipTest("symlink creation is unavailable on this runner")
                return original_resolve(path, *args, **kwargs)

            with patch.object(Path, "resolve", new=create_symlink_during_parent_resolution):
                with patch("backend.app.clipping.subprocess.run") as run:
                    with self.assertRaisesRegex(FileExistsError, "symbolic link|already exists"):
                        render_clip(source, output, 0, 2, rights_confirmed=True)
            self.assertTrue(output.is_symlink())
            self.assertFalse(target.exists())
            run.assert_not_called()

    def test_rejects_dangling_symlink_output_without_creating_target(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.mov"
            output = root / "clip.mp4"
            target = root / "redirected.mp4"
            source.write_bytes(b"synthetic")
            try:
                output.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is unavailable on this runner")
            with self.assertRaisesRegex(FileExistsError, "symbolic link"):
                render_clip(source, output, 0, 2, rights_confirmed=True)
            self.assertFalse(target.exists())
            self.assertTrue(output.is_symlink())

    def test_uses_argument_list_without_shell_and_creates_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                temporary_output = Path(command[-1])
                self.assertNotEqual(temporary_output, output)
                temporary_output.write_bytes(b"synthetic mp4")
                return None

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg) as run:
                result = render_clip(source, output, 1, 4, rights_confirmed=True)
            self.assertEqual(result, output.resolve())
            self.assertEqual(output.read_bytes(), b"synthetic mp4")
            args, kwargs = run.call_args
            self.assertIsInstance(args[0], list)
            self.assertTrue(kwargs["check"])
            self.assertEqual(args[0][args[0].index("-t") + 1], "3.000")
            video_filter = args[0][args[0].index("-vf") + 1]
            self.assertIn("scale=1080:1920:force_original_aspect_ratio=decrease", video_filter)
            self.assertIn("pad=1080:1920", video_filter)
            self.assertIn("setsar=1", video_filter)
            self.assertNotIn("shell", kwargs)
            self.assertEqual(kwargs["timeout"], 180)
            self.assertFalse(list(Path(folder).glob(".clip-*")))

    def test_refuses_to_publish_when_source_changes_during_ffmpeg(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"original synthetic source")

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"synthetic rendered bytes")
                # Simulate another process editing the same inode while FFmpeg
                # is reading it, rather than replacing the source pathname.
                source.write_bytes(b"modified source with different size")

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg):
                with self.assertRaisesRegex(
                    ClipRenderError, "changed during FFmpeg rendering"
                ):
                    render_clip(source, output, 0, 2, rights_confirmed=True)

            self.assertFalse(output.exists())
            self.assertFalse(list(Path(folder).glob(".clip-*")))

    def test_fsyncs_rendered_file_before_publish_and_parent_directory_after(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")
            events = []
            real_fsync = os.fsync
            real_link = os.link

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"durable synthetic mp4")

            def recording_fsync(descriptor):
                events.append("file_fsync")
                return real_fsync(descriptor)

            def recording_link(source_path, destination_path):
                events.append("link")
                return real_link(source_path, destination_path)

            def recording_directory_sync(path):
                events.append("directory_fsync")

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg), patch(
                "backend.app.clipping.os.fsync", side_effect=recording_fsync
            ), patch("backend.app.clipping.os.link", side_effect=recording_link), patch(
                "backend.app.clipping._fsync_parent_directory", side_effect=recording_directory_sync
            ):
                self.assertEqual(
                    render_clip(source, output, 0, 2, rights_confirmed=True), output.resolve()
                )

            self.assertEqual(events, ["file_fsync", "link", "directory_fsync"])

    def test_file_sync_failure_does_not_publish_final_output(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"unsynchronized output")

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg), patch(
                "backend.app.clipping.os.fsync", side_effect=OSError("simulated file sync failure")
            ), patch("backend.app.clipping.os.link") as link:
                with self.assertRaisesRegex(ClipRenderError, "synchronized before publication"):
                    render_clip(source, output, 0, 2, rights_confirmed=True)

            link.assert_not_called()
            self.assertFalse(output.exists())
            self.assertFalse(list(Path(folder).glob(".clip-*")))

    def test_directory_sync_failure_preserves_published_output_and_raises(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"published output")

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg), patch(
                "backend.app.clipping._fsync_parent_directory",
                side_effect=OSError("simulated directory sync failure"),
            ):
                with self.assertRaisesRegex(ClipRenderError, "output is preserved for inspection"):
                    render_clip(source, output, 0, 2, rights_confirmed=True)

            self.assertEqual(output.read_bytes(), b"published output")

    def test_concurrent_output_collision_preserves_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.mov"
            output = Path(folder) / "clip.mp4"
            source.write_bytes(b"synthetic")

            def fake_ffmpeg(command, **kwargs):
                Path(command[-1]).write_bytes(b"first render")
                output.write_bytes(b"second render owns destination")

            with patch("backend.app.clipping.subprocess.run", side_effect=fake_ffmpeg):
                with self.assertRaisesRegex(FileExistsError, "created by another render"):
                    render_clip(source, output, 0, 2, rights_confirmed=True)
            self.assertEqual(output.read_bytes(), b"second render owns destination")
            self.assertFalse(list(Path(folder).glob(".clip-*")))

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
            self.assertFalse(list(Path(folder).glob(".clip-*")))

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is not installed on this runner")
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
