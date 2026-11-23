"""Tests for fail-closed local media authorization."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.media import validate_authorized_media_asset
from backend.app.models import PermissionRecord


class MediaAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc)
        self.permission = PermissionRecord(
            source_id="authorized-source",
            granted_by="creator",
            scopes=frozenset({"analyze_chat", "process_media"}),
            granted_at=self.now - timedelta(minutes=5),
            expires_at=self.now + timedelta(minutes=5),
        )

    def test_accepts_existing_local_file_with_media_scope(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            asset = Path(folder) / "owned-recording.mp4"
            asset.write_bytes(b"synthetic-media-placeholder")
            result = validate_authorized_media_asset(
                asset, self.permission, "authorized-source", self.now
            )
            self.assertEqual(result, asset.resolve())

    def test_rejects_missing_media_scope(self) -> None:
        permission = PermissionRecord(
            source_id="authorized-source",
            granted_by="creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=self.now - timedelta(minutes=5),
        )
        with tempfile.TemporaryDirectory() as folder:
            asset = Path(folder) / "recording.mp4"
            asset.write_bytes(b"placeholder")
            with self.assertRaises(PermissionError):
                validate_authorized_media_asset(
                    asset, permission, "authorized-source", self.now
                )

    def test_rejects_expired_permission(self) -> None:
        expired = PermissionRecord(
            source_id="authorized-source",
            granted_by="creator",
            scopes=frozenset({"process_media"}),
            granted_at=self.now - timedelta(minutes=10),
            expires_at=self.now - timedelta(seconds=1),
        )
        with tempfile.TemporaryDirectory() as folder:
            asset = Path(folder) / "recording.mp4"
            asset.write_bytes(b"placeholder")
            with self.assertRaises(PermissionError):
                validate_authorized_media_asset(
                    asset, expired, "authorized-source", self.now
                )

    def test_rejects_wrong_source(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            asset = Path(folder) / "recording.mp4"
            asset.write_bytes(b"placeholder")
            with self.assertRaises(ValueError):
                validate_authorized_media_asset(
                    asset, self.permission, "another-source", self.now
                )

    def test_rejects_missing_or_non_file_asset(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                validate_authorized_media_asset(
                    Path(folder) / "missing.mp4",
                    self.permission,
                    "authorized-source",
                    self.now,
                )
            with self.assertRaises(ValueError):
                validate_authorized_media_asset(
                    Path(folder),
                    self.permission,
                    "authorized-source",
                    self.now,
                )

    def test_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "target.mp4"
            link = Path(folder) / "link.mp4"
            target.write_bytes(b"placeholder")
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are unavailable on this platform")
            with self.assertRaises(ValueError):
                validate_authorized_media_asset(
                    link, self.permission, "authorized-source", self.now
                )


if __name__ == "__main__":
    unittest.main()
