"""Focused regressions for bounded YouTube upload staging.

All media is synthetic. These tests never create an OAuth session or network request.
"""
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.youtube_upload import _copy_stream_with_limit, upload_video


class ChunkedReader:
    """Return deterministic chunks to exercise cumulative copy limits."""

    def __init__(self, chunks):
        self._chunks = iter(chunks)

    def read(self, _size=-1):
        return next(self._chunks, b"")


class YouTubeUploadLimitRegressionTests(unittest.TestCase):
    def test_later_chunk_cannot_push_snapshot_over_limit_and_tempdir_is_cleaned(self):
        with tempfile.TemporaryDirectory(prefix="aro-upload-limit-test-") as directory:
            staging_dir = Path(directory)
            snapshot_path = staging_dir / "approved-upload.mp4"
            with snapshot_path.open("wb") as snapshot:
                with self.assertRaisesRegex(ValueError, "configured upload limit"):
                    _copy_stream_with_limit(
                        ChunkedReader([b"1234", b"5"]),
                        snapshot,
                        max_upload_bytes=4,
                    )
                snapshot.flush()
                self.assertEqual(snapshot_path.read_bytes(), b"1234")
                self.assertLessEqual(snapshot_path.stat().st_size, 4)

        self.assertFalse(staging_dir.exists())

    def test_oversized_direct_call_stops_before_google_client_or_oauth_setup(self):
        with tempfile.TemporaryDirectory(prefix="aro-upload-direct-limit-") as directory:
            root = Path(directory)
            video = root / "oversized.mp4"
            video.write_bytes(b"12345")

            package = types.ModuleType("googleapiclient")
            discovery = types.ModuleType("googleapiclient.discovery")
            http = types.ModuleType("googleapiclient.http")
            discovery.build = Mock()
            http.MediaIoBaseUpload = Mock()
            package.discovery = discovery
            package.http = http
            modules = {
                "googleapiclient": package,
                "googleapiclient.discovery": discovery,
                "googleapiclient.http": http,
            }

            with patch.dict("sys.modules", modules):
                with patch("backend.app.youtube_upload._authorize_google") as authorize:
                    with self.assertRaisesRegex(ValueError, "configured upload limit"):
                        upload_video(
                            video,
                            {"snippet": {"title": "Synthetic"}, "status": {"privacyStatus": "private"}},
                            client_secrets=root / "client.json",
                            token_path=root / "token.json",
                            rights_report_path=root / "rights.json",
                            approval_record_path=root / "approval.json",
                            rights_db_path=root / "rights.sqlite3",
                            clip_id="synthetic-clip",
                            source_id="synthetic-source",
                            owner_approved=True,
                            rights_confirmed=True,
                            max_upload_bytes=4,
                        )

            discovery.build.assert_not_called()
            http.MediaIoBaseUpload.assert_not_called()
            authorize.assert_not_called()
            self.assertFalse((root / "token.json").exists())


if __name__ == "__main__":
    unittest.main()
