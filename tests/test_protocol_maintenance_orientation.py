"""Maintenance-run orientation seam: the maintenance rows of the
artifacts-are-the-state decision table (docs/pipeline-protocol.md,
ADR-0025) verified against fixture docs trees, pinning the protocol
module's next_stage directly — capture entry, re-entry depth, the
breakdown-placement rule, and the never-skippable verify.

Each fixture under tests/fixtures/maintenance-orientation/ is one row of
the table: a `docs/fixes/<slug>/` tree holding a maintenance run's
artifacts, and an `expected` file naming the stage orientation must
return for that tree. The run directory is discovered the way the
protocol discovers it — as a directory under docs/fixes/ — so the
fixtures also pin path-based recognition of an empty run.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from protocol import MAINTENANCE_STAGE_ARTIFACTS, next_stage  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "maintenance-orientation"


def fixture_cases():
    return sorted(p for p in FIXTURES.iterdir() if p.is_dir())


def run_dir(case):
    """The case's single run directory under docs/fixes/ (the protocol's
    run-discovery rule for maintenance runs)."""
    fixes = case / "docs" / "fixes"
    runs = sorted(p for p in fixes.iterdir() if p.is_dir())
    assert len(runs) == 1, f"expected one run dir in {fixes}, got {runs}"
    return runs[0]


class TestMaintenanceFixtureTrees(unittest.TestCase):
    def test_fixtures_exist(self):
        self.assertTrue(fixture_cases(), f"no fixture trees in {FIXTURES}")

    def test_decision_table(self):
        for case in fixture_cases():
            with self.subTest(fixture=case.name):
                expected = (case / "expected").read_text(encoding="utf-8").strip()
                self.assertEqual(next_stage(run_dir(case)), expected)

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
        reachable = {stage for stage, _ in MAINTENANCE_STAGE_ARTIFACTS}
        reachable.add("complete")
        covered = {(case / "expected").read_text(encoding="utf-8").strip()
                   for case in fixture_cases()}
        self.assertEqual(sorted(reachable - covered), [],
                         "rows of the maintenance table that no fixture"
                         " expects")
        self.assertEqual(sorted(covered - reachable), [],
                         "fixtures expecting a stage the table cannot"
                         " return")


if __name__ == "__main__":
    unittest.main()
