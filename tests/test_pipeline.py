"""Tests for the one-command offline pipeline orchestration."""
import csv
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def write_inputs(self, root: Path, source_id: str = "synthetic-stream") -> tuple[Path, Path]:
        origin = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
        events = []
        for bucket in range(4):
            count = 9 if bucket == 3 else 2
            for item in range(count):
                second = bucket * 10 + item
                events.append({
                    "event_id": f"{bucket}-{item}",
                    "source_id": source_id,
                    "timestamp": (origin + timedelta(seconds=second)).isoformat(),
                    "text": "synthetic event",
                })
        event_path = root / "events.json"
        event_path.write_text(json.dumps({
            "permission": {
                "source_id": source_id,
                "granted_by": "test-fixture",
                "scopes": ["analyze_chat"],
                "granted_at": (origin - timedelta(minutes=1)).isoformat(),
                "expires_at": (origin + timedelta(hours=1)).isoformat(),
            },
            "events": events,
        }), encoding="utf-8")
        anchors_path = root / "anchors.json"
        anchors_path.write_text(json.dumps({"anchors": [
            {
                "source_id": source_id,
                "chat_time": (origin + timedelta(seconds=offset)).isoformat(),
                "media_seconds": offset + 5,
            }
            for offset in (0, 60, 120)
        ]}), encoding="utf-8")
        return event_path, anchors_path

    def test_creates_complete_review_pack_without_rendering_or_uploading(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events, anchors = self.write_inputs(root)
            output = root / "new-run"
            summary = run_pipeline(events, anchors, output)
            self.assertEqual(summary["candidate_count"], 1)
            self.assertEqual(summary["renderable_count"], 1)
            self.assertFalse(summary["rendering_performed"])
            self.assertFalse(summary["upload_performed"])
            self.assertTrue((output / "clip_plan.json").is_file())
            self.assertTrue((output / "clip_pack" / "clip_candidates.md").is_file())
            self.assertTrue((output / "quality_scored_candidates.csv").is_file())
            with (output / "quality_scored_candidates.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["start_seconds"], "20.0")
            saved_summary = json.loads((output / "pipeline_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(saved_summary["review_csv"], "quality_scored_candidates.csv")
            self.assertFalse(saved_summary["publishing_enabled"])

    def test_never_overwrites_existing_output_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events, anchors = self.write_inputs(root)
            output = root / "existing"
            output.mkdir()
            sentinel = output / "owner.txt"
            sentinel.write_text("keep me", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                run_pipeline(events, anchors, output)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep me")

    def test_source_mismatch_cleans_only_new_partial_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events, anchors = self.write_inputs(root, source_id="chat-source")
            payload = json.loads(anchors.read_text(encoding="utf-8"))
            for anchor in payload["anchors"]:
                anchor["source_id"] = "different-source"
            anchors.write_text(json.dumps(payload), encoding="utf-8")
            output = root / "failed-run"
            with self.assertRaisesRegex(ValueError, "does not match"):
                run_pipeline(events, anchors, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
