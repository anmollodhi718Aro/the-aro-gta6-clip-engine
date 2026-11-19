"""Tests for local media probing and batch rendering orchestration."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from backend.app.media_probe import probe_media
from backend.app.batch_render import render_manifest

class MediaProbeTests(unittest.TestCase):
    def test_probe_parses_duration_and_format(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.mp4"
            source.write_bytes(b"sample")
            with patch("backend.app.media_probe.subprocess.run") as run:
                run.return_value.stdout = '{"format":{"duration":"42.5","format_name":"mov,mp4"}}'
                info = probe_media(source)
            self.assertEqual(info.duration_seconds, 42.5)
            self.assertEqual(info.format_name, "mov,mp4")
            self.assertNotIn("shell", run.call_args.kwargs)

    def test_probe_rejects_invalid_duration(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.mp4"
            source.write_bytes(b"sample")
            with patch("backend.app.media_probe.subprocess.run") as run:
                run.return_value.stdout = '{"format":{"duration":"nan"}}'
                with self.assertRaisesRegex(ValueError, "finite and positive"):
                    probe_media(source)

class BatchRenderTests(unittest.TestCase):
    def test_requires_rights_confirmation(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = Path(folder) / "manifest.json"
            manifest.write_text("{}")
            with self.assertRaises(PermissionError):
                render_manifest(manifest, Path(folder) / "out", rights_confirmed=False)

    def test_probes_media_and_renders_each_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            media = root / "authorized.mp4"
            media.write_bytes(b"sample")
            start = "2026-11-19T10:00:00+00:00"
            stamp = "2026-11-19T10:02:00+00:00"
            candidate = {"source_id":"creator-stream", "peak_window_start":stamp,
                "clip_start":"2026-11-19T10:01:45+00:00",
                "clip_end":"2026-11-19T10:02:15+00:00",
                "peak_message_count":10, "baseline_average":2, "score":90}
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"media_path":str(media), "media_start_utc":start,
                "clock_sync":{"chat_minus_media_seconds":0,"uncertainty_seconds":0.1,
                    "measured_at":start,"method":"test slate"},
                "candidates":[candidate,candidate]}))
            with patch("backend.app.batch_render.probe_media") as probe, \
                 patch("backend.app.batch_render.render_candidate") as render:
                probe.return_value.path = media
                probe.return_value.duration_seconds = 300
                probe.return_value.format_name = "mp4"
                render.side_effect = [Path("clip1.mp4"), Path("clip2.mp4")]
                report = render_manifest(manifest, root / "out", rights_confirmed=True)
            self.assertEqual(report["rendered_count"], 2)
            self.assertEqual(render.call_count, 2)
            self.assertFalse(report["publishing_enabled"])
            self.assertTrue((root / "out" / "review_manifest.json").is_file())

if __name__ == "__main__":
    unittest.main()
