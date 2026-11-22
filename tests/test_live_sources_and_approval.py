"""Tests for creator permission checks and immutable owner upload approval."""
import unittest
from datetime import datetime, timezone

from backend.app.approval import ApprovalStatus, UploadApproval, require_upload_approval
from backend.app.live_sources import LiveStream, resolve_authorized_stream
from backend.app.models import PermissionRecord


NOW = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)


def grant(source_id="creator-123", *scopes, expires_at=None, revoked_at=None):
    return PermissionRecord(
        source_id=source_id,
        granted_by="creator-oauth-consent",
        scopes=frozenset(scopes),
        granted_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        expires_at=expires_at,
        revoked_at=revoked_at,
    )


class FakeAuthorizedAdapter:
    def __init__(self, creator_id="creator-123", source_id="creator-123"):
        self.creator_id = creator_id
        self.source_id = source_id
        self.calls = 0

    def find_live_stream(self, creator_id):
        self.calls += 1
        return LiveStream(
            source_id=self.source_id,
            creator_id=self.creator_id,
            stream_id="live-1",
            title="Authorized test stream",
            started_at=NOW,
            media_reference="provider-approved://live-1",
        )

    def get_media_reference(self, stream):
        return stream.media_reference


class LiveSourceTests(unittest.TestCase):
    def test_discovers_stream_with_matching_active_creator_grant(self):
        stream = resolve_authorized_stream(
            FakeAuthorizedAdapter(), "creator-123", grant("creator-123", "read_live_stream"), at=NOW
        )
        self.assertEqual(stream.stream_id, "live-1")
        self.assertEqual(stream.media_reference, "provider-approved://live-1")

    def test_rejects_missing_read_scope_before_provider_call(self):
        adapter = FakeAuthorizedAdapter()
        with self.assertRaises(PermissionError):
            resolve_authorized_stream(adapter, "creator-123", grant("creator-123", "publish"), at=NOW)
        self.assertEqual(adapter.calls, 0)

    def test_rejects_grant_for_different_creator_before_provider_call(self):
        adapter = FakeAuthorizedAdapter()
        with self.assertRaises(PermissionError):
            resolve_authorized_stream(adapter, "creator-456", grant("creator-123", "read_live_stream"), at=NOW)
        self.assertEqual(adapter.calls, 0)

    def test_rejects_provider_response_for_different_creator(self):
        adapter = FakeAuthorizedAdapter(creator_id="creator-456")
        with self.assertRaises(PermissionError):
            resolve_authorized_stream(adapter, "creator-123", grant("creator-123", "read_live_stream"), at=NOW)

    def test_rejects_expired_or_revoked_creator_grants(self):
        expired = grant("creator-123", "read_live_stream", expires_at=NOW)
        revoked = grant("creator-123", "read_live_stream", revoked_at=NOW)
        for permission in (expired, revoked):
            with self.subTest(permission=permission):
                adapter = FakeAuthorizedAdapter()
                with self.assertRaises(PermissionError):
                    resolve_authorized_stream(adapter, "creator-123", permission, at=NOW)
                self.assertEqual(adapter.calls, 0)


class UploadApprovalTests(unittest.TestCase):
    def test_upload_requires_explicit_owner_approval_and_publish_scope(self):
        pending = UploadApproval("clip-1", "creator-123")
        with self.assertRaises(PermissionError):
            require_upload_approval(pending, grant("creator-123", "publish"), owner_identity="channel-owner", at=NOW)
        approved = pending.decide(True, "channel-owner", at=NOW)
        require_upload_approval(approved, grant("creator-123", "publish"), owner_identity="channel-owner", at=NOW)
        self.assertEqual(approved.status, ApprovalStatus.APPROVED)
        self.assertEqual(approved.reviewed_by, "channel-owner")

    def test_rejected_clip_cannot_be_uploaded(self):
        rejected = UploadApproval("clip-1", "creator-123").decide(False, "channel-owner", at=NOW)
        with self.assertRaises(PermissionError):
            require_upload_approval(rejected, grant("creator-123", "publish"), owner_identity="channel-owner", at=NOW)

    def test_non_owner_identity_cannot_approve_upload(self):
        approved = UploadApproval("clip-1", "creator-123").decide(True, "different-channel", at=NOW)
        with self.assertRaisesRegex(PermissionError, "authenticated channel owner"):
            require_upload_approval(
                approved, grant("creator-123", "publish"),
                owner_identity="channel-owner", at=NOW,
            )

    def test_missing_trusted_owner_identity_fails_closed(self):
        approved = UploadApproval("clip-1", "creator-123").decide(True, "channel-owner", at=NOW)
        with self.assertRaisesRegex(ValueError, "trusted channel owner"):
            require_upload_approval(
                approved, grant("creator-123", "publish"), owner_identity=" ", at=NOW,
            )

    def test_read_permission_alone_does_not_authorize_publishing(self):
        approved = UploadApproval("clip-1", "creator-123").decide(True, "channel-owner", at=NOW)
        with self.assertRaises(PermissionError):
            require_upload_approval(approved, grant("creator-123", "read_live_stream"), owner_identity="channel-owner", at=NOW)

    def test_final_decision_cannot_be_changed(self):
        approved = UploadApproval("clip-1", "creator-123").decide(True, "owner", at=NOW)
        with self.assertRaises(ValueError):
            approved.decide(False, "owner", at=NOW)

    def test_decision_requires_boolean_and_reviewer(self):
        pending = UploadApproval("clip-1", "creator-123")
        with self.assertRaises(ValueError):
            pending.decide("yes", "owner", at=NOW)
        with self.assertRaises(ValueError):
            pending.decide(True, "  ", at=NOW)


if __name__ == "__main__":
    unittest.main()
