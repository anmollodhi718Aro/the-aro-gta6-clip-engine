"""End-to-end synthetic smoke test for the local clip preparation workflow."""
import contextlib
import csv
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from backend.app.batch_render import run_batch
from backend.app.candidate_quality import score_rows
from backend.app.cli import analyze_file
from backend.app.clock_sync import ClockAnchor, fit_clock_sync
from backend.app.clip_pack import map_candidates_to_media, write_clip_pack
from backend.app.detection import DetectorConfig


class EndToEndPipelineSmokeTests(unittest.TestCase):
    def test_synthetic_chat_to_scored_review_and_batch_dry_run(self):
        origin = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events = []
            for bucket in range(4):
                count = 9 if bucket == 3 else 2
                for item in range(count):
                    seconds = bucket * 10 + item
                    events.append({
                        "event_id": f"{bucket}-{item}",
                        "source_id": "synthetic-stream",
                        "timestamp": (origin + timedelta(seconds=seconds)).isoformat(),
                        "text": "synthetic test event",
                    })
            source = root / "events.json"
            source.write_text(json.dumps({
                "permission": {
                    "source_id": "synthetic-stream",
                    "granted_by": "automated-test-fixture",
                    "scopes": ["analyze_chat"],
                    "granted_at": (origin - timedelta(minutes=1)).isoformat(),
                    "expires_at": (origin + timedelta(hours=1)).isoformat(),
                },
                "events": events,
            }), encoding="utf-8")

            plan_path = root / "clip_plan.json"
            with contextlib.redirect_stdout(io.StringIO()):
                status = analyze_file(source, plan_path, DetectorConfig())
            self.assertEqual(status, 0)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(plan["candidate_count"], 1)
            self.assertFalse(plan["publishing_enabled"])

            anchors = [
                ClockAnchor("synthetic-stream", origin + timedelta(seconds=offset), offset + 5)
                for offset in (0, 60, 120)
            ]
            sync = fit_clock_sync(anchors)
            mapped = map_candidates_to_media(
                plan["candidates"], clock_sync=sync, source_id=plan["source_id"],
            )
            self.assertEqual(mapped[0]["start_seconds"], 20.0)
            self.assertEqual(mapped[0]["end_seconds"], 60.0)
            self.assertTrue(mapped[0]["renderable"])

            pack_dir = root / "clip_pack"
            csv_path, markdown_path = write_clip_pack(mapped, pack_dir)
            self.assertTrue(markdown_path.is_file())
            with csv_path.open(encoding="utf-8", newline="") as handle:
                packed_rows = list(csv.DictReader(handle))
            scored = score_rows(packed_rows)
            self.assertEqual(len(scored), 1)
            self.assertGreaterEqual(scored[0]["quality_score"], 0)
            self.assertLessEqual(scored[0]["quality_score"], 100)

            scored_csv = root / "scored_candidates.csv"
            with scored_csv.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(scored[0]))
                writer.writeheader()
                for row in scored:
                    saved = dict(row)
                    saved["quality_reasons"] = " | ".join(saved["quality_reasons"])
                    writer.writerow(saved)

            media = root / "synthetic-authorized-placeholder.mp4"
            media.write_bytes(b"not real media; dry-run only")
            with patch("backend.app.batch_render.render_clip") as renderer:
                report = run_batch(scored_csv, media, root / "renders", {1})
            renderer.assert_not_called()
            self.assertEqual(report[0]["status"], "planned")
            self.assertEqual(report[0]["start_seconds"], 20.0)
            self.assertFalse((root / "renders").exists())


if __name__ == "__main__":
    unittest.main()
