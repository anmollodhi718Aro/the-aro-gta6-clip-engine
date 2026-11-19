"""End-to-end regression coverage for the manual local clipping CLI path.

This test uses a placeholder local media file and the renderer's dry-run mode.
It does not invoke FFmpeg, download media, or publish anything.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ManualClipCliWorkflowTests(unittest.TestCase):
    def test_manual_json_to_batch_dry_run_supports_unicode_paths(self):
        with tempfile.TemporaryDirectory(prefix="THE ARO 测试 ") as folder:
            root = Path(folder)
            media = root / "authorized gameplay recording.mp4"
            media.write_bytes(b"placeholder; dry-run must not decode this file")

            source = root / "manual moments.json"
            source.write_text(
                json.dumps({
                    "source_id": "owner-recording",
                    "clips": [
                        {
                            "start_seconds": 12.25,
                            "end_seconds": 42.5,
                            "note": "manual review moment",
                        }
                    ],
                }),
                encoding="utf-8",
            )
            candidate_csv = root / "candidate clips.csv"

            prepared = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "backend.app.manual_clip",
                    str(source),
                    "--output",
                    str(candidate_csv),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            self.assertTrue(candidate_csv.is_file())

            output_root = root / "render output"
            rendered = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "backend.app.batch_render",
                    str(candidate_csv),
                    "--media",
                    str(media),
                    "--approve",
                    "1",
                    "--output-dir",
                    str(output_root),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr)

            run_dirs = [path for path in output_root.iterdir() if path.is_dir()]
            self.assertEqual(len(run_dirs), 1)
            report_path = run_dirs[0] / "batch_render_report.json"
            self.assertTrue(report_path.is_file())
            report = json.loads(report_path.read_text(encoding="utf-8"))

            self.assertEqual(len(report), 1)
            self.assertEqual(report[0]["status"], "planned")
            self.assertEqual(report[0]["source_id"], "owner-recording")
            self.assertEqual(report[0]["start_seconds"], 12.25)
            self.assertEqual(report[0]["end_seconds"], 42.5)
            self.assertEqual(report[0]["media_identity"]["path"], str(media.resolve()))
            self.assertFalse(list(output_root.rglob("*.mp4")))


if __name__ == "__main__":
    unittest.main()
