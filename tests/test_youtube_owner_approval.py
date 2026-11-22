"""Mocked security tests for OAuth-bound, durable YouTube owner approvals."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

from backend.app.rights_registry import SourceRightsRegistry
from backend.app.youtube_owner_approval import (
    AuthenticatedChannelOwner,
    require_current_owner_approval,
    sha256_file,
    verify_authenticated_channel_owner,
    write_owner_approval_record,
)

NOW = datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc)
OWNER = AuthenticatedChannelOwner("youtube-channel-456")


class OwnerApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.video = self.root / "clip.mp4"
        self.video.write_bytes(b"test video bytes")
        self.record = self.root / "approval.json"
        self.registry = SourceRightsRegistry(self.root / "rights.sqlite3")
        self.registry.register({
            "source_id": "source-1",
            "source_url": "https://example.invalid/owner-provided-source",
            "grantor": "creator-owner",
            "evidence_ref": "local-evidence:permission-001",
            "allowed_uses": ["edit", "publish"],
            "platforms": ["youtube"],
            "valid_from": (NOW - timedelta(days=1)).isoformat(),
            "expires_at": (NOW + timedelta(days=2)).isoformat(),
        })
        write_owner_approval_record(
            self.record, clip_id="clip-1", source_id="source-1",
            video_path=self.video, owner=OWNER, confirmed=True,
            at=NOW, expires_at=NOW + timedelta(hours=12),
        )

    def tearDown(self):
        self.temp.cleanup()

    def gate(self, **overrides):
        args = {
            "approval_path": self.record,
            "clip_id": "clip-1",
            "source_id": "source-1",
            "video_path": self.video,
            "owner": OWNER,
            "rights_registry": self.registry,
            "at": NOW + timedelta(minutes=1),
        }
        args.update(overrides)
        require_current_owner_approval(**args)

    def test_oauth_channel_is_resolved_from_mocked_youtube_api(self):
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": OWNER.channel_id}]
        }
        self.assertEqual(
            verify_authenticated_channel_owner(
                youtube, expected_channel_id=OWNER.channel_id
            ),
            OWNER,
        )
        youtube.channels.return_value.list.assert_called_once_with(part="id", mine=True)

    def test_missing_or_mismatched_channel_fails_closed(self):
        with self.assertRaisesRegex(PermissionError, "configured destination"):
            verify_authenticated_channel_owner(Mock(), expected_channel_id="")
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "another-channel"}]
        }
        with self.assertRaisesRegex(PermissionError, "does not resolve"):
            verify_authenticated_channel_owner(
                youtube, expected_channel_id=OWNER.channel_id
            )

    def test_channel_lookup_error_fails_closed(self):
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.side_effect = RuntimeError("offline")
        with self.assertRaisesRegex(PermissionError, "could not verify"):
            verify_authenticated_channel_owner(
                youtube, expected_channel_id=OWNER.channel_id
            )

    def test_pending_or_rejected_decision_cannot_pass_upload_gate(self):
        original = json.loads(self.record.read_text(encoding="utf-8"))
        for decision in ("pending", "rejected", "needs_review"):
            altered = dict(original, decision=decision)
            self.record.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaisesRegex(PermissionError, "does not match"):
                self.gate()
        self.record.write_text(json.dumps(original), encoding="utf-8")

    def test_missing_source_rights_cannot_pass_upload_gate(self):
        empty_registry = SourceRightsRegistry(self.root / "empty-rights.sqlite3")
        with self.assertRaisesRegex(PermissionError, "no recorded rights"):
            self.gate(rights_registry=empty_registry)
    def test_matching_owner_clip_source_hash_and_publish_permission_pass(self):
        self.gate()

    def test_cannot_create_record_without_explicit_confirmation(self):
        with self.assertRaisesRegex(PermissionError, "explicit channel-owner confirmation"):
            write_owner_approval_record(
                self.record, clip_id="clip-1", source_id="source-1",
                video_path=self.video, owner=OWNER, confirmed=False, at=NOW,
            )

    def test_existing_approval_record_cannot_be_overwritten(self):
        with self.assertRaises(FileExistsError):
            write_owner_approval_record(
                self.record, clip_id="clip-2", source_id="source-1",
                video_path=self.video, owner=OWNER, confirmed=True, at=NOW,
            )

    def test_approval_is_bound_to_exact_video_hash(self):
        self.video.write_bytes(b"substituted video")
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate()

    def test_different_authenticated_channel_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(owner=AuthenticatedChannelOwner("another-channel"))

    def test_clip_and_source_mismatch_are_rejected(self):
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(clip_id="other-clip")
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(source_id="other-source")

    def test_expired_approval_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "expired"):
            self.gate(at=NOW + timedelta(days=1))

    def test_future_review_timestamp_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "invalid review time"):
            self.gate(at=NOW - timedelta(minutes=1))

    def test_missing_or_malformed_record_fails_closed(self):
        with self.assertRaisesRegex(PermissionError, "missing or unreadable"):
            self.gate(approval_path=self.root / "missing.json")
        self.record.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(PermissionError, "unsupported schema"):
            self.gate()

    def test_expired_rights_fail_closed(self):
        expired_registry = SourceRightsRegistry(self.root / "expired.sqlite3")
        expired_registry.register({
            "source_id": "source-1",
            "source_url": "https://example.invalid/owner-provided-source",
            "grantor": "creator-owner",
            "evidence_ref": "local-evidence:permission-002",
            "allowed_uses": ["publish"],
            "platforms": ["youtube"],
            "valid_from": (NOW - timedelta(days=2)).isoformat(),
            "expires_at": (NOW - timedelta(seconds=1)).isoformat(),
        })
        with self.assertRaises(PermissionError):
            self.gate(rights_registry=expired_registry)

    def test_revoked_rights_fail_closed(self):
        self.registry.revoke("source-1", actor="owner", at=NOW)
        with self.assertRaises(PermissionError):
            self.gate()

    def test_wrong_scope_or_platform_fails_closed(self):
        for uses, platforms in ((["edit"], ["youtube"]), (["publish"], ["tiktok"])):
            registry = SourceRightsRegistry(
                self.root / f"rights-{uses[0]}-{platforms[0]}.sqlite3"
            )
            registry.register({
                "source_id": "source-1",
                "source_url": "https://example.invalid/owner-provided-source",
                "grantor": "creator-owner",
                "evidence_ref": "local-evidence:permission-003",
                "allowed_uses": uses,
                "platforms": platforms,
                "valid_from": (NOW - timedelta(days=1)).isoformat(),
            })
            with self.assertRaises(PermissionError):
                self.gate(rights_registry=registry)

    def test_record_contains_durable_identity_and_timezone_fields(self):
        data = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertEqual(data["reviewer_channel_id"], OWNER.channel_id)
        self.assertEqual(data["destination_channel_id"], OWNER.channel_id)
        self.assertEqual(data["source_sha256"], sha256_file(self.video))
        self.assertEqual(data["decision"], "approved")
        self.assertTrue(data["reviewed_at"].endswith("+00:00"))
        self.assertTrue(data["expires_at"].endswith("+00:00"))


if __name__ == "__main__":
    unittest.main()
