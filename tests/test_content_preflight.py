"""Tests for the rights-aware visual asset preflight."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.content_preflight import preflight_content_pack
from backend.app.rights_registry import SourceRightsRegistry


class ContentPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.registry = SourceRightsRegistry(Path(self.temp.name) / "rights.sqlite3")
        self.now = datetime(2026, 11, 19, 8, tzinfo=timezone.utc)
        self.registry.register({
            "source_id": "approved-source",
            "source_url": "https://example.com/creator-video",
            "grantor": "creator",
            "evidence_ref": "permission-record-01",
            "allowed_uses": ["edit", "publish"],
            "platforms": ["youtube"],
            "attribution": "Creator credit required",
            "disclosure": "Authorized creator footage",
            "valid_from": self.now - timedelta(days=1),
            "expires_at": self.now + timedelta(days=1),
        })

    def tearDown(self):
        self.temp.cleanup()

    def test_original_assets_do_not_need_external_grant_but_still_need_review(self):
        report = preflight_content_pack(
            {"visual_assets": [{"asset_id": "chart-1", "kind": "original"}]},
            self.registry, "youtube", at=self.now,
        )
        self.assertEqual(report["status"], "ready_for_human_review")
        self.assertFalse(report["review"]["approved_for_upload"])
        self.assertEqual(
            report["assets"][0]["status"],
            "declared_original_requires_human_confirmation",
        )

    def test_authorized_asset_requires_edit_and_publish_scope(self):
        report = preflight_content_pack(
            {"visual_assets": [{
                "asset_id": "clip-1", "kind": "creator_authorized",
                "source_id": "approved-source",
            }]},
            self.registry, "youtube", at=self.now,
        )
        self.assertEqual(report["status"], "ready_for_human_review")
        self.assertEqual(report["required_attributions"], ["Creator credit required"])
        self.assertEqual(report["required_disclosures"], ["Authorized creator footage"])
        self.assertEqual(report["assets"][0]["status"], "scope_match_metadata_only")

    def test_unknown_wrong_platform_or_missing_source_is_blocked(self):
        for asset in (
            {"asset_id": "a", "kind": "licensed"},
            {"asset_id": "b", "kind": "licensed", "source_id": "missing"},
        ):
            report = preflight_content_pack(
                {"visual_assets": [asset]}, self.registry, "youtube", at=self.now,
            )
            self.assertEqual(report["status"], "blocked")
        report = preflight_content_pack(
            {"visual_assets": [{
                "asset_id": "c", "kind": "licensed", "source_id": "approved-source",
            }]},
            self.registry, "tiktok", at=self.now,
        )
        self.assertEqual(report["status"], "blocked")

    def test_expired_permission_and_invalid_asset_shapes_are_blocked(self):
        report = preflight_content_pack(
            {"visual_assets": [
                {"asset_id": "expired", "kind": "licensed", "source_id": "approved-source"},
                "not-an-object",
            ]},
            self.registry, "youtube", at=self.now + timedelta(days=2),
        )
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(len(report["errors"]), 2)

    def test_missing_visual_asset_declarations_are_blocked(self):
        report = preflight_content_pack({}, self.registry, "youtube", at=self.now)
        self.assertEqual(report["status"], "blocked")
        self.assertIn("at least one visual asset", report["errors"][0])

    def test_duplicate_asset_ids_and_unknown_kinds_are_blocked(self):
        report = preflight_content_pack(
            {"visual_assets": [
                {"asset_id": "same", "kind": "original"},
                {"asset_id": "same", "kind": "original"},
                {"asset_id": "bad", "kind": "download"},
            ]},
            self.registry, "youtube", at=self.now,
        )
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(len(report["errors"]), 2)

    def test_requires_pack_object_platform_and_asset_list(self):
        with self.assertRaises(ValueError):
            preflight_content_pack([], self.registry, "youtube", at=self.now)
        with self.assertRaises(ValueError):
            preflight_content_pack({}, self.registry, "", at=self.now)
        with self.assertRaises(ValueError):
            preflight_content_pack({"visual_assets": {}}, self.registry, "youtube", at=self.now)


if __name__ == "__main__":
    unittest.main()
