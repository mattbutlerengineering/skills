"""Audit defect #1852: nested-map frontmatter values must not crash string-only readers."""
import tempfile
import unittest
from pathlib import Path

import protocol


class TestNestedMapFrontmatter(unittest.TestCase):
    def test_nested_users_observed_leaves_operate_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "docs" / "features" / "x"
            run.mkdir(parents=True)
            (run / "retro.md").write_text(
                "---\nusers-observed:\n  web: 3\n  cli: 0\n"
                "signal-source: analytics\n---\n")
            self.assertFalse(protocol._retro_populated(run))

    def test_nested_description_is_a_problem_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = protocol.skill_path(root, "demo")
            path.parent.mkdir(parents=True)
            path.write_text("---\nname: demo\ndescription:\n"
                            "  Use when the user says: plan this\n---\n")
            self.assertEqual(
                protocol.skill_frontmatter_problems(root, "demo"),
                ["skills/demo/SKILL.md description is not a bare YAML "
                 "scalar: it is a nested map"])

if __name__ == "__main__":
    unittest.main()
