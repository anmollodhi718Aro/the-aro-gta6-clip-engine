"""Tests for source-specific rights registration and export authorization."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.rights_registry import SourceRightsRegistry


class SourceRightsRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.registry = SourceRightsRegistry(Path(self.temp.name) / "rights.sqlite3")
        self.now = datetime(2026, 11, 19, 8, tzinfo=timezone.utc)
        self.record = {
            "source_id": "creator-video-1",
            "source_url": "https://example.com/video",
            "grantor": "creator",
            "evidence_ref": "permission-email-2026-11-19",
            "allowed_uses": ["analyze", "edit", "publish"],
            "platforms": ["youtube"],
            "attribution": "Credit Creator",
            "disclosure": "Authorized collaboration",
            "valid_from": self.now - timedelta(hours=1),
            "expires_at": self.now + timedelta(hours=1),
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_authorizes_only_recorded_scope_and_platform(self):
        self.registry.register(self.record)
        result = self.registry.authorize("creator-video-1", "publish", "youtube", at=self.now)
        self.assertEqual(result["attribution"], "Credit Creator")
        with self.assertRaises(PermissionError):
            self.registry.authorize("creator-video-1", "publish", "tiktok", at=self.now)
        with self.assertRaises(PermissionError):
            self.registry.authorize("creator-video-1", "edit", "instagram", at=self.now)

    def test_unknown_expired_and_future_rights_fail_closed(self):
        with self.assertRaises(PermissionError):
            self.registry.authorize("unknown", "edit", "youtube", at=self.now)
        self.registry.register(self.record)
        with self.assertRaises(PermissionError):
            self.registry.authorize("creator-video-1", "publish", "youtube",
                                    at=self.now + timedelta(hours=2))

    def test_revocation_blocks_and_is_audited(self):
        self.registry.register(self.record)
        self.assertTrue(self.registry.revoke("creator-video-1", actor="owner", at=self.now))
        self.assertFalse(self.registry.revoke("creator-video-1", actor="owner", at=self.now))
        with self.assertRaises(PermissionError):
            self.registry.authorize("creator-video-1", "publish", "youtube",
                                    at=self.now + timedelta(minutes=1))
        self.assertEqual([e["action"] for e in self.registry.audit_events("creator-video-1")],
                         ["registered", "revoked"])

    def test_register_rejects_duplicate_source_id_without_overwriting_grant(self):
        # Start with a deliberately narrow grant, then try to broaden it using
        # the same source ID. The duplicate must not replace the original row.
        initial = dict(self.record, allowed_uses=["analyze"])
        self.registry.register(initial)
        replacement = dict(
            initial,
            source_url="https://example.com/replacement",
            evidence_ref="replacement-permission",
            allowed_uses=["publish"],
        )
        with self.assertRaisesRegex(PermissionError, "rights already exist"):
            self.registry.register(replacement)

        # The original narrower grant remains unchanged.
        with self.assertRaises(PermissionError):
            self.registry.authorize("creator-video-1", "publish", "youtube", at=self.now)
        self.registry.authorize("creator-video-1", "analyze", "youtube", at=self.now)
        self.assertEqual(
            [event["action"] for event in self.registry.audit_events("creator-video-1")],
            ["registered"],
        )

    def test_register_cannot_reactivate_revoked_source_id(self):
        self.registry.register(self.record)
        self.assertTrue(self.registry.revoke("creator-video-1", actor="owner", at=self.now))

        replacement = dict(
            self.record,
            evidence_ref="new-permission-after-revocation",
            valid_from=self.now + timedelta(days=1),
        )
        with self.assertRaisesRegex(PermissionError, "rights already exist"):
            self.registry.register(replacement)

        with self.assertRaisesRegex(PermissionError, "rights revoked"):
            self.registry.authorize(
                "creator-video-1", "publish", "youtube",
                at=self.now + timedelta(minutes=1),
            )
        self.assertEqual(
            [event["action"] for event in self.registry.audit_events("creator-video-1")],
            ["registered", "revoked"],
        )

    def test_rejects_missing_evidence_and_unknown_scope(self):
        invalid = dict(self.record, evidence_ref="")
        with self.assertRaises(ValueError):
            self.registry.register(invalid)
        invalid = dict(self.record, allowed_uses=["download_anything"])
        with self.assertRaises(ValueError):
            self.registry.register(invalid)

    def test_rejects_naive_timestamps(self):
        invalid = dict(self.record, valid_from="2026-11-19T08:00:00")
        with self.assertRaises(ValueError):
            self.registry.register(invalid)


if __name__ == "__main__":
    unittest.main()
