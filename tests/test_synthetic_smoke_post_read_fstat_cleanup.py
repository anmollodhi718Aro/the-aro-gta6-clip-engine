"""Regression coverage for descriptor cleanup when post-read fstat fails."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import synthetic_single_clip_smoke as smoke


class SyntheticSmokePostReadFstatCleanupTests(unittest.TestCase):
    def test_hash_verifier_closes_descriptor_when_post_read_fstat_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.mp4"
            original_bytes = b"synthetic output remains unchanged"
            output.write_bytes(original_bytes)

            real_open = smoke.os.open
            real_fstat = smoke.os.fstat
            observed: dict[str, int] = {}
            fstat_calls = {"count": 0}

            def capture_open(path, flags, *args, **kwargs):
                descriptor = real_open(path, flags, *args, **kwargs)
                observed["descriptor"] = descriptor
                return descriptor

            def fail_post_read_fstat(descriptor):
                fstat_calls["count"] += 1
                if fstat_calls["count"] == 2:
                    raise OSError("injected post-read fstat failure")
                return real_fstat(descriptor)

            with patch.object(smoke.os, "open", side_effect=capture_open), patch.object(
                smoke.os, "fstat", side_effect=fail_post_read_fstat
            ):
                with self.assertRaisesRegex(OSError, "injected post-read fstat failure"):
                    smoke._hash_verified_output(output)

            self.assertEqual(fstat_calls["count"], 2)
            self.assertIn("descriptor", observed)
            with self.assertRaises(OSError):
                real_fstat(observed["descriptor"])
            self.assertEqual(output.read_bytes(), original_bytes)


if __name__ == "__main__":
    unittest.main()
