"""Regression coverage for output-path replacement after descriptor open."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import synthetic_single_clip_smoke as smoke


class SyntheticSmokeSymlinkAfterOpenTests(unittest.TestCase):
    def test_hash_verifier_rejects_path_replaced_after_open_and_closes_fd(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "output.mp4"
            target = root / "external-target.mp4"
            target_bytes = b"external target must remain unchanged"
            output.write_bytes(b"initial regular output")
            target.write_bytes(target_bytes)

            real_open = smoke.os.open
            real_read = smoke.os.read
            observed: dict[str, int] = {}
            replaced = False

            def capture_open(path, flags, *args, **kwargs):
                descriptor = real_open(path, flags, *args, **kwargs)
                observed["descriptor"] = descriptor
                return descriptor

            def replace_path_then_read(descriptor, size):
                nonlocal replaced
                if not replaced:
                    replaced = True
                    output.unlink()
                    try:
                        output.symlink_to(target)
                    except (OSError, NotImplementedError) as exc:
                        raise unittest.SkipTest(f"symlink creation unavailable: {exc}")
                return real_read(descriptor, size)

            # Force the portable post-read path/descriptor identity check.
            # The open descriptor still refers to the original regular file,
            # while the pathname is changed to an external symlink mid-hash.
            with patch.object(smoke.os, "O_NOFOLLOW", 0, create=True), patch.object(
                smoke.os, "open", side_effect=capture_open
            ), patch.object(smoke.os, "read", side_effect=replace_path_then_read):
                with self.assertRaisesRegex(
                    RuntimeError, "changed during SHA-256 verification"
                ):
                    smoke._hash_verified_output(output)

            self.assertTrue(replaced)
            self.assertIn("descriptor", observed)
            with self.assertRaises(OSError):
                smoke.os.fstat(observed["descriptor"])
            self.assertTrue(output.is_symlink())
            self.assertEqual(target.read_bytes(), target_bytes)


if __name__ == "__main__":
    unittest.main()
