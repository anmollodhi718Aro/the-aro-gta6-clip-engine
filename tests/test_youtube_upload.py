"""Tests for gated YouTube upload without making network requests."""
import json
import tempfile
import unittest
from pathlib import Path

from backend.app.youtube_upload import build_upload_body, load_rights_report, validate_upload


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
            "review": {"approved_for_upload": False, "monetization_guaranteed": False},
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

    def test_upload_gate_arguments_must_be_real_booleans(self):
        invalid_flags = (
            ("made_for_kids", {"made_for_kids": "false"}),
            ("owner_approved", {"owner_approved": "false"}),
            ("rights_confirmed", {"rights_confirmed": "false"}),
            ("upload_requested", {"upload_requested": "false"}),
        )
        for name, override in invalid_flags:
            with self.subTest(flag=name):
                kwargs = {
                    "made_for_kids": False,
                    "owner_approved": True,
                    "rights_confirmed": True,
                    "upload_requested": True,
                }
                kwargs.update(override)
                with self.assertRaisesRegex(TypeError, name):
                    validate_upload(
                        self.video, self.report, title="Short", **kwargs,
                    )

    def test_metadata_builder_rejects_non_boolean_made_for_kids(self):
        for value in ("false", 0, 1, None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(TypeError, "made_for_kids"):
                    build_upload_body(
                        title="Short", description="", tags=[],
                        privacy="private", made_for_kids=value,
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
