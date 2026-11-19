"""Unit tests for permission-gated local video rendering."""
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from backend.app.models import PermissionRecord
from backend.app.video_clipper import ClipError, render_clip


class VideoClipperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.source = self.root / "source.mp4"
        self.source.write_bytes(b"test fixture, not a playable video")
        now = datetime.now(timezone.utc)
        self.permission = PermissionRecord(
            source_id="local-recording",
            granted_by="owner-attestation",
            scopes=frozenset({"render_video"}),
            granted_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(hours=1),
        )

    def tearDown(self) -> None:
        self.folder.cleanup()

    @patch("backend.app.video_clipper.subprocess.run")
    def test_renders_authorized_clip_to_atomic_destination(self, run) -> None:
        run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="120.0\n", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        ]
        output = self.root / "clip.mp4"
        result = render_clip(
            self.source, output, 10, 30, self.permission,
            confirm_authorized=True, vertical=True,
        )
        self.assertEqual(result, output.resolve())
        self.assertTrue(output.is_file())
        ffmpeg_command = run.call_args_list[1].args[0]
        self.assertIn("1080:1920", ffmpeg_command)
        self.assertNotEqual(ffmpeg_command[-1], str(output.resolve()))
        self.assertTrue(ffmpeg_command[-1].endswith(".tmp.mp4"))
        self.assertFalse(list(self.root.glob("*.tmp.mp4")))
        self.assertIn("-y", ffmpeg_command)

    def test_requires_explicit_authorization_attestation(self) -> None:
        with self.assertRaises(PermissionError):
            render_clip(self.source, self.root / "clip.mp4", 0, 10, self.permission)

    def test_requires_render_video_scope(self) -> None:
        denied = PermissionRecord(
            source_id="local-recording", granted_by="owner",
            scopes=frozenset({"analyze_chat"}),
            granted_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        with self.assertRaises(PermissionError):
            render_clip(
                self.source, self.root / "clip.mp4", 0, 10, denied,
                confirm_authorized=True,
            )

    @patch("backend.app.video_clipper.subprocess.run")
    def test_rejects_range_beyond_source(self, run) -> None:
        run.return_value = subprocess.CompletedProcess([], 0, stdout="20.0", stderr="")
        with self.assertRaises(ClipError):
            render_clip(
                self.source, self.root / "clip.mp4", 15, 10, self.permission,
                confirm_authorized=True,
            )
        self.assertEqual(run.call_count, 1)

    @patch("backend.app.video_clipper.subprocess.run")
    def test_rejects_non_finite_ranges_before_probing(self, run) -> None:
        for start, duration in ((float("nan"), 5), (float("inf"), 5), (0, float("nan")), (0, float("inf"))):
            with self.subTest(start=start, duration=duration):
                with self.assertRaises(ClipError):
                    render_clip(
                        self.source, self.root / "clip.mp4", start, duration,
                        self.permission, confirm_authorized=True,
                    )
        run.assert_not_called()

    @patch("backend.app.video_clipper.subprocess.run")
    def test_rejects_existing_output(self, run) -> None:
        output = self.root / "clip.mp4"
        output.write_bytes(b"keep")
        with self.assertRaises(ClipError):
            render_clip(
                self.source, output, 0, 10, self.permission,
                confirm_authorized=True,
            )
        run.assert_not_called()
        self.assertEqual(output.read_bytes(), b"keep")

    @patch("backend.app.video_clipper.subprocess.run")
    def test_ffmpeg_failure_leaves_no_destination_or_temp_file(self, run) -> None:
        run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="120", stderr=""),
            subprocess.CalledProcessError(1, ["ffmpeg"], stderr="encode failed"),
        ]
        output = self.root / "failed.mp4"
        with self.assertRaises(ClipError):
            render_clip(
                self.source, output, 0, 10, self.permission,
                confirm_authorized=True,
            )
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob(".failed.*.tmp.mp4")), [])

    @patch("backend.app.video_clipper.os.link", side_effect=FileExistsError)
    @patch("backend.app.video_clipper.subprocess.run")
    def test_atomic_publish_refuses_racing_destination(self, run, link) -> None:
        run.side_effect = [
            subprocess.CompletedProcess([], 0, stdout="120", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        ]
        output = self.root / "raced.mp4"
        with self.assertRaisesRegex(ClipError, "refusing to overwrite"):
            render_clip(
                self.source, output, 0, 10, self.permission,
                confirm_authorized=True,
            )
        link.assert_called_once()
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob(".raced.*.tmp.mp4")), [])


if __name__ == "__main__":
    unittest.main()
