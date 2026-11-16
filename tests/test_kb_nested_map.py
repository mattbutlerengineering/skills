"""Audit defect #1852: a nested-map `sources:`/`related:` value is a kb
problem string, not an AttributeError."""
import tempfile
import unittest
from pathlib import Path

import kb


class TestNestedMapField(unittest.TestCase):
    def test_nested_sources_is_a_problem_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            page = root / "docs" / "kb" / "p.md"
            page.parent.mkdir(parents=True)
            page.write_text("---\nsummary: s\nsources:\n  code: kb.py\n"
                            "verified: abc1234\nrelated:\n---\n\n# T\n")
            problems = kb.lint(root)
            self.assertIn("kb: docs/kb/p.md field 'sources' is a nested"
                          " map, not a comma-separated list", problems)


if __name__ == "__main__":
    unittest.main()
