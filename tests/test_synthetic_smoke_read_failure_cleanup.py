"""Regression coverage for descriptor cleanup when output hashing fails."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import synthetic_single_clip_smoke as smoke


class SyntheticSmokeReadFailureCleanupTests(unittest.TestCase):
    def test_hash_verifier_closes_descriptor_when_read_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.mp4"
            output.write_bytes(b"synthetic output remains unchanged")
            original_bytes = output.read_bytes()

            real_open = smoke.os.open
            observed: dict[str, int] = {}

            def capture_open(path, flags, *args, **kwargs):
                descriptor = real_open(path, flags, *args, **kwargs)
                observed["descriptor"] = descriptor
                return descriptor

            def fail_read(descriptor, size):
                raise OSError("injected read failure")

            with patch.object(smoke.os, "open", side_effect=capture_open), patch.object(
                smoke.os, "read", side_effect=fail_read
            ):
                with self.assertRaisesRegex(OSError, "injected read failure"):
                    smoke._hash_verified_output(output)

            self.assertIn("descriptor", observed)
            with self.assertRaises(OSError):
                smoke.os.fstat(observed["descriptor"])
            self.assertEqual(output.read_bytes(), original_bytes)


if __name__ == "__main__":
    unittest.main()
