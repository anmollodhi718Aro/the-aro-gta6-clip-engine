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



class SecurityGuardTests(unittest.TestCase):
    def test_local_request_guard_requires_loopback_and_same_origin(self):
        self.assertTrue(studio.is_trusted_local_request(
            "127.0.0.1:8765", "http://127.0.0.1:8765", "same-origin", 8765
        ))
        self.assertTrue(studio.is_trusted_local_request(
            "localhost:8765", "", "none", 8765
        ))
        self.assertFalse(studio.is_trusted_local_request(
            "attacker.example:8765", "", "", 8765
        ))
        self.assertFalse(studio.is_trusted_local_request(
            "127.0.0.1:8765", "http://attacker.example", "cross-site", 8765
        ))
        self.assertFalse(studio.is_trusted_local_request(
            "127.0.0.1:8765", "", "cross-site", 8765
        ))

    def test_csrf_token_comparison(self):
        self.assertTrue(studio.is_valid_csrf_token("owner-token", "owner-token"))
        self.assertFalse(studio.is_valid_csrf_token("wrong-token", "owner-token"))
        self.assertFalse(studio.is_valid_csrf_token("", "owner-token"))

    def test_server_uses_ipv6_socket_for_ipv6_loopback(self):
        self.assertEqual(
            studio.server_class_for_host("::1").address_family,
            studio.socket.AF_INET6,
        )
        self.assertEqual(
            studio.server_class_for_host("127.0.0.1").address_family,
            studio.socket.AF_INET,
        )

    def test_rights_store_rejects_expiry_before_valid_from(self):
        with tempfile.TemporaryDirectory() as temp:
            store = studio.RightsStore(Path(temp) / "rights.sqlite3")
            try:
                record = LocalDataTests().valid_rights_record()
                record["expires_at"] = "2026-11-18T00:00:00+00:00"
                with self.assertRaisesRegex(ValueError, "later than valid_from"):
                    store.add(record)
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()


class LocalRequestGuardTests(unittest.TestCase):
    def test_accepts_local_same_origin_request(self):
        self.assertTrue(
            studio.is_trusted_local_request(
                "127.0.0.1:8765", "http://127.0.0.1:8765", "same-origin", 8765
            )
        )

    def test_accepts_localhost_without_fetch_metadata(self):
        self.assertTrue(
            studio.is_trusted_local_request("localhost:8765", "", "", 8765)
        )

    def test_rejects_remote_host_and_dns_rebinding_port(self):
        self.assertFalse(
            studio.is_trusted_local_request("attacker.example:8765", "", "", 8765)
        )
        self.assertFalse(
            studio.is_trusted_local_request("localhost:9999", "", "", 8765)
        )

    def test_rejects_cross_site_fetch_and_mismatched_origin(self):
        self.assertFalse(
            studio.is_trusted_local_request(
                "localhost:8765", "http://localhost:8765", "cross-site", 8765
            )
        )
        self.assertFalse(
            studio.is_trusted_local_request(
                "localhost:8765", "http://attacker.example:8765", "same-origin", 8765
            )
        )

    def test_rejects_malformed_host_header(self):
        self.assertFalse(
            studio.is_trusted_local_request("localhost:not-a-port", "", "", 8765)
        )

    def test_csrf_token_must_match(self):
        self.assertTrue(studio.is_valid_csrf_token("known-token", "known-token"))
        self.assertFalse(studio.is_valid_csrf_token("wrong-token", "known-token"))
        self.assertFalse(studio.is_valid_csrf_token("", "known-token"))

    def test_dashboard_embeds_token_in_both_post_forms(self):
        rendered = studio.page([], [], 0, csrf_token="owner-session-token")
        self.assertEqual(rendered.count('name="csrf_token"'), 2)
        self.assertEqual(rendered.count('value="owner-session-token"'), 2)


