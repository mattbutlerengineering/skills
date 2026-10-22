"""eval_trends.py on the records the repo actually holds.

Two tests with two jobs (docs/features/eval-trends/breakdown.md, S15).
The FROZEN test pins the printed view of a byte-for-byte copy of the
records as they stood on 2026-10-21, under
tests/fixtures/eval_trends_2026_10_21/. That copy is test data, not an
eval record; no eval tool reads it, and landing new records in evals/ or
plugin-evals/ can never turn it red. The LIVE smoke test reads the real
tree and pins nothing that rots.
"""
import contextlib
import io
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import eval_schema  # noqa: E402
import eval_trends  # noqa: E402

REPO = Path(eval_trends.__file__).resolve().parent
FROZEN = REPO / "tests" / "fixtures" / "eval_trends_2026_10_21"
# (surface, glob under the root) in the order the view prints them.
LOCATIONS = (
    ("trigger", "evals/results/trigger*.json"),
    ("charter", "evals/results/charter-*.json"),
    ("output", "evals/results/output/*/grading.json"),
    ("plugin", "plugin-evals/records/*.json"),
    ("decompose-signals", "evals/results/decompose-signals-*.json"),
)


def run(root):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = eval_trends.main([str(root)])
    return code, out.getvalue().splitlines()


def inventory(lines):
    """{surface: record count} from the inventory lines."""
    found = {}
    for ln in lines:
        match = re.match(r"eval-trends: ([a-z-]+): (\d+) record\(s\)", ln)
        if match:
            found[match[1]] = int(match[2])
    return found


def refused_total(lines, surface):
    """Records the surface's REFUSED lines cover, summed."""
    total = 0
    for ln in lines:
        if not ln.startswith(f"eval-trends: REFUSED {surface}:"):
            continue
        have = re.search(r"too few records: need \d+, have (\d+)", ln)
        counted = re.search(r"(?:: | in )(\d+) record\(s\)", ln)
        total += int((have or counted)[1])
    return total


def trended_total(lines, surface):
    """Records named in the surface's trend lines (each ends in its files)."""
    total = 0
    for ln in lines:
        if ln.startswith(f"eval-trends: {surface} trend set "):
            total += len(ln.rsplit(" (", 1)[1].rstrip(")").split(", "))
    return total


class TestFrozenRecords(unittest.TestCase):
    """The view of the 2026-10-21 records, pinned."""

    @classmethod
    def setUpClass(cls):
        cls.code, cls.lines = run(FROZEN)

    def test_exit_zero_with_no_problem(self):
        self.assertEqual(self.code, 0)
        self.assertEqual(self.lines[-1], "eval-trends: 0 problem(s)")

    def test_inventory_counts(self):
        self.assertEqual(inventory(self.lines), {
            "trigger": 41, "charter": 2, "output": 2, "plugin": 3,
            "decompose-signals": 2})

    def test_counts_equal_the_fixture_files(self):
        counts = {s: len(list(FROZEN.glob(g))) for s, g in LOCATIONS}
        self.assertEqual(counts, inventory(self.lines))

    def test_every_fixture_name_parses_as_a_results_name(self):
        for path in FROZEN.glob("evals/results/*.json"):
            with self.subTest(name=path.name):
                self.assertIsNotNone(
                    eval_schema.parse_results_stem(path.stem))
        for path in FROZEN.glob("evals/results/output/*"):
            with self.subTest(name=path.name):
                self.assertIsNotNone(eval_schema.parse_results_stem(path.name))

    def test_no_trend_line_on_these_records(self):
        self.assertEqual([ln for ln in self.lines if "trend set" in ln], [])
        self.assertEqual([ln for ln in self.lines if "cost per pass" in ln],
                         [])

    def test_every_surface_is_refused_and_the_counts_sum_to_the_inventory(
            self):
        for surface, count in inventory(self.lines).items():
            if surface == "decompose-signals":
                continue
            with self.subTest(surface=surface):
                self.assertEqual(refused_total(self.lines, surface), count)
        self.assertIn(eval_trends.SIGNALS_REFUSED, self.lines)

    def test_the_refused_lines_for_the_small_surfaces_exactly(self):
        refused = [ln for ln in self.lines if ln.startswith("eval-trends: REFUSED")
                   and "REFUSED trigger" not in ln]
        self.assertEqual(refused, [
            "eval-trends: REFUSED charter: only same-day records: 2 "
            "record(s) in 1 group(s), each on one day; no trend claim",
            "eval-trends: REFUSED output: case sets differ: 2 record(s) "
            "share a suite with another record but not its case set; no "
            "trend claim",
            "eval-trends: REFUSED plugin: different suites: 3 record(s) "
            "share no suite with another record; no trend claim",
            eval_trends.SIGNALS_REFUSED])

    def test_the_185_case_same_day_pair_is_a_rerun_spread(self):
        spread = [ln for ln in self.lines if "rerun spread 2026-10-10" in ln]
        self.assertEqual(len(spread), 1)
        self.assertIn("passed 159..163 of 185 over 2 run(s) "
                      "(trigger-2026-10-10-2.json, trigger-2026-10-10-3.json)",
                      spread[0])
        self.assertIn(
            "eval-trends: REFUSED trigger: only same-day records: 2 "
            "record(s) in 1 group(s), each on one day; no trend claim",
            self.lines)

    def test_the_not_computed_line_names_the_note(self):
        self.assertIn(eval_trends.NOT_COMPUTED, self.lines)
        self.assertTrue(
            self.lines[-2].endswith(
                "see docs/research/eval-quality-metrics-2026-10-21.md"))


class TestLiveTreeSmoke(unittest.TestCase):
    """Reads the real repo root and pins only what cannot rot.

    Records are append-only and will grow: a later run may add a real
    trend, a new surface file, or a cost line. So this test asserts the
    tool's own invariants (a clean run, an inventory that matches an
    independent glob, and every record accounted for as refused or
    trended) and never a literal count or the absence of a trend line;
    the frozen copy above carries those pins."""

    @classmethod
    def setUpClass(cls):
        cls.code, cls.lines = run(REPO)

    def test_exit_zero_and_no_malformed_record(self):
        self.assertEqual(self.code, 0)
        self.assertEqual(self.lines[-1], "eval-trends: 0 problem(s)")

    def test_each_inventory_count_equals_an_independent_glob(self):
        counts = {s: len(list(REPO.glob(g))) for s, g in LOCATIONS}
        self.assertEqual(inventory(self.lines), counts)

    def test_every_record_is_refused_or_trended(self):
        for surface, count in inventory(self.lines).items():
            if surface == "decompose-signals":
                continue
            with self.subTest(surface=surface):
                self.assertEqual(
                    refused_total(self.lines, surface)
                    + trended_total(self.lines, surface), count)


if __name__ == "__main__":
    unittest.main()
