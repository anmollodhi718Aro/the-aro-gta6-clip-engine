"""Regression tests for the synthetic smoke harness safety-report contract."""
import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import synthetic_single_clip_smoke as smoke


class SyntheticSmokeSafetyContractTests(unittest.TestCase):
    def test_renderer_report_claiming_upload_or_publishing_is_rejected(self):
        for unsafe_field in ("upload_performed", "publishing_enabled"):
            with self.subTest(unsafe_field=unsafe_field):
                captured = {}

                def fake_render(source, output, start, end, **kwargs):
                    output_path = Path(output)
                    captured["directory"] = output_path.parent
                    payload = b"synthetic rendered output"
                    output_path.write_bytes(payload)
                    return {
                        "status": "RENDERED",
                        "output_sha256": hashlib.sha256(payload).hexdigest(),
                        "upload_performed": unsafe_field == "upload_performed",
                        "publishing_enabled": unsafe_field == "publishing_enabled",
                    }

                with patch.object(smoke.shutil, "which", side_effect=lambda name: f"/tools/{name}"), patch.object(
                    smoke.subprocess, "run"
                ), patch.object(smoke, "render_selected_clip", side_effect=fake_render):
                    with self.assertRaisesRegex(
                        RuntimeError, "unexpectedly enabled upload or publishing"
                    ):
                        smoke.run_smoke_test()

                self.assertFalse(captured["directory"].exists())


if __name__ == "__main__":
    unittest.main()