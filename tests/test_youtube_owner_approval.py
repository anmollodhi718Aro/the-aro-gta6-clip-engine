"""Mocked security tests for OAuth-bound, durable YouTube owner approvals."""
import json
import tempfile
import unittest
import sys
import types
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.youtube_owner_approval import (
    AuthenticatedChannelOwner,
    require_active_publish_permission,
    require_current_owner_approval,
    sha256_file,
    write_owner_approval_record,
    verify_authenticated_channel_owner,
)

NOW = datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc)
OWNER = AuthenticatedChannelOwner("google-subject-123", "youtube-channel-456")


class OwnerApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.video = self.root / "clip.mp4"
        self.video.write_bytes(b"test video bytes")
        self.record = self.root / "approval.json"
        self.permission = {
            "source_id": "source-1",
            "status": "active",
            "revoked": False,
            "scopes": ["read", "publish"],
            "expires_at": (NOW + timedelta(days=2)).isoformat(),
        }
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
            "permission_evidence": self.permission,
            "at": NOW + timedelta(minutes=1),
        }
        args.update(overrides)
        require_current_owner_approval(**args)

    def test_oauth_identity_and_channel_are_verified_with_mocked_google_clients(self):
        google = types.ModuleType("google")
        auth = types.ModuleType("google.auth")
        transport = types.ModuleType("google.auth.transport")
        requests = types.ModuleType("google.auth.transport.requests")
        oauth2 = types.ModuleType("google.oauth2")
        id_token = types.ModuleType("google.oauth2.id_token")
        requests.Request = Mock
        id_token.verify_oauth2_token = Mock(return_value={"sub": OWNER.google_subject, "iss": "https://accounts.google.com"})
        google.auth = auth
        auth.transport = transport
        transport.requests = requests
        google.oauth2 = oauth2
        oauth2.id_token = id_token
        credentials = types.SimpleNamespace(id_token="mock-signed-id-token")
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {"items": [{"id": OWNER.channel_id}]}
        modules = {"google": google, "google.auth": auth, "google.auth.transport": transport, "google.auth.transport.requests": requests, "google.oauth2": oauth2, "google.oauth2.id_token": id_token}
        with patch.dict(sys.modules, modules):
            identity = verify_authenticated_channel_owner(credentials, youtube, oauth_client_id="client-id", expected_google_subject=OWNER.google_subject, expected_channel_id=OWNER.channel_id)
        self.assertEqual(identity, OWNER)
        id_token.verify_oauth2_token.assert_called_once()
        youtube.channels.return_value.list.assert_called_once_with(part="id", mine=True)

    def test_wrong_google_subject_fails_before_channel_lookup(self):
        google = types.ModuleType("google")
        auth = types.ModuleType("google.auth")
        transport = types.ModuleType("google.auth.transport")
        requests = types.ModuleType("google.auth.transport.requests")
        oauth2 = types.ModuleType("google.oauth2")
        id_token = types.ModuleType("google.oauth2.id_token")
        requests.Request = Mock
        id_token.verify_oauth2_token = Mock(return_value={"sub": "attacker", "iss": "accounts.google.com"})
        google.auth, auth.transport, transport.requests = auth, transport, requests
        google.oauth2, oauth2.id_token = oauth2, id_token
        credentials = types.SimpleNamespace(id_token="mock-signed-id-token")
        youtube = Mock()
        modules = {"google": google, "google.auth": auth, "google.auth.transport": transport, "google.auth.transport.requests": requests, "google.oauth2": oauth2, "google.oauth2.id_token": id_token}
        with patch.dict(sys.modules, modules):
            with self.assertRaisesRegex(PermissionError, "not the configured channel owner"):
                verify_authenticated_channel_owner(credentials, youtube, oauth_client_id="client-id", expected_google_subject=OWNER.google_subject, expected_channel_id=OWNER.channel_id)
        youtube.channels.assert_not_called()

    def test_missing_oidc_identity_token_fails_closed(self):
        with self.assertRaisesRegex(PermissionError, "no OpenID Connect"):
            verify_authenticated_channel_owner(types.SimpleNamespace(id_token=None), Mock(), oauth_client_id="client-id", expected_google_subject=OWNER.google_subject, expected_channel_id=OWNER.channel_id)

    def test_matching_authenticated_owner_clip_source_and_hash_pass(self):
        self.gate()

    def test_cannot_create_record_without_explicit_confirmation(self):
        with self.assertRaisesRegex(PermissionError, "explicit channel-owner confirmation"):
            write_owner_approval_record(
                self.record, clip_id="clip-1", source_id="source-1",
                video_path=self.video, owner=OWNER, confirmed=False, at=NOW,
            )

    def test_approval_is_bound_to_exact_video_hash(self):
        self.video.write_bytes(b"substituted video")
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate()

    def test_different_authenticated_google_subject_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(owner=AuthenticatedChannelOwner("other-subject", OWNER.channel_id))

    def test_different_destination_channel_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(owner=AuthenticatedChannelOwner(OWNER.google_subject, "other-channel"))

    def test_clip_and_source_mismatch_are_rejected(self):
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(clip_id="other-clip")
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(source_id="other-source")

    def test_expired_approval_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "expired"):
            self.gate(at=NOW + timedelta(days=1))

    def test_missing_or_malformed_record_fails_closed(self):
        with self.assertRaisesRegex(PermissionError, "missing or unreadable"):
            self.gate(approval_path=self.root / "missing.json")
        self.record.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(PermissionError, "unsupported schema"):
            self.gate()

    def test_publish_permission_must_be_current_active_and_source_bound(self):
        require_active_publish_permission(self.permission, "source-1", at=NOW)
        for bad in (
            {**self.permission, "status": "revoked", "revoked": True},
            {**self.permission, "revoked": True},
            {**self.permission, "scopes": ["read"]},
            {**self.permission, "source_id": "other-source"},
            {**self.permission, "expires_at": (NOW - timedelta(seconds=1)).isoformat()},
        ):
            with self.assertRaises(PermissionError):
                require_active_publish_permission(bad, "source-1", at=NOW)

    def test_upload_gate_rechecks_revoked_and_expired_permission(self):
        for bad in (
            {**self.permission, "revoked": True},
            {**self.permission, "status": "revoked"},
            {**self.permission, "scopes": ["read"]},
            {**self.permission, "expires_at": (NOW - timedelta(seconds=1)).isoformat()},
        ):
            with self.assertRaises(PermissionError):
                self.gate(permission_evidence=bad)

    def test_missing_permission_evidence_fails_closed(self):
        with self.assertRaisesRegex(PermissionError, "evidence is required"):
            self.gate(permission_evidence=None)

    def test_approval_record_is_private_and_has_durable_identity_fields(self):
        data = json.loads(self.record.read_text(encoding="utf-8"))
        self.assertEqual(data["reviewer_google_subject"], OWNER.google_subject)
        self.assertEqual(data["destination_channel_id"], OWNER.channel_id)
        self.assertEqual(data["source_sha256"], sha256_file(self.video))
        self.assertEqual(data["decision"], "approved")
        self.assertTrue(data["reviewed_at"].endswith("+00:00"))
        self.assertTrue(data["expires_at"].endswith("+00:00"))


if __name__ == "__main__":
    unittest.main()
