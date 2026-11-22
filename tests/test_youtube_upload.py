"""Tests for fail-closed authenticated YouTube upload approval without network calls."""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from backend.app.approval import ApprovalStatus, UploadApproval
from backend.app.youtube_upload import (
    authenticated_channel_identity,
    build_upload_body,
    load_rights_report,
    load_upload_approval,
    save_upload_approval,
    upload_video,
    validate_upload,
)


NOW = datetime(2026, 11, 22, 12, tzinfo=timezone.utc)


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
        self.approval_path = self.root / "approval.json"
        self.permission_path = self.root / "permission.json"
        self.permission_path.write_text(json.dumps({
            "source_id": "source-1",
            "granted_by": "creator-consent",
            "scopes": ["publish"],
            "granted_at": "2026-11-01T00:00:00+00:00",
            "expires_at": None,
            "revoked_at": None,
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def _youtube(self, channel_id="channel-owner-1", video_id="video-1"):
        youtube = Mock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": channel_id}]
        }
        youtube.videos.return_value.insert.return_value.execute.return_value = {"id": video_id}
        return youtube

    def _approved_record(self, reviewer="channel-owner-1"):
        save_upload_approval(
            self.approval_path, clip_id="clip-1", source_id="source-1",
            approved=True, authenticated_owner_identity=reviewer, at=NOW,
        )

    def test_dry_run_validates_without_approval_or_upload_flags(self):
        video, body = validate_upload(
            self.video, self.report, title="THE ARO GTA 6 Short",
            tags=["GTA6", "THEARO"], made_for_kids=False,
        )
        self.assertEqual(video, self.video)
        self.assertEqual(body["status"]["privacyStatus"], "private")
        self.assertFalse(body["status"]["selfDeclaredMadeForKids"])

    def test_actual_upload_requires_additional_acknowledgements(self):
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

    def test_boolean_flags_alone_do_not_authorize_upload(self):
        youtube = self._youtube()
        with self.assertRaises(FileNotFoundError):
            upload_video(
                self.video, {}, client_secrets=self.root / "missing.json",
                token_path=self.root / "token.json", approval_path=self.approval_path,
                permission_path=self.permission_path, clip_id="clip-1", source_id="source-1",
                youtube_client=youtube, at=NOW,
            )
        youtube.videos.return_value.insert.assert_not_called()

    def test_authenticated_owner_approval_and_permission_allow_mocked_upload(self):
        self._approved_record()
        youtube = self._youtube()
        result = upload_video(
            self.video, {"status": {"privacyStatus": "private"}},
            client_secrets=self.root / "unused.json", token_path=self.root / "unused-token.json",
            approval_path=self.approval_path, permission_path=self.permission_path,
            clip_id="clip-1", source_id="source-1", youtube_client=youtube, at=NOW,
        )
        self.assertEqual(result["video_id"], "video-1")
        youtube.channels.return_value.list.assert_called_once_with(part="id", mine=True)
        youtube.videos.return_value.insert.assert_called_once()

    def test_approval_by_different_authenticated_account_fails_closed(self):
        self._approved_record(reviewer="some-other-channel")
        youtube = self._youtube(channel_id="channel-owner-1")
        with self.assertRaisesRegex(PermissionError, "authenticated channel owner"):
            upload_video(
                self.video, {}, client_secrets=self.root / "unused.json",
                token_path=self.root / "unused-token.json", approval_path=self.approval_path,
                permission_path=self.permission_path, clip_id="clip-1", source_id="source-1",
                youtube_client=youtube, at=NOW,
            )
        youtube.videos.return_value.insert.assert_not_called()

    def test_pending_or_rejected_approval_cannot_upload(self):
        for approved in (False,):
            with self.subTest(approved=approved):
                save_upload_approval(
                    self.approval_path, clip_id="clip-1", source_id="source-1",
                    approved=approved, authenticated_owner_identity="channel-owner-1", at=NOW,
                )
                youtube = self._youtube()
                with self.assertRaisesRegex(PermissionError, "owner approval"):
                    upload_video(
                        self.video, {}, client_secrets=self.root / "unused.json",
                        token_path=self.root / "unused-token.json", approval_path=self.approval_path,
                        permission_path=self.permission_path, clip_id="clip-1", source_id="source-1",
                        youtube_client=youtube, at=NOW,
                    )
                youtube.videos.return_value.insert.assert_not_called()
                self.approval_path.unlink()

    def test_wrong_clip_or_source_cannot_reuse_approval(self):
        self._approved_record()
        youtube = self._youtube()
        with self.assertRaisesRegex(PermissionError, "does not match"):
            upload_video(
                self.video, {}, client_secrets=self.root / "unused.json",
                token_path=self.root / "unused-token.json", approval_path=self.approval_path,
                permission_path=self.permission_path, clip_id="clip-other", source_id="source-1",
                youtube_client=youtube, at=NOW,
            )
        youtube.videos.return_value.insert.assert_not_called()

    def test_missing_expired_or_revoked_publish_permission_fails_closed(self):
        self._approved_record()
        for patch in (
            {"scopes": ["read_live_stream"]},
            {"expires_at": "2026-11-22T11:00:00+00:00"},
            {"revoked_at": "2026-11-22T11:00:00+00:00"},
        ):
            permission = {
                "source_id": "source-1", "granted_by": "creator-consent",
                "scopes": ["publish"], "granted_at": "2026-11-01T00:00:00+00:00",
                "expires_at": None, "revoked_at": None,
            }
            permission.update(patch)
            self.permission_path.write_text(json.dumps(permission), encoding="utf-8")
            youtube = self._youtube()
            with self.assertRaises(PermissionError):
                upload_video(
                    self.video, {}, client_secrets=self.root / "unused.json",
                    token_path=self.root / "unused-token.json", approval_path=self.approval_path,
                    permission_path=self.permission_path, clip_id="clip-1", source_id="source-1",
                    youtube_client=youtube, at=NOW,
                )
            youtube.videos.return_value.insert.assert_not_called()

    def test_missing_or_ambiguous_authenticated_channel_fails_closed(self):
        youtube = self._youtube()
        youtube.channels.return_value.list.return_value.execute.return_value = {"items": []}
        with self.assertRaisesRegex(PermissionError, "exactly one"):
            authenticated_channel_identity(youtube)
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "one"}, {"id": "two"}]
        }
        with self.assertRaisesRegex(PermissionError, "exactly one"):
            authenticated_channel_identity(youtube)

    def test_approval_record_is_immutable_and_durable(self):
        self._approved_record()
        loaded = load_upload_approval(self.approval_path)
        self.assertEqual(loaded.clip_id, "clip-1")
        self.assertEqual(loaded.status, ApprovalStatus.APPROVED)
        self.assertEqual(loaded.reviewed_by, "channel-owner-1")
        with self.assertRaises(FileExistsError):
            save_upload_approval(
                self.approval_path, clip_id="clip-1", source_id="source-1",
                approved=False, authenticated_owner_identity="channel-owner-1", at=NOW,
            )

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


if __name__ == "__main__":
    unittest.main()
