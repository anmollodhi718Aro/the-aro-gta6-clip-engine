"""Regression tests for the single-file local THE ARO Studio dashboard."""
import json
import tempfile
import unittest
from pathlib import Path

import THE_ARO_STUDIO as studio


class ContentPackTests(unittest.TestCase):
    def valid_payload(self):
        return {
            "working_title": "GTA 6: Test topic",
            "topic": "test topic",
            "original_angle": "A clearly original analysis angle",
            "research_notes": [
                {
                    "claim": "A sourced factual claim that still needs fact-checking.",
                    "source_url": "https://example.com/source",
                    "aro_commentary": "An original explanation written by the channel.",
                    "visual": "Use an original graphic.",
                }
            ],
        }

    def test_builds_draft_without_upload_approval(self):
        pack = studio.build_content_pack(self.valid_payload())
        self.assertEqual(pack["working_title"], "GTA 6: Test topic")
        self.assertEqual(len(pack["research_beats"]), 1)
        self.assertEqual(pack["metadata"]["source_links"], ["https://example.com/source"])
        self.assertFalse(pack["review"]["approved_for_upload"])
        self.assertTrue(pack["review"]["human_fact_check_required"])
        self.assertTrue(pack["review"]["rights_review_required_for_each_visual"])

    def test_rejects_missing_research_notes(self):
        payload = self.valid_payload()
        payload["research_notes"] = []
        with self.assertRaisesRegex(ValueError, "research_notes"):
            studio.build_content_pack(payload)

    def test_rejects_unsourced_or_non_original_research_beats(self):
        payload = self.valid_payload()
        payload["research_notes"][0]["source_url"] = "javascript:alert(1)"
        with self.assertRaisesRegex(ValueError, "research note 1"):
            studio.build_content_pack(payload)

        payload = self.valid_payload()
        payload["research_notes"][0]["aro_commentary"] = "   "
        with self.assertRaisesRegex(ValueError, "research note 1"):
            studio.build_content_pack(payload)

    def test_markdown_contains_review_gate_and_source(self):
        pack = studio.build_content_pack(self.valid_payload())
        markdown = studio.pack_markdown(pack)
        self.assertIn("https://example.com/source", markdown)
        self.assertIn("Confirm rights for every visual and audio asset.", markdown)
        self.assertIn("Human owner explicitly approves any upload.", markdown)
        self.assertIn("Draft only.", markdown)


class LocalDataTests(unittest.TestCase):
    def valid_rights_record(self):
        return {
            "source_id": "creator-source-1",
            "source_url": "https://example.com/authorized-source",
            "grantor": "Creator",
            "evidence_ref": "owner-reviewed-reference",
            "allowed_uses": ["analyze", "edit"],
            "platforms": ["youtube"],
            "valid_from": "2026-11-19T00:00:00+00:00",
            "expires_at": None,
            "attribution": "Credit the creator",
            "disclosure": "Authorized collaboration",
        }

    def test_rights_store_persists_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            store = studio.RightsStore(Path(temp) / "rights.sqlite3")
            try:
                store.add(self.valid_rights_record())
                self.assertEqual(store.count(), 1)
            finally:
                store.close()

    def test_rights_store_rejects_invalid_url_and_missing_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            store = studio.RightsStore(Path(temp) / "rights.sqlite3")
            try:
                invalid_url = self.valid_rights_record()
                invalid_url["source_url"] = "file:///private/video.mp4"
                with self.assertRaisesRegex(ValueError, "http"):
                    store.add(invalid_url)

                missing = self.valid_rights_record()
                missing["evidence_ref"] = ""
                with self.assertRaises(ValueError):
                    store.add(missing)
            finally:
                store.close()

    def test_rights_store_rejects_naive_timestamps(self):
        with tempfile.TemporaryDirectory() as temp:
            store = studio.RightsStore(Path(temp) / "rights.sqlite3")
            try:
                record = self.valid_rights_record()
                record["valid_from"] = "2026-11-19T00:00:00"
                with self.assertRaisesRegex(ValueError, "timezone"):
                    store.add(record)
            finally:
                store.close()

    def test_load_reports_filters_rows_and_reports_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "batch.json").write_text(
                json.dumps([
                    {"status": "rendered", "source_id": "one"},
                    {"status": "unknown", "source_id": "two"},
                    "not-a-row",
                ]),
                encoding="utf-8",
            )
            (root / "broken.json").write_text("{not-json", encoding="utf-8")

            rows, errors = studio.load_reports(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["source_id"], "one")
            self.assertEqual(rows[0]["candidate_row"], 1)
            self.assertEqual(len(errors), 1)

    def test_dashboard_escapes_untrusted_report_values(self):
        rows = [{
            "candidate_row": 1,
            "source_id": "<script>alert(1)</script>",
            "status": "rendered",
        }]
        rendered = studio.page(rows, [], rights_count=0)
        self.assertNotIn("<script>alert(1)</script>", rendered)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", rendered)


if __name__ == "__main__":
    unittest.main()
