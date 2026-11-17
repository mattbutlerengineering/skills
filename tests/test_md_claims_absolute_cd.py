"""Audit defect #1857: a documented `cd /absolute/path` leaves the repo,
so the claim after it is skipped like any unplaceable cd, not a crash."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import md_claims  # noqa: E402


class TestAbsoluteCd(unittest.TestCase):
    def test_cd_outside_the_repo_skips_the_claim(self):
        for command in ("npm run build", "make build", "node run.js"):
            with self.subTest(command=command):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    (root / "README.md").write_text(
                        f"```sh\ncd /opt/app && {command}\n```\n")
                    self.assertEqual(md_claims.check(root), [])


if __name__ == "__main__":
    unittest.main()
