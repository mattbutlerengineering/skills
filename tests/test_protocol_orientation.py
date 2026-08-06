"""Orientation-protocol seam: the artifacts-are-the-state decision table
(docs/pipeline-protocol.md) verified against fixture docs trees, pinning
the protocol module's next_stage directly — the one implementation that
must agree with the spec in docs/pipeline-protocol.md.

Each fixture under tests/fixtures/orientation/ is one row of the table:
a `run/` directory holding a run's artifacts, and an `expected` file naming
the stage orientation must return for that tree.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from protocol import next_stage  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "orientation"


def fixture_cases():
    return sorted(p for p in FIXTURES.iterdir() if p.is_dir())


class TestFixtureTrees(unittest.TestCase):
    def test_fixtures_exist(self):
        self.assertTrue(fixture_cases(), f"no fixture trees in {FIXTURES}")

    def test_decision_table(self):
        for case in fixture_cases():
            with self.subTest(fixture=case.name):
                expected = (case / "expected").read_text(encoding="utf-8").strip()
                self.assertEqual(next_stage(case / "run"), expected)


if __name__ == "__main__":
    unittest.main()
