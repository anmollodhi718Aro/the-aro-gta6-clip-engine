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
    def test_renders_authorized_clip(self, run) -> None:
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
        ffmpeg_command = run.call_args_list[1].args[0]
        self.assertIn("1080:1920", ffmpeg_command)
        self.assertEqual(ffmpeg_command[-1], str(output.resolve()))

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
    def test_rejects_existing_output(self, run) -> None:
        output = self.root / "clip.mp4"
        output.write_bytes(b"keep")
        with self.assertRaises(ClipError):
            render_clip(
                self.source, output, 0, 10, self.permission,
                confirm_authorized=True,
            )
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
