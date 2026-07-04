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

from protocol import next_stage  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
