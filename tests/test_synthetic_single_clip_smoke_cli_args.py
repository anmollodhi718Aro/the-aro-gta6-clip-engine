"""CLI argument forwarding regressions for the synthetic single-clip smoke harness."""
import contextlib
import io
import json
import sys
import unittest
from unittest.mock import patch

from scripts import synthetic_single_clip_smoke as smoke


class SyntheticSingleClipSmokeCliArgumentTests(unittest.TestCase):
    def test_main_forwards_explicit_ffmpeg_and_ffprobe_overrides(self):
        expected = {
            "status": "PASS",
            "media": "synthetic test pattern and tone only",
            "upload_performed": False,
            "publishing_enabled": False,
        }
        stdout = io.StringIO()
        argv = [
            "synthetic_single_clip_smoke.py",
            "--ffmpeg", "/owner/tools/ffmpeg-custom",
            "--ffprobe", "/owner/tools/ffprobe-custom",
        ]

        with patch.object(smoke, "run_smoke_test", return_value=expected) as run_smoke, patch.object(
            sys, "argv", argv
        ), contextlib.redirect_stdout(stdout):
            exit_code = smoke.main()

        self.assertEqual(exit_code, 0)
        run_smoke.assert_called_once_with(
            ffmpeg="/owner/tools/ffmpeg-custom",
            ffprobe="/owner/tools/ffprobe-custom",
        )
        self.assertEqual(json.loads(stdout.getvalue()), expected)


if __name__ == "__main__":
    unittest.main()
