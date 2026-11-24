"""Tests for gated YouTube upload without making network requests."""
import hashlib
import io
import json
import os
import sys
import tempfile
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.rights_registry import SourceRightsRegistry
from backend.app.youtube_owner_approval import AuthenticatedChannelOwner, write_owner_approval_record
from backend.app.youtube_upload import (build_upload_body, load_destination_profile, load_rights_report, resolve_destination_identity, upload_video, validate_upload, _persist_oauth_token, _copy_upload_snapshot, _validate_max_upload_bytes)


class YouTubeUploadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.video = self.root / "short.mp4"
        self.video.write_bytes(b"synthetic video bytes")
        self.client_secrets = self.root / "client.json"
        self.client_secrets.write_text(json.dumps({"installed": {"client_id": "mock-client-id"}}), encoding="utf-8")
        self.report = self.root / "preflight.json"
        self.report.write_text(json.dumps({
            "status": "ready_for_human_review",
            "platform": "youtube",
            "assets": [{"asset_id": "aro-graphic", "status": "declared_original_requires_human_confirmation"}],
            "errors": [],
            "review": {
                "approved_for_upload": False,
                "monetization_guaranteed": False,
                "permission_evidence_human_verification_required": True,
                "all_embedded_music_and_third_party_rights_review_required": True,
                "original_asset_declarations_human_confirmation_required": True,
                "human_edit_and_platform_policy_review_required": True,
            },
        }), encoding="utf-8")
        self.client_secrets = self.root / "client.json"
        self.client_secrets.write_text(
            json.dumps({"installed": {"client_id": "client-id"}}), encoding="utf-8"
        )
        self.owner = AuthenticatedChannelOwner("google-subject-123", "youtube-channel-456")

    def tearDown(self):
        self.temp.cleanup()

    def test_dry_run_validates_without_owner_or_upload_flags(self):
        video, body = validate_upload(
            self.video, self.report, title="THE ARO GTA 6 Short",
            tags=["GTA6", "THEARO"], made_for_kids=False,
        )
        self.assertEqual(video, self.video)
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertFalse(body["status"]["selfDeclaredMadeForKids"])

    def test_actual_upload_requires_both_explicit_approvals(self):
        with self.assertRaisesRegex(PermissionError, "owner-approved"):
            validate_upload(
                self.video, self.report, title="Approved title",
                made_for_kids=False, rights_confirmed=True, upload_requested=True,
            )
        with self.assertRaisesRegex(PermissionError, "confirm-rights"):
            validate_upload(
                self.video, self.report, title="Approved title",
                made_for_kids=False, owner_approved=True, upload_requested=True,
            )

    def test_actual_upload_validation_passes_with_both_approvals(self):
        video, body = validate_upload(
            self.video, self.report, title="Approved title",
            made_for_kids=True, owner_approved=True, rights_confirmed=True, max_upload_bytes=1024 * 1024, max_upload_bytes=1024 * 1024,
                            max_upload_bytes=1024 * 1024,
            upload_requested=True, privacy="unlisted",
        )
        self.assertEqual(video, self.video)
        self.assertEqual(body["status"]["privacyStatus"], "unlisted")
        self.assertTrue(body["status"]["selfDeclaredMadeForKids"])

    def test_max_upload_bytes_must_be_positive_integer(self):
        for invalid in (0, -1, True, 1.5, "100"):
            with self.assertRaises(ValueError):
                _validate_max_upload_bytes(invalid)
        self.assertEqual(_validate_max_upload_bytes(1024), 1024)

    def test_validate_upload_rejects_file_above_configured_limit(self):
        with self.assertRaisesRegex(ValueError, "configured upload limit"):
            validate_upload(
                self.video, self.report, title="Short", made_for_kids=False,
                max_upload_bytes=5,
            )

    def test_snapshot_copy_is_disk_backed_and_hashes_exact_bytes(self):
        source = self.root / "snapshot-source.mp4"
        snapshot = self.root / "snapshot-copy.mp4"
        payload = b"0123456789" * 1000
        source.write_bytes(payload)
        copied, digest = _copy_upload_snapshot(source, snapshot, len(payload))
        self.assertEqual(copied, len(payload))
        self.assertEqual(snapshot.read_bytes(), payload)
        self.assertEqual(digest, hashlib.sha256(payload).hexdigest())
        if os.name == "posix":
            self.assertEqual(snapshot.stat().st_mode & 0o777, 0o400)

    def test_snapshot_copy_rejects_oversize_and_removes_partial_snapshot(self):
        source = self.root / "oversize-source.mp4"
        snapshot = self.root / "oversize-copy.mp4"
        source.write_bytes(b"x" * 32)
        with self.assertRaisesRegex(ValueError, "configured upload limit"):
            _copy_upload_snapshot(source, snapshot, 16)
        self.assertFalse(snapshot.exists())

    def test_upload_requires_explicit_device_limit_before_oauth(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        with patch("backend.app.youtube_upload._authorize_google") as authorize:
            with self.assertRaisesRegex(PermissionError, "explicit device-selected"):
                upload_video(
                    self.video,
                    {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                    client_secrets=self.client_secrets, token_path=self.root / "token.json",
                    rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                    rights_db_path=db_path, clip_id="clip-1", source_id="source-1",
                    owner_approved=True, rights_confirmed=True
                )
        authorize.assert_not_called()

    def test_upload_growth_after_initial_stat_fails_before_oauth(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        original_copy = _copy_upload_snapshot

        def grow_source(source_path, snapshot_path, max_bytes):
            Path(source_path).write_bytes(b"g" * 128)
            return original_copy(source_path, snapshot_path, max_bytes)

        with patch("backend.app.youtube_upload._copy_upload_snapshot", side_effect=grow_source):
            with patch("backend.app.youtube_upload._authorize_google") as authorize:
                with self.assertRaisesRegex(ValueError, "configured upload limit"):
                    upload_video(
                        self.video,
                        {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                        client_secrets=self.client_secrets, token_path=self.root / "token.json",
                        rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                        rights_db_path=db_path, clip_id="clip-1", source_id="source-1",
                        owner_approved=True, rights_confirmed=True, max_upload_bytes=64,
                    )
        authorize.assert_not_called()

    def test_upload_uses_approved_disk_snapshot_if_original_changes_during_insert(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        original_payload = self.video.read_bytes()
        youtube = Mock()
        staged_paths = []

        def execute(num_retries):
            stream = self.media_io_upload.call_args.args[0]
            staged_path = Path(stream.name)
            staged_paths.append(staged_path)
            self.assertTrue(staged_path.is_file())
            self.assertTrue(staged_path.parent.name.startswith("aro-youtube-upload-"))
            self.assertNotIsInstance(stream, io.BytesIO)
            self.video.write_bytes(b"changed after staging")
            stream.seek(0)
            self.assertEqual(stream.read(), original_payload)
            return {"id": "snapshot-video", "status": {"privacyStatus": "private"}}

        youtube.videos.return_value.insert.return_value.execute.side_effect = execute
        with patch.dict(sys.modules, self._mock_google_modules(youtube)):
            with patch.dict(os.environ, {
                "ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123",
                "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456",
            }):
                with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch(
                    "backend.app.youtube_owner_approval.verify_authenticated_channel_owner",
                    return_value=self.owner,
                ):
                    result = upload_video(
                        self.video,
                        {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                        client_secrets=self.client_secrets, token_path=self.root / "token.json",
                        rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                        rights_db_path=db_path, clip_id="clip-1", source_id="source-1",
                        owner_approved=True, rights_confirmed=True, max_upload_bytes=1024 * 1024,
                    )
        self.assertEqual(result["video_id"], "snapshot-video")
        self.assertEqual(self.media_io_upload.call_args.kwargs["chunksize"], 1024 * 1024)
        self.assertFalse(staged_paths[0].exists())
        youtube.videos.return_value.insert.assert_called_once()

    def test_cli_live_upload_requires_explicit_device_limit_before_oauth(self):
        args = [
            "youtube_upload.py", str(self.video), "--rights-report", str(self.report),
            "--title", "THE ARO test", "--not-made-for-kids", "--upload",
            "--owner-approved", "--confirm-rights",
        ]
        with patch.object(sys, "argv", args):
            with patch("backend.app.youtube_upload.resolve_destination_identity") as resolve:
                with patch("backend.app.youtube_upload._authorize_google") as authorize:
                    from backend.app.youtube_upload import main
                    self.assertEqual(main(), 2)
        resolve.assert_not_called()
        authorize.assert_not_called()

    def test_blocked_or_missing_rights_report_fails_closed(self):
        blocked = self.root / "blocked.json"
        blocked.write_text(json.dumps({"status": "blocked", "errors": ["no permission"], "assets": []}), encoding="utf-8")
        with self.assertRaisesRegex(PermissionError, "not ready"):
            load_rights_report(blocked)
        with self.assertRaises(FileNotFoundError):
            load_rights_report(self.root / "missing.json")

    def test_rights_report_must_target_youtube_and_have_assets(self):
        report = json.loads(self.report.read_text(encoding="utf-8"))
        report["platform"] = "tiktok"
        self.report.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(PermissionError, "target the youtube"):
            load_rights_report(self.report)
        report["platform"] = "youtube"
        report["assets"] = []
        self.report.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(PermissionError, "at least one declared"):
            load_rights_report(self.report)

    def test_rights_report_requires_all_human_review_gates(self):
        report = json.loads(self.report.read_text(encoding="utf-8"))
        report["review"]["all_embedded_music_and_third_party_rights_review_required"] = False
        self.report.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(PermissionError, "mandatory human-review gates"):
            load_rights_report(self.report)

    def test_rejects_remote_or_missing_video_paths(self):
        with self.assertRaises(FileNotFoundError):
            validate_upload("https://example.com/short.mp4", self.report, title="Short", made_for_kids=False)

    def test_rejects_invalid_title_and_privacy(self):
        with self.assertRaisesRegex(ValueError, "title"):
            build_upload_body(title=" ", description="", tags=[], privacy="private", made_for_kids=False)
        with self.assertRaisesRegex(ValueError, "100 characters"):
            build_upload_body(title="x" * 101, description="", tags=[], privacy="private", made_for_kids=False)
        with self.assertRaisesRegex(ValueError, "privacy"):
            build_upload_body(title="Short", description="", tags=[], privacy="everyone", made_for_kids=False)

    def test_rejects_overlong_tags(self):
        with self.assertRaisesRegex(ValueError, "100 characters"):
            build_upload_body(title="Short", description="", tags=["x" * 101], privacy="private", made_for_kids=False)

    def test_rejects_empty_video(self):
        empty = self.root / "empty.mp4"
        empty.touch()
        with self.assertRaisesRegex(ValueError, "empty"):
            validate_upload(empty, self.report, title="Short", made_for_kids=False)

    def _write_upload_rights(self, db_path):
        now = datetime.now(timezone.utc)
        registry = SourceRightsRegistry(db_path)
        registry.register({
            "source_id": "source-1",
            "source_url": "https://example.invalid/owner-provided-source",
            "grantor": "creator-owner",
            "evidence_ref": "local-evidence:permission-001",
            "allowed_uses": ["edit", "publish"],
            "platforms": ["youtube"],
            "valid_from": (now - timedelta(hours=1)).isoformat(),
            "expires_at": (now + timedelta(days=1)).isoformat(),
        })
        report = json.loads(self.report.read_text(encoding="utf-8"))
        report.update({"clip_id": "clip-1", "source_id": "source-1"})
        self.report.write_text(json.dumps(report), encoding="utf-8")
        owner = self.owner
        approval_path = self.root / "approval.json"
        write_owner_approval_record(
            approval_path, clip_id="clip-1", source_id="source-1",
            video_path=self.video, owner=owner, privacy="private", confirmed=True,
        )
        return registry, owner, approval_path

    def _mock_google_modules(self, youtube):
        package = types.ModuleType("googleapiclient")
        discovery = types.ModuleType("googleapiclient.discovery")
        http = types.ModuleType("googleapiclient.http")
        discovery.build = Mock(return_value=youtube)
        self.media_io_upload = Mock(return_value=object())
        http.MediaIoBaseUpload = self.media_io_upload
        package.discovery = discovery
        package.http = http
        return {
            "googleapiclient": package,
            "googleapiclient.discovery": discovery,
            "googleapiclient.http": http,
        }

    def test_upload_rechecks_oauth_owner_and_live_rights_before_api_insert(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "youtube-channel-456"}]
        }
        youtube.videos.return_value.insert.return_value.execute.return_value = {"id": "video-123", "status": {"privacyStatus": "private"}}
        with patch.dict(sys.modules, self._mock_google_modules(youtube)):
            with patch.dict(os.environ, {"ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123", "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456"}):
                with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch("backend.app.youtube_owner_approval.verify_authenticated_channel_owner", return_value=self.owner) as verify_owner:
                    result = upload_video(
                        self.video, {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                        client_secrets=self.client_secrets, token_path=self.root / "token.json",
                        rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                        rights_db_path=db_path, clip_id="clip-1", source_id="source-1",
                        owner_approved=True, rights_confirmed=True, max_upload_bytes=1024 * 1024,
                    )
        self.assertEqual(result["video_id"], "video-123")
        self.assertEqual(verify_owner.call_count, 2)
        youtube.videos.return_value.insert.assert_called_once()

    def test_upload_does_not_report_success_without_private_visibility_confirmation(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        youtube = Mock()
        youtube.videos.return_value.insert.return_value.execute.return_value = {
            "id": "video-456",
            "status": {"privacyStatus": "unlisted"},
        }
        with patch.dict(sys.modules, self._mock_google_modules(youtube)):
            with patch.dict(os.environ, {
                "ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123",
                "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456",
            }):
                with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch(
                    "backend.app.youtube_owner_approval.verify_authenticated_channel_owner",
                    return_value=self.owner,
                ):
                    with self.assertRaisesRegex(RuntimeError, "did not confirm PRIVATE visibility"):
                        upload_video(
                            self.video,
                            {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                            client_secrets=self.client_secrets,
                            token_path=self.root / "token.json",
                            rights_report_path=self.report,
                            approval_record_path=self.root / "approval.json",
                            rights_db_path=db_path,
                            clip_id="clip-1",
                            source_id="source-1",
                            owner_approved=True,
                            rights_confirmed=True,
                            max_upload_bytes=1024 * 1024,
                        )
        youtube.videos.return_value.insert.assert_called_once()

    def test_upload_does_not_report_success_when_response_omits_visibility(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        youtube = Mock()
        youtube.videos.return_value.insert.return_value.execute.return_value = {
            "id": "video-789",
        }
        with patch.dict(sys.modules, self._mock_google_modules(youtube)):
            with patch.dict(os.environ, {
                "ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123",
                "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456",
            }):
                with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch(
                    "backend.app.youtube_owner_approval.verify_authenticated_channel_owner",
                    return_value=self.owner,
                ):
                    with self.assertRaisesRegex(RuntimeError, "did not confirm PRIVATE visibility"):
                        upload_video(
                            self.video,
                            {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                            client_secrets=self.client_secrets,
                            token_path=self.root / "token.json",
                            rights_report_path=self.report,
                            approval_record_path=self.root / "approval.json",
                            rights_db_path=db_path,
                            clip_id="clip-1",
                            source_id="source-1",
                            owner_approved=True,
                            rights_confirmed=True,
                        )
        youtube.videos.return_value.insert.assert_called_once()

    def test_revoked_permission_blocks_before_any_upload_api_request(self):
        db_path = self.root / "source_rights.sqlite3"
        registry, _, _ = self._write_upload_rights(db_path)
        registry.revoke("source-1", actor="test-owner")
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "youtube-channel-456"}]
        }
        with patch.dict(sys.modules, self._mock_google_modules(youtube)):
            with patch.dict(os.environ, {"ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123", "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456"}):
                with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch("backend.app.youtube_owner_approval.verify_authenticated_channel_owner", return_value=self.owner):
                    with self.assertRaises(PermissionError):
                        upload_video(
                            self.video, {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                            client_secrets=self.client_secrets, token_path=self.root / "token.json",
                            rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                            rights_db_path=db_path, clip_id="clip-1", source_id="source-1",
                            owner_approved=True, rights_confirmed=True, max_upload_bytes=1024 * 1024,
                        )
        youtube.videos.return_value.insert.assert_not_called()

    def test_wrong_channel_blocks_before_any_upload_api_request(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "another-channel"}]
        }
        with patch.dict(sys.modules, self._mock_google_modules(youtube)):
            with patch.dict(os.environ, {"ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123", "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456"}):
                with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch("backend.app.youtube_owner_approval.verify_authenticated_channel_owner", side_effect=PermissionError("OAuth account does not resolve to the configured destination channel")):
                    with self.assertRaisesRegex(PermissionError, "does not resolve"):
                        upload_video(
                            self.video, {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                            client_secrets=self.client_secrets, token_path=self.root / "token.json",
                            rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                            rights_db_path=db_path, clip_id="clip-1", source_id="source-1",
                            owner_approved=True, rights_confirmed=True, max_upload_bytes=1024 * 1024,
                        )
        youtube.videos.return_value.insert.assert_not_called()

    def test_cli_requires_typed_per_clip_confirmation_to_record_approval(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "youtube-channel-456"}]
        }
        args = [
            "youtube_upload.py", str(self.video), "--rights-report", str(self.report),
            "--title", "THE ARO test", "--not-made-for-kids", "--approve-clip", "--client-secrets", str(self.client_secrets),
            "--clip-id", "clip-1", "--source-id", "source-1",
            "--approval-record", str(self.root / "new-approval.json"),
            "--rights-db", str(db_path),
        ]
        with patch.object(sys, "argv", args):
            with patch.dict(sys.modules, self._mock_google_modules(youtube)):
                with patch.dict(os.environ, {"ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123", "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456"}):
                    with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch("backend.app.youtube_owner_approval.verify_authenticated_channel_owner", return_value=self.owner):
                        with patch("builtins.input", return_value="NO"):
                            from backend.app.youtube_upload import main
                            self.assertEqual(main(), 2)
        self.assertFalse((self.root / "new-approval.json").exists())
        youtube.videos.return_value.insert.assert_not_called()

    def test_cli_records_approval_only_after_exact_typed_confirmation(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "youtube-channel-456"}]
        }
        approval_path = self.root / "new-approval.json"
        args = [
            "youtube_upload.py", str(self.video), "--rights-report", str(self.report),
            "--title", "THE ARO test", "--not-made-for-kids", "--approve-clip", "--client-secrets", str(self.client_secrets),
            "--clip-id", "clip-1", "--source-id", "source-1",
            "--approval-record", str(approval_path), "--rights-db", str(db_path),
        ]
        with patch.object(sys, "argv", args):
            with patch.dict(sys.modules, self._mock_google_modules(youtube)):
                with patch.dict(os.environ, {"ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123", "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456"}):
                    with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch("backend.app.youtube_owner_approval.verify_authenticated_channel_owner", return_value=self.owner):
                        with patch("builtins.input", return_value="APPROVE PRIVATE clip-1"):
                            from backend.app.youtube_upload import main
                            self.assertEqual(main(), 0)
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
        self.assertEqual(approval["clip_id"], "clip-1")
        self.assertEqual(approval["source_id"], "source-1")
        self.assertEqual(approval["reviewer_channel_id"], "youtube-channel-456")
        self.assertEqual(approval["reviewer_google_subject"], "google-subject-123")
        self.assertEqual(approval["privacy"], "private")
        youtube.videos.return_value.insert.assert_not_called()

    def test_upload_rejects_different_google_account_even_for_same_channel(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        youtube = Mock()
        google = types.ModuleType("google")
        auth = types.ModuleType("google.auth")
        transport = types.ModuleType("google.auth.transport")
        requests = types.ModuleType("google.auth.transport.requests")
        oauth2 = types.ModuleType("google.oauth2")
        id_token = types.ModuleType("google.oauth2.id_token")
        requests.Request = Mock(return_value=object())
        id_token.verify_oauth2_token = Mock(return_value={
            "sub": "different-google-subject",
            "iss": "https://accounts.google.com",
            "azp": "client-id",
        })
        google.auth = auth
        auth.transport = transport
        transport.requests = requests
        google.oauth2 = oauth2
        oauth2.id_token = id_token
        modules = self._mock_google_modules(youtube)
        modules.update({
            "google": google,
            "google.auth": auth,
            "google.auth.transport": transport,
            "google.auth.transport.requests": requests,
            "google.oauth2": oauth2,
            "google.oauth2.id_token": id_token,
        })
        with patch.dict(sys.modules, modules):
            with patch.dict(os.environ, {
                "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456",
                "ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-456",
            }):
                with patch(
                    "backend.app.youtube_upload._authorize_google",
                    return_value=Mock(id_token="mock-token"),
                ):
                    with self.assertRaisesRegex(
                        PermissionError, "not the configured channel owner"
                    ):
                        upload_video(
                            self.video,
                            {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                            client_secrets=self.client_secrets,
                            token_path=self.root / "token.json",
                            rights_report_path=self.report,
                            approval_record_path=self.root / "approval.json",
                            rights_db_path=db_path,
                            clip_id="clip-1",
                            source_id="source-1",
                            owner_approved=True,
                            rights_confirmed=True,
                        )
        id_token.verify_oauth2_token.assert_called_once_with(
            "mock-token", unittest.mock.ANY, audience="client-id"
        )
        youtube.channels.assert_not_called()
        youtube.videos.return_value.insert.assert_not_called()

    def test_upload_rejects_private_approval_for_public_visibility(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        youtube = Mock()
        with patch.dict(sys.modules, self._mock_google_modules(youtube)):
            with patch.dict(os.environ, {"ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123", "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456"}):
                with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch("backend.app.youtube_owner_approval.verify_authenticated_channel_owner", return_value=self.owner):
                    with self.assertRaisesRegex(PermissionError, "only permits PRIVATE"):
                        upload_video(
                            self.video, {"snippet": {"title": "Test"}, "status": {"privacyStatus": "public"}},
                            client_secrets=self.client_secrets, token_path=self.root / "token.json",
                            rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                            rights_db_path=db_path, clip_id="clip-1", source_id="source-1",
                            owner_approved=True, rights_confirmed=True, max_upload_bytes=1024 * 1024,
                        )
        youtube.videos.return_value.insert.assert_not_called()

    def test_upload_rejects_clip_or_source_identifier_mismatch(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "youtube-channel-456"}]
        }
        with patch.dict(sys.modules, self._mock_google_modules(youtube)):
            with patch.dict(os.environ, {"ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123", "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456"}):
                with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch("backend.app.youtube_owner_approval.verify_authenticated_channel_owner", return_value=self.owner):
                    with self.assertRaisesRegex(PermissionError, "do not match"):
                        upload_video(
                            self.video, {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                            client_secrets=self.client_secrets, token_path=self.root / "token.json",
                            rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                            rights_db_path=db_path, clip_id="other-clip", source_id="source-1",
                            owner_approved=True, rights_confirmed=True, max_upload_bytes=1024 * 1024,
                        )
        youtube.videos.return_value.insert.assert_not_called()

    def test_cli_passes_exact_clip_and_source_to_upload_boundary(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        approval_path = self.root / "approval.json"
        args = [
            "youtube_upload.py", str(self.video), "--rights-report", str(self.report),
            "--title", "THE ARO test", "--not-made-for-kids", "--upload",
            "--owner-approved", "--confirm-rights", "--max-upload-bytes", "1048576", "--clip-id", "clip-1",
            "--source-id", "source-1", "--approval-record", str(approval_path),
            "--rights-db", str(db_path),
        ]
        with patch.object(sys, "argv", args), patch.dict(os.environ, {
            "ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123",
            "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456",
        }):
            with patch("backend.app.youtube_upload.upload_video", return_value={"video_id": "mock-id", "url": "https://youtube.invalid/mock-id"}) as upload:
                from backend.app.youtube_upload import main
                self.assertEqual(main(), 0)
        self.assertEqual(upload.call_args.kwargs["clip_id"], "clip-1")
        self.assertEqual(upload.call_args.kwargs["source_id"], "source-1")
        self.assertEqual(upload.call_args.kwargs["expected_google_subject"], "google-subject-123")
        self.assertEqual(upload.call_args.kwargs["expected_channel_id"], "youtube-channel-456")
        self.assertTrue(upload.call_args.kwargs["owner_approved"])
        self.assertTrue(upload.call_args.kwargs["rights_confirmed"])
        self.assertEqual(upload.call_args.kwargs["max_upload_bytes"], 1048576)


    def test_upload_rejects_unlisted_visibility_before_oauth_or_api(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        with patch("backend.app.youtube_upload._authorize_google") as authorize:
            with self.assertRaisesRegex(PermissionError, "only permits PRIVATE"):
                upload_video(
                    self.video, {"snippet": {"title": "Test"}, "status": {"privacyStatus": "unlisted"}},
                    client_secrets=self.client_secrets, token_path=self.root / "token.json",
                    rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                    rights_db_path=db_path, clip_id="clip-1", source_id="source-1",
                    owner_approved=True, rights_confirmed=True, max_upload_bytes=1024 * 1024,
                )
        authorize.assert_not_called()


class OAuthTokenPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_token_is_written_atomically_with_restricted_permissions(self):
        target = self.root / "tokens" / "profile.json"
        _persist_oauth_token(target, '{"access_token":"test"}')
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"access_token": "test"})
        if os.name == "posix":
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_token_symlink_is_rejected_without_modifying_target(self):
        external = self.root / "external-token.json"
        external.write_text('{"access_token":"keep"}', encoding="utf-8")
        target = self.root / "tokens" / "profile.json"
        target.parent.mkdir()
        try:
            target.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links are unavailable in this environment")
        with self.assertRaisesRegex(PermissionError, "symbolic link"):
            _persist_oauth_token(target, '{"access_token":"replace"}')
        self.assertEqual(external.read_text(encoding="utf-8"), '{"access_token":"keep"}')

    def test_failed_atomic_replace_preserves_existing_token_and_cleans_temp_file(self):
        target = self.root / "tokens" / "profile.json"
        target.parent.mkdir()
        target.write_text('{"access_token":"old"}', encoding="utf-8")
        with patch("backend.app.youtube_upload.os.replace", side_effect=OSError("simulated replace failure")):
            with self.assertRaisesRegex(OSError, "simulated replace failure"):
                _persist_oauth_token(target, '{"access_token":"new"}')
        self.assertEqual(target.read_text(encoding="utf-8"), '{"access_token":"old"}')
        self.assertEqual(list(target.parent.iterdir()), [target])


class YouTubeDestinationProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        secrets_dir = self.root / ".secrets"
        secrets_dir.mkdir()
        self.config = secrets_dir / "destination_profiles.json"
        self.config.write_text(json.dumps({
            "profiles": {
                "aroanmol7": {
                    "google_subject": "google-subject-one",
                    "channel_id": "UC1234567890abcdef",
                },
                "the_arro07": {
                    "google_subject": "google-subject-two",
                    "channel_id": "UCabcdef1234567890",
                },
            }
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_profiles_resolve_to_distinct_channel_and_token_paths(self):
        first = load_destination_profile(self.config, "aroanmol7", repository_root=self.root)
        second = load_destination_profile(self.config, "the_arro07", repository_root=self.root)
        self.assertEqual(first["channel_id"], "UC1234567890abcdef")
        self.assertEqual(second["channel_id"], "UCabcdef1234567890")
        self.assertNotEqual(first["google_subject"], second["google_subject"])
        self.assertNotEqual(first["token_path"], second["token_path"])
        self.assertEqual(first["token_path"], self.root.resolve() / ".secrets" / "tokens" / "aroanmol7.json")

    def test_profile_name_cannot_escape_token_directory(self):
        with self.assertRaisesRegex(ValueError, "letters, numbers"):
            load_destination_profile(self.config, "../outside", repository_root=self.root)

    def test_profile_config_outside_ignored_secrets_directory_is_rejected(self):
        external = self.root / "destination_profiles_external.json"
        external.write_text(self.config.read_text(encoding="utf-8"), encoding="utf-8")
        with patch.object(Path, "read_text", side_effect=AssertionError("external config must not be read")):
            with self.assertRaisesRegex(PermissionError, "must resolve inside"):
                load_destination_profile(external, "aroanmol7", repository_root=self.root)

    def test_external_directory_named_secrets_is_rejected(self):
        external_secrets = self.root / "external" / ".secrets"
        external_secrets.mkdir(parents=True)
        external = external_secrets / "destination_profiles.json"
        external.write_text(self.config.read_text(encoding="utf-8"), encoding="utf-8")
        with patch.object(Path, "read_text", side_effect=AssertionError("external config must not be read")):
            with self.assertRaisesRegex(PermissionError, "this repository .secrets"):
                load_destination_profile(external, "aroanmol7", repository_root=self.root)

    def test_symlinked_token_directory_is_rejected(self):
        external_tokens = self.root / "external-tokens"
        external_tokens.mkdir()
        token_dir = self.root / ".secrets" / "tokens"
        try:
            token_dir.symlink_to(external_tokens, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symbolic links are unavailable in this environment")
        with self.assertRaisesRegex(PermissionError, "token directory must not be a symbolic link"):
            load_destination_profile(self.config, "aroanmol7", repository_root=self.root)

    def test_metadata_dry_run_does_not_require_oauth_profile(self):
        args = [
            "youtube_upload.py", str(self.root / "sample.mp4"),
            "--rights-report", str(self.root / "dryrun-report.json"),
            "--title", "THE ARO dry run", "--not-made-for-kids",
        ]
        (self.root / "sample.mp4").write_bytes(b"synthetic")
        (self.root / "dryrun-report.json").write_text(json.dumps({
            "status": "ready_for_human_review", "platform": "youtube",
            "assets": [{"status": "declared_original_requires_human_confirmation"}],
            "errors": [],
            "review": {
                "approved_for_upload": False,
                "permission_evidence_human_verification_required": True,
                "all_embedded_music_and_third_party_rights_review_required": True,
                "original_asset_declarations_human_confirmation_required": True,
                "human_edit_and_platform_policy_review_required": True,
            },
        }), encoding="utf-8")
        with patch.object(sys, "argv", args), patch.dict(os.environ, {}, clear=True):
            from backend.app.youtube_upload import main
            self.assertEqual(main(), 0)

    def test_unknown_profile_fails_closed(self):
        with self.assertRaisesRegex(PermissionError, "unknown destination profile"):
            load_destination_profile(self.config, "not-a-channel", repository_root=self.root)

    def test_duplicate_channel_mapping_fails_closed(self):
        payload = json.loads(self.config.read_text(encoding="utf-8"))
        payload["profiles"]["the_arro07"]["channel_id"] = payload["profiles"]["aroanmol7"]["channel_id"]
        self.config.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(PermissionError, "unique YouTube channel ID"):
            load_destination_profile(self.config, "aroanmol7", repository_root=self.root)

    def test_profile_requires_config_and_name_together(self):
        with self.assertRaisesRegex(PermissionError, "must be supplied together"):
            resolve_destination_identity(
                config_path=self.config, profile_name=None, token_override=None
            )

    def test_profile_token_path_cannot_be_overridden(self):
        with self.assertRaisesRegex(PermissionError, "cannot override"):
            resolve_destination_identity(
                config_path=self.config, profile_name="aroanmol7",
                token_override=self.root / "shared-token.json", repository_root=self.root,
            )

    def test_profile_resolution_keeps_channels_isolated(self):
        first = resolve_destination_identity(
            config_path=self.config, profile_name="aroanmol7", token_override=None, repository_root=self.root
        )
        second = resolve_destination_identity(
            config_path=self.config, profile_name="the_arro07", token_override=None, repository_root=self.root
        )
        self.assertEqual(first[1], "UC1234567890abcdef")
        self.assertEqual(second[1], "UCabcdef1234567890")
        self.assertNotEqual(first[2], second[2])



if __name__ == "__main__":
    unittest.main()
