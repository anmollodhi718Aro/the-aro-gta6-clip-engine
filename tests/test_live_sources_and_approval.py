"""Tests for creator-authorized live source discovery and upload approval."""
import unittest
from datetime import datetime, timezone

from backend.app.approval import ApprovalStatus, UploadApproval, require_upload_approval
from backend.app.live_sources import LiveStream, resolve_authorized_stream
from backend.app.models import PermissionRecord


NOW = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)


def grant(*scopes):
    return PermissionRecord(
        source_id="creator-123",
        granted_by="creator-oauth-consent",
        scopes=frozenset(scopes),
        granted_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
    )


class FakeAuthorizedAdapter:
    def find_live_stream(self, creator_id):
        return LiveStream(
            source_id="creator-123", creator_id=creator_id, stream_id="live-1",
            title="Authorized test stream", started_at=NOW,
            media_reference="provider-approved://live-1",
        )

    def get_media_reference(self, stream):
        return stream.media_reference


class LiveSourceTests(unittest.TestCase):
    def test_discovers_stream_with_active_creator_grant(self):
        stream = resolve_authorized_stream(
            FakeAuthorizedAdapter(), "creator-123", grant("read_live_stream"), at=NOW
        )
        self.assertEqual(stream.stream_id, "live-1")
        self.assertEqual(stream.media_reference, "provider-approved://live-1")

    def test_rejects_missing_read_scope(self):
        with self.assertRaises(PermissionError):
            resolve_authorized_stream(
                FakeAuthorizedAdapter(), "creator-123", grant("publish"), at=NOW
            )


class UploadApprovalTests(unittest.TestCase):
    def test_upload_requires_explicit_owner_approval_and_publish_scope(self):
        pending = UploadApproval("clip-1", "creator-123")
        with self.assertRaises(PermissionError):
            require_upload_approval(pending, grant("publish"), at=NOW)
        approved = pending.decide(True, "channel-owner", at=NOW)
        require_upload_approval(approved, grant("publish"), at=NOW)
        self.assertEqual(approved.status, ApprovalStatus.APPROVED)

    def test_rejected_clip_cannot_be_uploaded(self):
        rejected = UploadApproval("clip-1", "creator-123").decide(False, "channel-owner", at=NOW)
        with self.assertRaises(PermissionError):
            require_upload_approval(rejected, grant("publish"), at=NOW)

    def test_read_permission_alone_does_not_authorize_publishing(self):
        approved = UploadApproval("clip-1", "creator-123").decide(True, "channel-owner", at=NOW)
        with self.assertRaises(PermissionError):
            require_upload_approval(approved, grant("read_live_stream"), at=NOW)


if __name__ == "__main__":
    unittest.main()
