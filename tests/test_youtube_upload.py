"""Tests for gated YouTube upload without making network requests."""
import json
import os
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from backend.app.approval import ApprovalStatus, UploadApproval
from backend.app.upload_approval_store import save_upload_approval
from backend.app.youtube_upload import (
    build_upload_body, load_rights_report, record_upload_approval,
    resolve_authenticated_channel_id, upload_video, validate_upload,
)


class YouTubeUploadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.video = self.root / "short.mp4"
        self.video.write_bytes(b"synthetic video bytes")
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

    def test_actual_upload_requires_explicit_rights_confirmation(self):
        with self.assertRaisesRegex(PermissionError, "confirm-rights"):
            validate_upload(
                self.video, self.report, title="Approved title",
                made_for_kids=False, upload_requested=True,
            )

    def test_actual_upload_validation_passes_with_both_approvals(self):
        video, body = validate_upload(
            self.video, self.report, title="Approved title",
            made_for_kids=True, rights_confirmed=True,
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

    def test_authenticated_channel_resolution_fails_closed_for_zero_or_multiple_channels(self):
        class Request:
            def __init__(self, items):
                self.items = items
            def execute(self, num_retries=0):
                return {"items": self.items}
        class Channels:
            def __init__(self, items):
                self.items = items
            def list(self, **kwargs):
                return Request(self.items)
        class YouTube:
            def __init__(self, items):
                self.items = items
            def channels(self):
                return Channels(self.items)

        self.assertEqual(resolve_authenticated_channel_id(YouTube([{"id": "UC_OWNER"}])), "UC_OWNER")
        with self.assertRaisesRegex(PermissionError, "exactly one"):
            resolve_authenticated_channel_id(YouTube([]))
        with self.assertRaisesRegex(PermissionError, "exactly one"):
            resolve_authenticated_channel_id(YouTube([{"id": "UC_A"}, {"id": "UC_B"}]))

    def test_approval_record_uses_oauth_channel_identity_not_cli_reviewer_text(self):
        permission = self.root / "permission.json"
        permission.write_text(json.dumps({
            "source_id": "source-001", "granted_by": "creator-001",
            "scopes": ["publish"], "granted_at": "2026-11-22T00:00:00+00:00",
            "expires_at": None, "revoked_at": None,
        }), encoding="utf-8")
        class Request:
            def execute(self, num_retries=0):
                return {"items": [{"id": "UC_AUTHENTICATED_OWNER"}]}
        class Channels:
            def list(self, **kwargs):
                return Request()
        class YouTube:
            def channels(self):
                return Channels()
        with patch("backend.app.youtube_upload._authorize_google", return_value=object()), \\
             patch("backend.app.youtube_upload._build_youtube_client", return_value=YouTube()), \\
             patch("builtins.input", return_value="APPROVE"), \\
             patch.dict(os.environ, {"ARO_UPLOAD_APPROVAL_KEY": "test-only-signing-key-with-32-bytes-minimum"}):
            approval_path = record_upload_approval(
                approval_record=self.root / "approval.json",
                permission_record=permission,
                clip_id="clip-001",
                source_id="source-001",
                expected_channel_id="UC_AUTHENTICATED_OWNER",
                client_secrets=self.root / "client.json",
                token_path=self.root / "token.json",
            )
        saved = json.loads(approval_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["reviewed_by"], "UC_AUTHENTICATED_OWNER")

    def test_approval_record_rejects_oauth_channel_mismatch(self):
        class Request:
            def execute(self, num_retries=0):
                return {"items": [{"id": "UC_OTHER"}]}
        class Channels:
            def list(self, **kwargs):
                return Request()
        class YouTube:
            def channels(self):
                return Channels()
        with patch("backend.app.youtube_upload._authorize_google", return_value=object()), \\
             patch("backend.app.youtube_upload._build_youtube_client", return_value=YouTube()):
            with self.assertRaisesRegex(PermissionError, "does not match"):
                record_upload_approval(
                    approval_record=self.root / "approval.json",
                    permission_record=self.root / "missing-permission.json",
                    clip_id="clip-001",
                    source_id="source-001",
                    expected_channel_id="UC_EXPECTED",
                    client_secrets=self.root / "client.json",
                    token_path=self.root / "token.json",
                )
        self.assertFalse((self.root / "approval.json").exists())

    def test_upload_api_is_not_called_when_owner_approval_does_not_match_oauth(self):
        os.environ["ARO_UPLOAD_APPROVAL_KEY"] = "test-only-signing-key-with-32-bytes-minimum"
        permission = self.root / "permission.json"
        permission.write_text(json.dumps({
            "source_id": "source-001", "granted_by": "creator-001",
            "scopes": ["publish"], "granted_at": "2026-11-22T00:00:00+00:00",
            "expires_at": None, "revoked_at": None,
        }), encoding="utf-8")
        approval = UploadApproval(
            clip_id="clip-001", source_id="source-001",
            status=ApprovalStatus.APPROVED, reviewed_by="UC_DIFFERENT_OWNER",
            reviewed_at=datetime.now(timezone.utc),
        )
        approval_path = save_upload_approval(self.root / "approval.json", approval)

        class Request:
            def execute(self, num_retries=0):
                return {"items": [{"id": "UC_AUTHENTICATED_OWNER"}]}
        class Channels:
            def list(self, **kwargs):
                return Request()
        class Videos:
            def __init__(self):
                self.insert_called = False
            def insert(self, **kwargs):
                self.insert_called = True
                raise AssertionError("upload request must not be constructed")
        class YouTube:
            def __init__(self):
                self.video_api = Videos()
            def channels(self):
                return Channels()
            def videos(self):
                return self.video_api
        youtube = YouTube()
        package = types.ModuleType("googleapiclient")
        package.__path__ = []
        http_module = types.ModuleType("googleapiclient.http")
        http_module.MediaFileUpload = lambda *args, **kwargs: object()
        with patch.dict(sys.modules, {
            "googleapiclient": package,
            "googleapiclient.http": http_module,
        }), patch("backend.app.youtube_upload._authorize_google", return_value=object()), \\
             patch("backend.app.youtube_upload._build_youtube_client", return_value=youtube):
            with self.assertRaisesRegex(PermissionError, "authenticated channel owner"):
                upload_video(
                    self.video, {"snippet": {}, "status": {}},
                    client_secrets=self.root / "client.json",
                    token_path=self.root / "token.json",
                    approval_record=approval_path,
                    permission_record=permission,
                    clip_id="clip-001",
                    source_id="source-001",
                    expected_channel_id="UC_AUTHENTICATED_OWNER",
                )
        self.assertFalse(youtube.video_api.insert_called)

    def test_expired_or_revoked_publish_permission_blocks_upload(self):
        os.environ["ARO_UPLOAD_APPROVAL_KEY"] = "test-only-signing-key-with-32-bytes-minimum"
        for permission_fields in (
            {"expires_at": "2026-11-22T00:00:00+00:00", "revoked_at": None},
            {"expires_at": None, "revoked_at": "2026-11-22T00:00:00+00:00"},
        ):
            permission = self.root / "permission.json"
            permission.write_text(json.dumps({
                "source_id": "source-001", "granted_by": "creator-001",
                "scopes": ["publish"], "granted_at": "2026-11-21T00:00:00+00:00",
                **permission_fields,
            }), encoding="utf-8")
            approval = UploadApproval(
                clip_id="clip-001", source_id="source-001",
                status=ApprovalStatus.APPROVED, reviewed_by="UC_AUTHENTICATED_OWNER",
                reviewed_at=datetime.now(timezone.utc),
            )
            approval_path = save_upload_approval(self.root / f"approval-{len(list(self.root.glob('approval-*.json')))}.json", approval)

            class Request:
                def execute(self, num_retries=0):
                    return {"items": [{"id": "UC_AUTHENTICATED_OWNER"}]}
            class Channels:
                def list(self, **kwargs):
                    return Request()
            class Videos:
                def __init__(self):
                    self.insert_called = False
                def insert(self, **kwargs):
                    self.insert_called = True
                    raise AssertionError("upload request must not be constructed")
            class YouTube:
                def __init__(self):
                    self.video_api = Videos()
                def channels(self):
                    return Channels()
                def videos(self):
                    return self.video_api
            youtube = YouTube()
            package = types.ModuleType("googleapiclient")
            package.__path__ = []
            http_module = types.ModuleType("googleapiclient.http")
            http_module.MediaFileUpload = lambda *args, **kwargs: object()
            with patch.dict(sys.modules, {
                "googleapiclient": package,
                "googleapiclient.http": http_module,
            }), patch("backend.app.youtube_upload._authorize_google", return_value=object()), \\
                 patch("backend.app.youtube_upload._build_youtube_client", return_value=youtube):
                with self.assertRaisesRegex(PermissionError, "active publish permission"):
                    upload_video(
                        self.video, {"snippet": {}, "status": {}},
                        client_secrets=self.root / "client.json",
                        token_path=self.root / "token.json",
                        approval_record=approval_path,
                        permission_record=permission,
                        clip_id="clip-001",
                        source_id="source-001",
                        expected_channel_id="UC_AUTHENTICATED_OWNER",
                    )
            self.assertFalse(youtube.video_api.insert_called)


if __name__ == "__main__":
    unittest.main()
