"""Regression coverage for a symlink swapped into the smoke output path at open time."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import synthetic_single_clip_smoke as smoke


class SyntheticSmokeSymlinkOpenRaceTests(unittest.TestCase):
    def test_hash_verifier_rejects_symlink_swapped_in_before_open_and_closes_fd(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "output.mp4"
            target = root / "external-target.mp4"
            target_bytes = b"external target must remain unchanged"
            output.write_bytes(b"initial regular output")
            target.write_bytes(target_bytes)

            real_open = smoke.os.open
            observed: dict[str, int] = {}

            def swap_to_symlink_then_open(path, flags, *args, **kwargs):
                output.unlink()
                try:
                    output.symlink_to(target)
                except (OSError, NotImplementedError) as exc:
                    raise unittest.SkipTest(f"symlink creation unavailable: {exc}")
                descriptor = real_open(path, flags, *args, **kwargs)
                observed["descriptor"] = descriptor
                return descriptor

            # Exercise the portable identity comparison rather than relying on
            # O_NOFOLLOW to reject the replacement before a descriptor exists.
            with patch.object(smoke.os, "O_NOFOLLOW", 0, create=True), patch.object(
                smoke.os, "open", side_effect=swap_to_symlink_then_open
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "changed while opening it for verification"
                ):
                    smoke._hash_verified_output(output)

            self.assertIn("descriptor", observed)
            with self.assertRaises(OSError):
                smoke.os.fstat(observed["descriptor"])
            self.assertTrue(output.is_symlink())
            self.assertEqual(target.read_bytes(), target_bytes)


if __name__ == "__main__":
    unittest.main()
