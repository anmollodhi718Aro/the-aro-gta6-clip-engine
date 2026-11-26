"""Resolved executable consistency regressions for the synthetic smoke harness."""
import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import synthetic_single_clip_smoke as smoke


class SyntheticSingleClipSmokeToolResolutionTests(unittest.TestCase):
    def test_resolved_tool_paths_are_shared_by_fixture_generation_and_renderer(self):
        requested_ffmpeg = "/owner/tools/ffmpeg-custom"
        requested_ffprobe = "/owner/tools/ffprobe-custom"
        resolved_ffmpeg = "/resolved/tools/ffmpeg-custom"
        resolved_ffprobe = "/resolved/tools/ffprobe-custom"
        captured = {}
        output_bytes = b"synthetic-rendered-output"

        def locate_tool(name):
            return {
                requested_ffmpeg: resolved_ffmpeg,
                requested_ffprobe: resolved_ffprobe,
            }.get(name)

        def generate_fixture(command, **kwargs):
            captured["generation_command"] = command
            Path(command[-1]).write_bytes(b"synthetic-source")
            return None

        def render(source, output, start, end, **kwargs):
            captured["render_kwargs"] = kwargs
            Path(output).write_bytes(output_bytes)
            return {
                "status": "RENDERED",
                "output_sha256": hashlib.sha256(output_bytes).hexdigest(),
                "upload_performed": False,
                "publishing_enabled": False,
            }

        with patch.object(smoke.shutil, "which", side_effect=locate_tool) as which, patch.object(
            smoke.subprocess, "run", side_effect=generate_fixture
        ) as generate, patch.object(smoke, "render_selected_clip", side_effect=render):
            result = smoke.run_smoke_test(
                ffmpeg=requested_ffmpeg,
                ffprobe=requested_ffprobe,
            )

        self.assertEqual(which.call_args_list, [
            unittest.mock.call(requested_ffmpeg),
            unittest.mock.call(requested_ffprobe),
        ])
        generate.assert_called_once()
        self.assertEqual(captured["generation_command"][0], resolved_ffmpeg)
        self.assertEqual(captured["render_kwargs"]["ffmpeg_binary"], resolved_ffmpeg)
        self.assertEqual(captured["render_kwargs"]["ffprobe_binary"], resolved_ffprobe)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["output_sha256"], hashlib.sha256(output_bytes).hexdigest())
        self.assertFalse(result["upload_performed"])
        self.assertFalse(result["publishing_enabled"])
        self.assertFalse(result["artifacts_retained"])


if __name__ == "__main__":
    unittest.main()
