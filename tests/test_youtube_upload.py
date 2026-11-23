"""Tests for gated YouTube upload without making network requests."""
import io
import json
import os
import sys
import tempfile
import types
import unittest
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from backend.app.rights_registry import SourceRightsRegistry
from backend.app.youtube_owner_approval import AuthenticatedChannelOwner, write_owner_approval_record
from backend.app.youtube_upload import (
    _copy_stream_with_limit, build_upload_body, load_rights_report,
    upload_video, validate_upload,
)


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
            made_for_kids=True, owner_approved=True, rights_confirmed=True,
            upload_requested=True, privacy="unlisted",
        )
        self.assertEqual(video, self.video)
        self.assertEqual(body["status"]["privacyStatus"], "unlisted")
        self.assertTrue(body["status"]["selfDeclaredMadeForKids"])

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

    def test_validate_upload_rejects_file_above_memory_budget(self):
        with self.assertRaisesRegex(ValueError, "configured upload limit"):
            validate_upload(
                self.video, self.report, title="Short", made_for_kids=False,
                max_upload_bytes=4,
            )

    def test_snapshot_copy_stops_before_writing_bytes_over_limit(self):
        source = io.BytesIO(b"12345")
        snapshot = io.BytesIO()
        with self.assertRaisesRegex(ValueError, "configured upload limit"):
            _copy_stream_with_limit(source, snapshot, max_upload_bytes=4)
        self.assertEqual(snapshot.getvalue(), b"")

    def test_snapshot_copy_rejects_later_chunk_that_exceeds_cumulative_limit(self):
        source = Mock()
        source.read.side_effect = [b"1234", b"5"]
        snapshot = io.BytesIO()

        with self.assertRaisesRegex(ValueError, "configured upload limit"):
            _copy_stream_with_limit(source, snapshot, max_upload_bytes=4)

        # The first in-budget chunk is retained; the over-budget second chunk
        # is rejected before it can be written to the snapshot.
        self.assertEqual(snapshot.getvalue(), b"1234")
        self.assertEqual(source.read.call_count, 2)

    def test_max_upload_bytes_must_be_positive(self):
        for invalid in (0, -1, True):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    validate_upload(
                        self.video, self.report, title="Short", made_for_kids=False,
                        max_upload_bytes=invalid,
                    )

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
        http.MediaIoBaseUpload = Mock(side_effect=lambda stream, **kwargs: SimpleNamespace(stream=stream))
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
        youtube.videos.return_value.insert.return_value.execute.return_value = {"id": "video-123"}
        with patch.dict(sys.modules, self._mock_google_modules(youtube)):
            with patch.dict(os.environ, {"ARO_YOUTUBE_OWNER_GOOGLE_SUBJECT": "google-subject-123", "ARO_YOUTUBE_CHANNEL_ID": "youtube-channel-456"}):
                with patch("backend.app.youtube_upload._authorize_google", return_value=object()), patch("backend.app.youtube_owner_approval.verify_authenticated_channel_owner", return_value=self.owner) as verify_owner:
                    result = upload_video(
                        self.video, {"snippet": {"title": "Test"}, "status": {"privacyStatus": "private"}},
                        client_secrets=self.client_secrets, token_path=self.root / "token.json",
                        rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                        rights_db_path=db_path, clip_id="clip-1", source_id="source-1",
                        owner_approved=True, rights_confirmed=True,
                    )
        self.assertEqual(result["video_id"], "video-123")
        self.assertEqual(verify_owner.call_count, 2)
        youtube.videos.return_value.insert.assert_called_once()

    def test_upload_uses_approved_snapshot_when_original_changes_after_staging(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        approved_bytes = self.video.read_bytes()
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "youtube-channel-456"}]
        }
        captured = {}

        def execute_upload(num_retries):
            media_body = youtube.videos.return_value.insert.call_args.kwargs["media_body"]
            media_body.stream.seek(0)
            captured["uploaded_bytes"] = media_body.stream.read()
            return {"id": "snapshot-video"}

        youtube.videos.return_value.insert.return_value.execute.side_effect = execute_upload

        def media_io_upload(stream, **kwargs):
            # Simulate another process replacing the caller's source path after
            # the private snapshot has been made but before the API consumes it.
            self.video.write_bytes(b"attacker-substituted bytes")
            return SimpleNamespace(stream=stream)

        modules = self._mock_google_modules(youtube)
        modules["googleapiclient.http"].MediaIoBaseUpload = Mock(side_effect=media_io_upload)
        with patch.dict(sys.modules, modules):
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
                        owner_approved=True, rights_confirmed=True,
                    )

        self.assertEqual(result["video_id"], "snapshot-video")
        self.assertEqual(captured["uploaded_bytes"], approved_bytes)
        self.assertNotEqual(captured["uploaded_bytes"], self.video.read_bytes())
        youtube.videos.return_value.insert.assert_called_once()

    def test_staged_file_mutation_after_final_checks_cannot_change_upload_payload(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        approved_bytes = self.video.read_bytes()
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "youtube-channel-456"}]
        }
        staged = {}
        captured = {}
        real_tempdir = tempfile.TemporaryDirectory

        class RecordingTemporaryDirectory:
            def __init__(self, *args, **kwargs):
                self._delegate = real_tempdir(*args, **kwargs)

            def __enter__(self):
                directory = self._delegate.__enter__()
                staged["path"] = Path(directory) / "approved-upload.mp4"
                return directory

            def __exit__(self, *exc_info):
                return self._delegate.__exit__(*exc_info)

        def execute_upload(num_retries):
            media_body = youtube.videos.return_value.insert.call_args.kwargs["media_body"]
            media_body.stream.seek(0)
            captured["uploaded_bytes"] = media_body.stream.read()
            return {"id": "immutable-snapshot-video"}

        def mutate_staged_file_after_final_checks(*args, **kwargs):
            # insert() is reached only after the final approval/hash and
            # rights checks. Simulate a same-user filesystem mutation before
            # execute() consumes the media stream.
            snapshot_path = staged["path"]
            os.chmod(snapshot_path, 0o600)
            snapshot_path.write_bytes(b"tampered after final approval checks")
            captured["staged_bytes_after_gate"] = snapshot_path.read_bytes()
            return youtube.videos.return_value.insert.return_value

        youtube.videos.return_value.insert.side_effect = mutate_staged_file_after_final_checks
        youtube.videos.return_value.insert.return_value.execute.side_effect = execute_upload
        modules = self._mock_google_modules(youtube)
        modules["googleapiclient.http"].MediaIoBaseUpload = Mock(
            side_effect=lambda stream, **kwargs: SimpleNamespace(stream=stream)
        )

        with patch("backend.app.youtube_upload.tempfile.TemporaryDirectory", RecordingTemporaryDirectory):
            with patch.dict(sys.modules, modules):
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
                            owner_approved=True, rights_confirmed=True,
                        )

        self.assertEqual(result["video_id"], "immutable-snapshot-video")
        self.assertEqual(captured["staged_bytes_after_gate"], b"tampered after final approval checks")
        self.assertEqual(captured["uploaded_bytes"], approved_bytes)
        self.assertNotEqual(captured["uploaded_bytes"], captured["staged_bytes_after_gate"])
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
                            owner_approved=True, rights_confirmed=True,
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
                            owner_approved=True, rights_confirmed=True,
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
                    with self.assertRaisesRegex(PermissionError, "does not match"):
                        upload_video(
                            self.video, {"snippet": {"title": "Test"}, "status": {"privacyStatus": "public"}},
                            client_secrets=self.client_secrets, token_path=self.root / "token.json",
                            rights_report_path=self.report, approval_record_path=self.root / "approval.json",
                            rights_db_path=db_path, clip_id="clip-1", source_id="source-1",
                            owner_approved=True, rights_confirmed=True,
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
                            owner_approved=True, rights_confirmed=True,
                        )
        youtube.videos.return_value.insert.assert_not_called()

    def test_cli_passes_exact_clip_and_source_to_upload_boundary(self):
        db_path = self.root / "source_rights.sqlite3"
        self._write_upload_rights(db_path)
        approval_path = self.root / "approval.json"
        args = [
            "youtube_upload.py", str(self.video), "--rights-report", str(self.report),
            "--title", "THE ARO test", "--not-made-for-kids", "--upload",
            "--owner-approved", "--confirm-rights", "--clip-id", "clip-1",
            "--source-id", "source-1", "--approval-record", str(approval_path),
            "--rights-db", str(db_path),
        ]
        with patch.object(sys, "argv", args):
            with patch("backend.app.youtube_upload.upload_video", return_value={"video_id": "mock-id", "url": "https://youtube.invalid/mock-id"}) as upload:
                from backend.app.youtube_upload import main
                self.assertEqual(main(), 0)
        self.assertEqual(upload.call_args.kwargs["clip_id"], "clip-1")
        self.assertEqual(upload.call_args.kwargs["source_id"], "source-1")
        self.assertTrue(upload.call_args.kwargs["owner_approved"])
        self.assertTrue(upload.call_args.kwargs["rights_confirmed"])


if __name__ == "__main__":
    unittest.main()
