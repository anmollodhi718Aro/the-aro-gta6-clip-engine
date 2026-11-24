"""Tests for source-specific rights registration and export authorization."""
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier
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

    def test_rejects_scalar_or_malformed_scope_collections(self):
        for invalid_uses in ("publish", ["publish", 7], [" "], []):
            with self.subTest(allowed_uses=invalid_uses):
                with self.assertRaises(ValueError):
                    self.registry.register(dict(self.record, allowed_uses=invalid_uses))
        for invalid_platforms in ("youtube", ["youtube", None], [" "], []):
            with self.subTest(platforms=invalid_platforms):
                with self.assertRaises(ValueError):
                    self.registry.register(dict(self.record, platforms=invalid_platforms))

    def test_rejects_non_string_actor_without_attribute_error(self):
        with self.assertRaisesRegex(ValueError, "actor is required"):
            self.registry.register(self.record, actor=None)

    def test_rejects_non_object_rights_record(self):
        for invalid in (None, [], "record", 7):
            with self.subTest(record=invalid):
                with self.assertRaisesRegex(ValueError, "rights record must be an object"):
                    self.registry.register(invalid)

    def test_authorize_rejects_missing_or_non_string_identifiers(self):
        invalid_calls = (
            (None, "publish", "youtube"),
            ("creator-video-1", None, "youtube"),
            ("creator-video-1", "publish", None),
            (" ", "publish", "youtube"),
            ("creator-video-1", 7, "youtube"),
        )
        for source_id, use, platform in invalid_calls:
            with self.subTest(source_id=source_id, use=use, platform=platform):
                with self.assertRaisesRegex(ValueError, "non-empty strings"):
                    self.registry.authorize(source_id, use, platform, at=self.now)

    def test_revoke_and_audit_reject_invalid_source_or_actor(self):
        for source_id, actor in ((None, "owner"), ("creator-video-1", None),
                                 (" ", "owner"), ("creator-video-1", 7)):
            with self.subTest(source_id=source_id, actor=actor):
                with self.assertRaisesRegex(ValueError, "non-empty strings"):
                    self.registry.revoke(source_id, actor=actor, at=self.now)
        for source_id in (None, "", 7):
            with self.subTest(audit_source_id=source_id):
                with self.assertRaisesRegex(ValueError, "non-empty string"):
                    self.registry.audit_events(source_id)

    def test_concurrent_duplicate_registration_creates_exactly_one_grant(self):
        barrier = Barrier(2)

        def attempt_registration(actor):
            barrier.wait(timeout=5)
            try:
                self.registry.register(dict(self.record), actor=actor)
                return "registered"
            except PermissionError:
                return "duplicate"

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(attempt_registration, ("worker-a", "worker-b")))

        self.assertCountEqual(outcomes, ["registered", "duplicate"])
        events = self.registry.audit_events("creator-video-1")
        self.assertEqual([event["action"] for event in events], ["registered"])
        self.assertIn(events[0]["actor"], ("worker-a", "worker-b"))

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
        # sqlite3.Connection's context manager commits/rolls back but does not
        # close the handle. Close explicitly so Windows can remove the temp DB
        # in tearDown after this trigger-backed regression.
        with closing(sqlite3.connect(self.registry.database_path)) as db:
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



    def test_register_rejects_malformed_source_urls(self):
        invalid_urls = (
            "https://",
            "http://",
            "https:///video",
            "ftp://example.com/video",
            "https://example.com:bad/video",
            "https://example.com:/video",
            "https://[::1]:/video",
            "https://example.com:70000/video",
            "https://example..com/video",
            "https://-example.com/video",
            "https://example-.com/video",
            "https://exa_mple.com/video",
            "https://%65xample.com/video",
            "https://user:password@example.com/video",
            "https://exa mple.com/video",
            "https://exa\nmple.com/video",
            "https://exa\tmple.com/video",
            "https://example.com\\\\@evil.example/video",
        )
        for source_url in invalid_urls:
            with self.subTest(source_url=source_url):
                with self.assertRaises(ValueError):
                    self.registry.register(dict(self.record, source_url=source_url))

    def test_register_accepts_http_and_https_source_urls(self):
        for index, source_url in enumerate((
            "http://example.com/video",
            "https://example.com/video",
            "https://[::1]/video",
            "https://bücher.example/video",
            "https://example.com./video",
        )):
            with self.subTest(source_url=source_url):
                record = dict(self.record, source_id=f"url-source-{index}", source_url=source_url)
                self.registry.register(record)
                self.assertEqual(
                    self.registry.authorize(
                        record["source_id"], "publish", "youtube", at=self.now
                    )["source_url"],
                    source_url,
                )
    def test_register_rejects_ambiguous_noncanonical_ipv4_hosts(self):
        invalid_hosts = (
            "999.999.999.999",
            "127.1",
            "0177.0.0.1",
            "0x7f.0.0.1",
            "2130706433",
            "example.123",
            "example.0x2",
            "example.012",
        )
        for host in invalid_hosts:
            with self.subTest(host=host):
                with self.assertRaisesRegex(ValueError, "valid http\\(s\\) URL"):
                    self.registry.register(
                        dict(self.record, source_url=f"https://{host}/video")
                    )

    def test_register_accepts_canonical_ipv4_host(self):
        source_url = "https://192.0.2.10/video"
        record = dict(self.record, source_id="url-source-ipv4", source_url=source_url)
        self.registry.register(record)
        self.assertEqual(
            self.registry.authorize(
                record["source_id"], "publish", "youtube", at=self.now
            )["source_url"],
            source_url,
        )

    def test_register_rejects_non_string_rights_metadata(self):
        for field in ("source_id", "source_url", "grantor", "evidence_ref"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    self.registry.register(dict(self.record, **{field: 7}))
        for field in ("attribution", "disclosure"):
            for invalid in (None, 7, []):
                with self.subTest(field=field, value=invalid):
                    with self.assertRaises(ValueError):
                        self.registry.register(dict(self.record, **{field: invalid}))

    def test_register_rejects_non_datetime_timestamp_values(self):
        for field in ("valid_from", "expires_at"):
            for invalid in (7, [], object()):
                with self.subTest(field=field, value_type=type(invalid).__name__):
                    with self.assertRaises(ValueError):
                        self.registry.register(dict(self.record, **{field: invalid}))

    def test_authorize_and_revoke_reject_invalid_explicit_timestamps(self):
        self.registry.register(self.record)
        with self.assertRaises(ValueError):
            self.registry.authorize("creator-video-1", "publish", "youtube", at=0)
        with self.assertRaises(ValueError):
            self.registry.revoke("creator-video-1", actor="owner", at=0)


    def test_register_rejects_blank_required_text_fields(self):
        for field in ("source_id", "source_url", "grantor", "evidence_ref"):
            for invalid in ("", "   "):
                with self.subTest(field=field, value=repr(invalid)):
                    with self.assertRaises(ValueError):
                        self.registry.register(dict(self.record, **{field: invalid}))

    def test_register_rejects_falsey_explicit_timestamps(self):
        for field in ("valid_from", "expires_at"):
            for invalid in ("", False, 0):
                with self.subTest(field=field, value=repr(invalid)):
                    with self.assertRaises(ValueError):
                        self.registry.register(dict(self.record, **{field: invalid}))

    def test_authorize_and_revoke_reject_all_falsey_explicit_timestamps(self):
        self.registry.register(self.record)
        for invalid in ("", False, 0):
            with self.subTest(operation="authorize", value=repr(invalid)):
                with self.assertRaises(ValueError):
                    self.registry.authorize(
                        "creator-video-1", "publish", "youtube", at=invalid
                    )
            with self.subTest(operation="revoke", value=repr(invalid)):
                with self.assertRaises(ValueError):
                    self.registry.revoke("creator-video-1", actor="owner", at=invalid)

if __name__ == "__main__":
    unittest.main()
