"""Mocked security tests for OAuth-bound, durable YouTube owner approvals."""
import json
import os
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.app.rights_registry import SourceRightsRegistry
from backend.app.youtube_owner_approval import (
    AuthenticatedChannelOwner,
    require_current_owner_approval,
    sha256_file,
    sha256_bytes,
    _verify_google_id_token,
    verify_authenticated_channel_owner,
    write_owner_approval_record,
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
            video_path=self.video, owner=OWNER, privacy="private", confirmed=True,
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
            "privacy": "private",
            "rights_registry": self.registry,
            "at": NOW + timedelta(minutes=1),
        }
        args.update(overrides)
        require_current_owner_approval(**args)

    def _mock_google_modules(self, claims):
        google = types.ModuleType("google")
        auth = types.ModuleType("google.auth")
        transport = types.ModuleType("google.auth.transport")
        requests = types.ModuleType("google.auth.transport.requests")
        oauth2 = types.ModuleType("google.oauth2")
        id_token = types.ModuleType("google.oauth2.id_token")
        requests.Request = Mock(return_value=object())
        id_token.verify_oauth2_token = Mock(return_value=claims)
        google.auth = auth
        auth.transport = transport
        transport.requests = requests
        google.oauth2 = oauth2
        oauth2.id_token = id_token
        return {
            "google": google,
            "google.auth": auth,
            "google.auth.transport": transport,
            "google.auth.transport.requests": requests,
            "google.oauth2": oauth2,
            "google.oauth2.id_token": id_token,
        }, id_token

    def test_id_token_helper_verifies_signature_and_audience(self):
        claims = {
            "sub": OWNER.google_subject,
            "iss": "https://accounts.google.com",
            "azp": "client-id",
        }
        modules, id_token = self._mock_google_modules(claims)
        credentials = SimpleNamespace(id_token="signed-id-token")
        with patch.dict(sys.modules, modules):
            actual = _verify_google_id_token(credentials, "client-id")
        self.assertEqual(actual, claims)
        id_token.verify_oauth2_token.assert_called_once()
        args, kwargs = id_token.verify_oauth2_token.call_args
        self.assertEqual(args[0], "signed-id-token")
        self.assertEqual(kwargs["audience"], "client-id")

    def test_id_token_helper_rejects_missing_token_and_client_id(self):
        with self.assertRaisesRegex(PermissionError, "no OpenID Connect"):
            _verify_google_id_token(SimpleNamespace(id_token=None), "client-id")
        with self.assertRaisesRegex(PermissionError, "OAuth client ID"):
            _verify_google_id_token(SimpleNamespace(id_token="signed-id-token"), "")

    def test_id_token_helper_wraps_signature_verification_failure(self):
        modules, id_token = self._mock_google_modules({})
        id_token.verify_oauth2_token.side_effect = ValueError("bad signature")
        with patch.dict(sys.modules, modules):
            with self.assertRaisesRegex(PermissionError, "could not be verified"):
                _verify_google_id_token(
                    SimpleNamespace(id_token="invalid-token"), "client-id"
                )

    def test_oauth_subject_and_youtube_channel_are_both_verified(self):
        modules, id_token = self._mock_google_modules({
            "sub": OWNER.google_subject,
            "iss": "https://accounts.google.com",
            "azp": "client-id",
        })
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": OWNER.channel_id}]
        }
        credentials = SimpleNamespace(id_token="signed-id-token")
        with patch.dict(sys.modules, modules):
            actual = verify_authenticated_channel_owner(
                credentials, youtube, oauth_client_id="client-id",
                expected_google_subject=OWNER.google_subject,
                expected_channel_id=OWNER.channel_id,
            )
        self.assertEqual(actual, OWNER)
        id_token.verify_oauth2_token.assert_called_once()
        youtube.channels.return_value.list.assert_called_once_with(part="id", mine=True)

    def test_different_google_account_is_rejected_even_for_same_channel(self):
        modules, _ = self._mock_google_modules({
            "sub": "different-google-account",
            "iss": "accounts.google.com",
            "azp": "client-id",
        })
        youtube = Mock()
        credentials = SimpleNamespace(id_token="signed-id-token")
        with patch.dict(sys.modules, modules):
            with self.assertRaisesRegex(PermissionError, "not the configured channel owner"):
                verify_authenticated_channel_owner(
                    credentials, youtube, oauth_client_id="client-id",
                    expected_google_subject=OWNER.google_subject,
                    expected_channel_id=OWNER.channel_id,
                )
        youtube.channels.assert_not_called()

    def test_missing_oidc_identity_token_fails_closed(self):
        with self.assertRaisesRegex(PermissionError, "no OpenID Connect"):
            verify_authenticated_channel_owner(
                SimpleNamespace(id_token=None), Mock(), oauth_client_id="client-id",
                expected_google_subject=OWNER.google_subject,
                expected_channel_id=OWNER.channel_id,
            )

    def test_invalid_issuer_or_authorized_party_fails_closed(self):
        for claims in (
            {"sub": OWNER.google_subject, "iss": "untrusted.example"},
            {"sub": OWNER.google_subject, "iss": "accounts.google.com", "azp": "other-client"},
        ):
            modules, _ = self._mock_google_modules(claims)
            with patch.dict(sys.modules, modules):
                with self.assertRaisesRegex(PermissionError, "valid subject, issuer or authorized party"):
                    verify_authenticated_channel_owner(
                        SimpleNamespace(id_token="signed-id-token"), Mock(),
                        oauth_client_id="client-id",
                        expected_google_subject=OWNER.google_subject,
                        expected_channel_id=OWNER.channel_id,
                    )

    def test_missing_or_mismatched_channel_fails_closed(self):
        with self.assertRaisesRegex(PermissionError, "configured Google owner subject"):
            verify_authenticated_channel_owner(
                SimpleNamespace(id_token="token"), Mock(), oauth_client_id="",
                expected_google_subject=OWNER.google_subject,
                expected_channel_id=OWNER.channel_id,
            )
        modules, _ = self._mock_google_modules({
            "sub": OWNER.google_subject, "iss": "accounts.google.com",
        })
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "another-channel"}]
        }
        with patch.dict(sys.modules, modules):
            with self.assertRaisesRegex(PermissionError, "does not resolve"):
                verify_authenticated_channel_owner(
                    SimpleNamespace(id_token="signed-id-token"), youtube,
                    oauth_client_id="client-id",
                    expected_google_subject=OWNER.google_subject,
                    expected_channel_id=OWNER.channel_id,
                )

    def test_channel_lookup_error_fails_closed(self):
        modules, _ = self._mock_google_modules({
            "sub": OWNER.google_subject, "iss": "accounts.google.com",
        })
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.side_effect = RuntimeError("offline")
        with patch.dict(sys.modules, modules):
            with self.assertRaisesRegex(PermissionError, "could not verify"):
                verify_authenticated_channel_owner(
                    SimpleNamespace(id_token="signed-id-token"), youtube,
                    oauth_client_id="client-id",
                    expected_google_subject=OWNER.google_subject,
                    expected_channel_id=OWNER.channel_id,
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

    def test_approval_gate_accepts_hash_of_immutable_upload_payload(self):
        payload = self.video.read_bytes()
        self.gate(video_path=None, video_sha256=sha256_bytes(payload))

    def test_approval_gate_rejects_mismatched_immutable_upload_payload_hash(self):
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(video_path=None, video_sha256=sha256_bytes(b"tampered payload"))

    def test_cannot_create_record_without_explicit_confirmation(self):
        with self.assertRaisesRegex(PermissionError, "explicit channel-owner confirmation"):
            write_owner_approval_record(
                self.record, clip_id="clip-1", source_id="source-1",
                video_path=self.video, owner=OWNER, privacy="private",
                confirmed=False, at=NOW,
            )

    def test_existing_approval_record_cannot_be_overwritten(self):
        with self.assertRaises(FileExistsError):
            write_owner_approval_record(
                self.record, clip_id="clip-2", source_id="source-1",
                video_path=self.video, owner=OWNER, privacy="private", confirmed=True, at=NOW,
            )

    def test_approval_is_bound_to_exact_video_hash(self):
        self.video.write_bytes(b"substituted video")
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate()

    def test_different_google_account_is_rejected_even_when_channel_matches(self):
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(owner=AuthenticatedChannelOwner("other-subject", OWNER.channel_id))

    def test_different_destination_channel_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(owner=AuthenticatedChannelOwner(OWNER.google_subject, "another-channel"))

    def test_different_google_subject_on_same_channel_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(owner=AuthenticatedChannelOwner("different-google-subject", OWNER.channel_id))

    def test_privacy_mismatch_is_rejected(self):
        with self.assertRaisesRegex(PermissionError, "does not match"):
            self.gate(privacy="public")

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

    def test_directory_approval_path_is_rejected(self):
        directory_path = self.root / "approval-directory"
        directory_path.mkdir()
        with self.assertRaisesRegex(PermissionError, "must be a regular file"):
            self.gate(approval_path=directory_path)

    def test_symlinked_approval_record_is_rejected_without_reading_target(self):
        target = self.root / "external-approval.json"
        target.write_text(self.record.read_text(encoding="utf-8"), encoding="utf-8")
        link = self.root / "approval-link.json"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable on this platform")
        with self.assertRaisesRegex(PermissionError, "must not be a symlink"):
            self.gate(approval_path=link)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["decision"], "approved")

    def test_fifo_approval_path_is_rejected_without_blocking(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO creation is unavailable on this platform")
        fifo_path = self.root / "approval.fifo"
        os.mkfifo(fifo_path)
        with self.assertRaisesRegex(PermissionError, "must be a regular file"):
            self.gate(approval_path=fifo_path)

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
        self.assertEqual(data["reviewer_google_subject"], OWNER.google_subject)
        self.assertEqual(data["reviewer_channel_id"], OWNER.channel_id)
        self.assertEqual(data["privacy"], "private")
        self.assertEqual(data["destination_channel_id"], OWNER.channel_id)
        self.assertEqual(data["source_sha256"], sha256_file(self.video))
        self.assertEqual(data["decision"], "approved")
        self.assertTrue(data["reviewed_at"].endswith("+00:00"))
        self.assertTrue(data["expires_at"].endswith("+00:00"))


if __name__ == "__main__":
    unittest.main()
