"""Safety and command-construction tests for local clip rendering."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, Mock
from backend.app.clipping import render_local_clip
from backend.app.models import PermissionRecord

class LocalRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.source = self.root / "owned-sample.mp4"
        self.source.write_bytes(b"synthetic test fixture")
        now = datetime.now(timezone.utc)
        self.permission = PermissionRecord(
            source_id="authorized-local-source", granted_by="test-owner",
            scopes=frozenset({"clip_media"}), granted_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=10),
        )
        self.output = self.root / "clip.mp4"

    def tearDown(self) -> None:
        self.folder.cleanup()

    @patch("backend.app.clipping.shutil.which", return_value="/usr/bin/tool")
    @patch("backend.app.clipping.subprocess.run")
    def test_renders_and_validates_local_clip(self, run: Mock, _which: Mock) -> None:
        run.side_effect = [
            Mock(returncode=0, stderr="", stdout=""),
            Mock(returncode=0, stderr="", stdout='{"format":{"duration":"12.0"},"streams":[{"codec_type":"video","codec_name":"h264"}]}'),
        ]
        result = render_local_clip(
            self.source, self.output, source_id="authorized-local-source",
            permission=self.permission, start_seconds=20, duration_seconds=12, confirmed=True,
        )
        self.assertEqual(result.duration_seconds, 12.0)
        self.assertEqual(result.video_codec, "h264")
        command = run.call_args_list[0].args[0]
        self.assertIn("-protocol_whitelist", command)
        self.assertIn("file", command)
        self.assertIn("-n", command)
        self.assertNotIn("-y", command)
        self.assertFalse(any("http://" in str(arg) or "https://" in str(arg) for arg in command))

    @patch("backend.app.clipping.subprocess.run")
    def test_requires_explicit_confirmation(self, run: Mock) -> None:
        with patch("backend.app.clipping.shutil.which", return_value="/usr/bin/tool"):
            with self.assertRaises(PermissionError):
                render_local_clip(self.source, self.output, source_id="authorized-local-source",
                    permission=self.permission, start_seconds=0, duration_seconds=5)
        run.assert_not_called()

    @patch("backend.app.clipping.subprocess.run")
    def test_rejects_missing_clip_permission(self, run: Mock) -> None:
        denied = PermissionRecord(source_id="authorized-local-source", granted_by="test-owner",
            scopes=frozenset({"analyze_chat"}), granted_at=datetime.now(timezone.utc)-timedelta(minutes=1))
        with self.assertRaises(PermissionError):
            render_local_clip(self.source, self.output, source_id="authorized-local-source",
                permission=denied, start_seconds=0, duration_seconds=5, confirmed=True)
        run.assert_not_called()

    def test_rejects_source_mismatch_and_invalid_ranges(self) -> None:
        with self.assertRaises(PermissionError):
            render_local_clip(self.source, self.output, source_id="different-source",
                permission=self.permission, start_seconds=0, duration_seconds=5, confirmed=True)
        for start, duration in [(-1, 5), (0, 0), (0, 601), (float("nan"), 5)]:
            with self.assertRaises(ValueError):
                render_local_clip(self.source, self.output, source_id="authorized-local-source",
                    permission=self.permission, start_seconds=start, duration_seconds=duration, confirmed=True)

    @patch("backend.app.clipping.shutil.which", return_value="/usr/bin/tool")
    @patch("backend.app.clipping.subprocess.run")
    def test_refuses_to_overwrite_existing_output(self, run: Mock, _which: Mock) -> None:
        self.output.write_bytes(b"keep this")
        with self.assertRaises(FileExistsError):
            render_local_clip(self.source, self.output, source_id="authorized-local-source",
                permission=self.permission, start_seconds=0, duration_seconds=5, confirmed=True)
        run.assert_not_called()

if __name__ == "__main__":
    unittest.main()
