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

from protocol import STAGE_ARTIFACTS, next_stage  # noqa: E402

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

    def test_every_stage_the_table_can_return_has_a_fixture(self):
        """Closure between the rows and the fixtures, both ways.

        Without it the fixture set is whatever rows someone happened to
        write trees for, and a row can be added to the table -- or reached
        by a new completion rule -- with nothing that exercises it. That
        is not hypothetical: `decompose` was reachable here (a run that
        re-entered at architect, with architecture.md written and
        breakdown.md not) and no fixture expected it, so the row was
        pinned by nobody.

        The reverse direction catches the cheaper mistake: an `expected`
        file naming a stage the table cannot return is a typo that would
        otherwise sit green forever, since test_decision_table would
        simply compare two things that are equal for the wrong reason.
        """
        reachable = {stage for stage, _ in STAGE_ARTIFACTS}
        reachable.add("complete")
        covered = {(case / "expected").read_text(encoding="utf-8").strip()
                   for case in fixture_cases()}
        self.assertEqual(sorted(reachable - covered), [],
                         "rows of the table that no fixture"
                         " expects")
        self.assertEqual(sorted(covered - reachable), [],
                         "fixtures expecting a stage the table cannot"
                         " return")


if __name__ == "__main__":
    unittest.main()
