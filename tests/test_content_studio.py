"""Tests for sourced, original commentary pack generation."""
import unittest

from backend.app.content_studio import build_content_pack, render_markdown


class ContentStudioTests(unittest.TestCase):
    def payload(self):
        return {
            "working_title": "GTA 6 feature explained",
            "topic": "weather system",
            "original_angle": "Why dynamic weather changes gameplay",
            "visual_assets": [{"asset_id": "aro-weather-chart", "kind": "original", "description": "Self-made weather graphic"}],
            "research_notes": [{
                "claim": "The supplied source describes a dynamic weather feature.",
                "source_url": "https://example.com/gta6",
                "aro_commentary": "इसका gameplay पर असर समझना ज़्यादा दिलचस्प है।",
                "visual": "Use an original weather comparison graphic.",
            }],
        }

    def test_builds_script_sources_visuals_and_closed_upload_gate(self):
        pack = build_content_pack(self.payload())
        self.assertGreaterEqual(len(pack["voiceover_script"]), 3)
        self.assertEqual(pack["metadata"]["source_links"], ["https://example.com/gta6"])
        self.assertFalse(pack["review"]["approved_for_upload"])
        self.assertFalse(pack["review"]["monetization_guaranteed"])
        self.assertIn("human_fact_check_required", pack["review"])
        self.assertEqual(pack["visual_assets"][0]["asset_id"], "aro-weather-chart")

    def test_requires_explicit_visual_asset_declarations(self):
        data = self.payload()
        data["visual_assets"] = []
        with self.assertRaisesRegex(ValueError, "visual_assets"):
            build_content_pack(data)

    def test_third_party_visual_requires_source_id_and_unique_asset_id(self):
        data = self.payload()
        data["visual_assets"] = [
            {"asset_id": "external-clip", "kind": "creator_authorized"}
        ]
        with self.assertRaisesRegex(ValueError, "requires source_id"):
            build_content_pack(data)
        data["visual_assets"] = [
            {"asset_id": "duplicate", "kind": "original"},
            {"asset_id": "duplicate", "kind": "original"},
        ]
        with self.assertRaisesRegex(ValueError, "unique"):
            build_content_pack(data)

    def test_requires_sourced_research_and_original_commentary(self):
        data = self.payload()
        data["research_notes"] = [{"claim": "Unsourced claim", "aro_commentary": "My view", "source_url": "https://example.com"}]
        with self.assertRaises(ValueError):
            build_content_pack(data)
        data = self.payload()
        data["research_notes"][0]["aro_commentary"] = ""
        with self.assertRaises(ValueError):
            build_content_pack(data)

    def test_rejects_invalid_source_url(self):
        data = self.payload()
        data["research_notes"][0]["source_url"] = "not-a-url"
        with self.assertRaises(ValueError):
            build_content_pack(data)

    def test_markdown_contains_review_gate_and_sources(self):
        markdown = render_markdown(build_content_pack(self.payload()))
        self.assertIn("## Voiceover draft", markdown)
        self.assertIn("https://example.com/gta6", markdown)
        self.assertIn("Human owner approves upload", markdown)


if __name__ == "__main__":
    unittest.main()
