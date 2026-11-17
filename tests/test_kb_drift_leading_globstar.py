"""Audit defect #1861: a `**/x` .gitignore rule matches x at any depth,
the top level included."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import kb_drift  # noqa: E402


class TestLeadingGlobstar(unittest.TestCase):
    def test_matches_top_level_and_nested(self):
        rules = kb_drift._ignore_rules("**/dist\n")
        self.assertTrue(kb_drift.gitignored(rules, "dist/app.js"))
        self.assertTrue(kb_drift.gitignored(rules, "a/dist/app.js"))
        self.assertFalse(kb_drift.gitignored(rules, "a/src/app.js"))

    def test_multi_segment_remainder(self):
        rules = kb_drift._ignore_rules("**/build/out\n")
        self.assertTrue(kb_drift.gitignored(rules, "build/out/x"))
        self.assertTrue(kb_drift.gitignored(rules, "p/build/out/x"))
        self.assertFalse(kb_drift.gitignored(rules, "build/in/x"))


if __name__ == "__main__":
    unittest.main()
