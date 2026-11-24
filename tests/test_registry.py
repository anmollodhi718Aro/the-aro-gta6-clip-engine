"""Tests for the in-memory source permission registry."""

import unittest
from datetime import datetime, timedelta, timezone

from backend.app.models import PermissionRecord
from backend.app.registry import SourcePermissionRegistry


class SourcePermissionRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
        self.record = PermissionRecord(
            source_id="synthetic-source",
            granted_by="test-creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=self.now - timedelta(hours=1),
            expires_at=self.now + timedelta(hours=1),
        )
        self.registry = SourcePermissionRegistry()

    def test_register_and_authorize_only_granted_scope(self) -> None:
        self.registry.register(self.record)
        self.assertTrue(self.registry.is_allowed("synthetic-source", "analyze_chat", self.now))
        self.assertFalse(self.registry.is_allowed("synthetic-source", "download_video", self.now))

    def test_unknown_source_is_denied(self) -> None:
        self.assertFalse(self.registry.is_allowed("missing", "analyze_chat", self.now))
        with self.assertRaises(PermissionError):
            self.registry.require("missing", "analyze_chat", self.now)

    def test_duplicate_registration_is_rejected(self) -> None:
        self.registry.register(self.record)
        with self.assertRaises(ValueError):
            self.registry.register(self.record)

    def test_expired_permission_is_denied(self) -> None:
        self.registry.register(self.record)
        self.assertFalse(
            self.registry.is_allowed(
                "synthetic-source", "analyze_chat", self.now + timedelta(hours=1)
            )
        )

    def test_revocation_blocks_access_from_revocation_time(self) -> None:
        self.registry.register(self.record)
        revoked_at = self.now + timedelta(minutes=5)
        revoked = self.registry.revoke("synthetic-source", revoked_at)
        self.assertEqual(revoked.revoked_at, revoked_at)
        self.assertTrue(
            self.registry.is_allowed(
                "synthetic-source", "analyze_chat", revoked_at - timedelta(seconds=1)
            )
        )
        self.assertFalse(
            self.registry.is_allowed("synthetic-source", "analyze_chat", revoked_at)
        )

    def test_revocation_cannot_precede_grant(self) -> None:
        self.registry.register(self.record)
        with self.assertRaises(ValueError):
            self.registry.revoke(
                "synthetic-source", self.record.granted_at - timedelta(seconds=1)
            )


if __name__ == "__main__":
    unittest.main()
