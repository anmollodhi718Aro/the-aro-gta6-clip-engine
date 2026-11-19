"""Tests for durable creator consent and revocation."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.consent_registry import ConsentRegistry
from backend.app.models import PermissionRecord


class ConsentRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "state" / "consent.sqlite3"
        self.now = datetime(2026, 11, 18, 12, tzinfo=timezone.utc)
        self.permission = PermissionRecord(
            source_id="video-123", granted_by="creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=self.now - timedelta(minutes=1),
            expires_at=self.now + timedelta(hours=1),
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_grant_survives_registry_restart(self):
        ConsentRegistry(self.db).grant(self.permission, actor="owner")
        restarted = ConsentRegistry(self.db)
        self.assertEqual(restarted.get("video-123"), self.permission)

    def test_require_checks_scope_and_expiry(self):
        registry = ConsentRegistry(self.db)
        registry.grant(self.permission)
        self.assertEqual(
            registry.require("video-123", "analyze_chat", at=self.now),
            self.permission,
        )
        with self.assertRaises(PermissionError):
            registry.require("video-123", "publish", at=self.now)
        with self.assertRaises(PermissionError):
            registry.require("video-123", "analyze_chat",
                             at=self.now + timedelta(hours=2))

    def test_revoke_is_immediate_and_idempotent(self):
        registry = ConsentRegistry(self.db)
        registry.grant(self.permission)
        revoked_at = self.now + timedelta(minutes=1)
        self.assertTrue(registry.revoke("video-123", actor="owner", at=revoked_at))
        self.assertFalse(registry.revoke("video-123", actor="owner", at=revoked_at))
        with self.assertRaises(PermissionError):
            registry.require("video-123", "analyze_chat", at=revoked_at)
        self.assertEqual(
            [event["action"] for event in registry.audit_events("video-123")],
            ["granted", "revoked"],
        )

    def test_unknown_source_fails_closed(self):
        registry = ConsentRegistry(self.db)
        self.assertIsNone(registry.get("missing"))
        with self.assertRaises(PermissionError):
            registry.require("missing", "analyze_chat", at=self.now)

    def test_regrant_clears_previous_revocation(self):
        registry = ConsentRegistry(self.db)
        registry.grant(self.permission)
        registry.revoke("video-123", actor="owner", at=self.now)
        renewed = PermissionRecord(
            source_id="video-123", granted_by="creator",
            scopes=frozenset({"analyze_chat"}),
            granted_at=self.now + timedelta(minutes=1),
        )
        registry.grant(renewed, actor="owner")
        self.assertEqual(registry.require(
            "video-123", "analyze_chat", at=self.now + timedelta(minutes=2)
        ), renewed)
        self.assertEqual(
            [event["action"] for event in registry.audit_events("video-123")],
            ["granted", "revoked", "granted"],
        )


if __name__ == "__main__":
    unittest.main()
