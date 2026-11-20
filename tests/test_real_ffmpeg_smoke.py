"""Real FFmpeg/FFprobe smoke coverage using a generated, non-copyrighted fixture.

This proves the local renderer can create and decode a real MP4. It is synthetic
media verification only, not authorization or verification of GTA 6 footage.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from backend.app.clipping import render_clip
from backend.app.render_validation import verify_rendered_media


class RealFfmpegRenderSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ffmpeg = shutil.which("ffmpeg")
        cls.ffprobe = shutil.which("ffprobe")
        if not cls.ffmpeg or not cls.ffprobe:
            raise unittest.SkipTest("FFmpeg and FFprobe are required for the real-media smoke test")

    def test_generated_fixture_renders_valid_vertical_mp4_and_decodes(self):
        with tempfile.TemporaryDirectory(prefix="aro-ffmpeg-smoke-") as directory:
            root = Path(directory)
            source = root / "synthetic-source.mp4"
            output = root / "rendered-vertical.mp4"

            subprocess.run(
                [
                    self.ffmpeg,
                    "-hide_banner",
                    "-loglevel", "error",
                    "-y",
                    "-f", "lavfi",
                    "-i", "testsrc2=size=320x240:rate=24",
                    "-f", "lavfi",
                    "-i", "sine=frequency=440:sample_rate=48000",
                    "-t", "4",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-shortest",
                    str(source),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )

            rendered = render_clip(
                source,
                output,
                0.5,
                2.5,
                rights_confirmed=True,
                ffmpeg_binary=self.ffmpeg,
                ffprobe_binary=self.ffprobe,
                vertical=True,
            )

            self.assertEqual(rendered, output.resolve())
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)

            info = verify_rendered_media(
                output,
                expected_duration_seconds=2.0,
                vertical=True,
                ffprobe_binary=self.ffprobe,
            )
            self.assertEqual((info.width, info.height), (1080, 1920))
            self.assertGreater(info.duration_seconds, 0)
            self.assertTrue(info.has_audio)

            # Decode the complete output, not just its container metadata.
            subprocess.run(
                [
                    self.ffmpeg,
                    "-hide_banner",
                    "-v", "error",
                    "-i", str(output),
                    "-f", "null",
                    "-",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )


if __name__ == "__main__":
    unittest.main()
