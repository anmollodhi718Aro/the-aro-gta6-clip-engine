"""Tests for source-specific rights registration and export authorization."""
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier

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

    def test_concurrent_revoke_records_exactly_one_revocation(self):
        self.registry.register(self.record)
        barrier = Barrier(2)

        def attempt_revoke(actor):
            barrier.wait(timeout=5)
            return self.registry.revoke("creator-video-1", actor=actor, at=self.now)

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(attempt_revoke, ("worker-a", "worker-b")))

        self.assertCountEqual(outcomes, [True, False])
        events = self.registry.audit_events("creator-video-1")
        self.assertEqual([event["action"] for event in events],
                         ["registered", "revoked"])
        self.assertIn(events[1]["actor"], ("worker-a", "worker-b"))

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

    def test_duplicate_source_id_cannot_broaden_active_grant(self):
        original = dict(self.record, allowed_uses=["analyze"])
        self.registry.register(original)
        broadened = dict(
            self.record,
            source_url="https://attacker.example/replacement",
            grantor="different-grantor",
            evidence_ref="replacement-evidence",
            allowed_uses=["analyze", "publish"],
            platforms=["youtube", "tiktok"],
            attribution="replacement attribution",
            disclosure="replacement disclosure",
        )
        with self.assertRaisesRegex(PermissionError, "rights already exist"):
            self.registry.register(broadened)
        original_grant = self.registry.authorize(
            "creator-video-1", "analyze", "youtube", at=self.now
        )
        self.assertEqual(original_grant["source_url"], self.record["source_url"])
        self.assertEqual(original_grant["grantor"], self.record["grantor"])
        self.assertEqual(original_grant["evidence_ref"], self.record["evidence_ref"])
        self.assertEqual(original_grant["attribution"], self.record["attribution"])
        self.assertEqual(original_grant["disclosure"], self.record["disclosure"])
        with self.assertRaises(PermissionError):
            self.registry.authorize("creator-video-1", "publish", "youtube", at=self.now)
        # The duplicate attempt must not broaden the platform allowlist either.
        with self.assertRaises(PermissionError):
            self.registry.authorize("creator-video-1", "analyze", "tiktok", at=self.now)
        with self.assertRaises(PermissionError):
            self.registry.authorize("creator-video-1", "edit", "youtube", at=self.now)
        self.assertEqual([e["action"] for e in self.registry.audit_events("creator-video-1")],
                         ["registered"])

    def test_duplicate_source_id_cannot_reactivate_revoked_grant(self):
        self.registry.register(self.record)
        self.registry.revoke("creator-video-1", actor="owner", at=self.now)
        with self.assertRaisesRegex(PermissionError, "rights already exist"):
            self.registry.register(self.record)
        with self.assertRaises(PermissionError):
            self.registry.authorize("creator-video-1", "publish", "youtube",
                                    at=self.now + timedelta(minutes=1))
        self.assertEqual([e["action"] for e in self.registry.audit_events("creator-video-1")],
                         ["registered", "revoked"])

    def test_non_duplicate_integrity_error_is_not_misreported_as_duplicate(self):
        with sqlite3.connect(self.registry.database_path) as db:
            db.execute("""
                CREATE TRIGGER reject_source_registration
                BEFORE INSERT ON source_rights
                BEGIN
                    SELECT RAISE(ABORT, 'synthetic integrity failure');
                END
            """)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "synthetic integrity failure"):
            self.registry.register(self.record)
        self.assertEqual(self.registry.audit_events("creator-video-1"), [])


if __name__ == "__main__":
    unittest.main()
