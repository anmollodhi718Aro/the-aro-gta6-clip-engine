"""Race regression tests for source/output identity during smoke verification."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import synthetic_single_clip_smoke as smoke


class SyntheticSmokeSourceIdentityRaceTests(unittest.TestCase):
    def test_hash_verifier_rejects_output_swapped_to_source_hardlink_before_open(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.mp4"
            output = root / "output.mp4"
            source.write_bytes(b"authorized synthetic fixture")
            output.write_bytes(b"independent rendered bytes")
            real_open = smoke.os.open
            swapped = {"done": False}

            def swap_to_source_hardlink(path, flags, *args, **kwargs):
                if Path(path) == output and not swapped["done"]:
                    output.unlink()
                    try:
                        output.hardlink_to(source)
                    except (OSError, NotImplementedError) as exc:
                        self.skipTest(f"hard-link creation unavailable: {exc}")
                    swapped["done"] = True
                return real_open(path, flags, *args, **kwargs)

            with patch.object(smoke.os, "open", side_effect=swap_to_source_hardlink):
                with self.assertRaisesRegex(RuntimeError, "must not alias its source"):
                    smoke._hash_verified_output(output, distinct_from=source)

            self.assertTrue(swapped["done"])
            self.assertEqual(output.stat().st_ino, source.stat().st_ino)
            self.assertEqual(source.read_bytes(), b"authorized synthetic fixture")


if __name__ == "__main__":
    unittest.main()
