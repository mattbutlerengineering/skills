"""eval_trends.py — a read-only eval-trend view over recorded history.

The run is docs/features/eval-trends/ (ADR-0115). Every expected value
here is worked by hand in this file or recomputed from the fixture files
the test itself wrote; none is copied from the tool. Fixture trees are
temp directories, never files under evals/ or plugin-evals/. No test
calls a model, `claude` or the network.
"""
import copy
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import eval_trends  # noqa: E402

SUITE_A = ("claude", "m", 3, 0.5)
SUITE_B = ("omp", "m", 3, 0.5)
SET_X = (("c1", "direct", "q1"), ("c2", "direct", "q2"))
SET_Y = (("c1", "direct", "q1"), ("c3", "direct", "q3"))
SET_Z = (("z1", "direct", "q1"),)
SET_W = (("w1", "direct", "q1"),)


def row(file, day, suite=SUITE_A, case_set=SET_X, n=40, hits=20, cost=None):
    return {"surface": "trigger", "file": file, "day": day, "suite": suite,
            "case_set": case_set, "n": n, "hits": hits, "cost": cost}


class TestConstants(unittest.TestCase):
    def test_the_minimums_are_the_architectures(self):
        self.assertEqual(eval_trends.MIN_CASES, 30)
        self.assertEqual(eval_trends.MIN_DAYS, 2)


class TestWilson(unittest.TestCase):
    """Wilson 95 percent, z = 1.96. Checkpoints worked by hand from
    centre (p + z*z/2n)/(1 + z*z/n), half-width
    z*sqrt(p(1-p)/n + z*z/4n*n)/(1 + z*z/n); for p = 1/2 the centre is
    1/2 and the half-width is z*sqrt(1/4n + z*z/4n*n)/(1 + z*z/n)."""

    def assertInterval(self, got, lo, hi):
        self.assertAlmostEqual(got[0], lo, places=3)
        self.assertAlmostEqual(got[1], hi, places=3)

    def test_a_fifty_percent_rate_narrows_with_n(self):
        self.assertInterval(eval_trends.wilson(5, 10), 0.2366, 0.7634)
        self.assertInterval(eval_trends.wilson(15, 30), 0.3315, 0.6685)
        # 23.5 of 47 is exactly one half; the formula takes any h.
        self.assertInterval(eval_trends.wilson(23.5, 47), 0.3626, 0.6374)

    def test_the_architecture_checkpoints_to_printed_precision(self):
        printed = [tuple(round(x, 2) for x in eval_trends.wilson(h, n))
                   for h, n in ((5, 10), (15, 30), (23.5, 47))]
        self.assertEqual(printed, [(0.24, 0.76), (0.33, 0.67),
                                   (0.36, 0.64)])

    def test_edges_stay_inside_zero_to_one(self):
        # 0 of 10: lower is 0, upper is z*z/(n + z*z) = 3.8416/13.8416.
        self.assertInterval(eval_trends.wilson(0, 10), 0.0, 0.2775)
        # 10 of 10: lower is n/(n + z*z) = 10/13.8416, upper is 1.
        self.assertInterval(eval_trends.wilson(10, 10), 0.7225, 1.0)
        for h, n in ((0, 1), (1, 1), (0, 185), (185, 185)):
            lo, hi = eval_trends.wilson(h, n)
            self.assertTrue(0.0 <= lo <= hi <= 1.0, (h, n, lo, hi))


class TestDayInterval(unittest.TestCase):
    def test_one_record_is_its_own_interval(self):
        got = eval_trends.day_interval([row("a", "d1", n=10, hits=5)])
        self.assertEqual(got, eval_trends.wilson(5, 10))

    def test_a_day_of_reruns_is_the_hull_of_the_intervals(self):
        rows = [row("a", "d1", n=10, hits=5), row("b", "d1", n=30, hits=25)]
        lo, hi = eval_trends.day_interval(rows)
        # lower of 5/10 (0.2366), upper of 25/30 (0.9266)
        self.assertAlmostEqual(lo, 0.2366, places=3)
        self.assertAlmostEqual(hi, 0.9266, places=3)

    def test_the_input_is_not_mutated(self):
        rows = [row("a", "d1", n=10, hits=5), row("b", "d1", n=30, hits=25)]
        before = copy.deepcopy(rows)
        eval_trends.day_interval(rows)
        self.assertEqual(rows, before)


class TestCostPerPass(unittest.TestCase):
    def test_summed_cost_over_summed_passes_to_four_decimals(self):
        rows = [row("a", "d1", n=3, hits=2, cost=0.5771082),
                row("b", "d1", n=6, hits=4, cost=4.057434)]
        # (0.5771082 + 4.057434) / (2 + 4) = 0.7724237
        self.assertEqual(eval_trends.cost_per_pass(rows), 0.7724)

    def test_one_record_without_a_cost_refuses_the_line(self):
        rows = [row("a", "d1", hits=2, cost=1.0),
                row("b", "d1", hits=4, cost=None)]
        self.assertIsNone(eval_trends.cost_per_pass(rows))

    def test_no_passed_case_refuses_the_line(self):
        self.assertIsNone(eval_trends.cost_per_pass(
            [row("a", "d1", hits=0, cost=1.0)]))


class TestCaseSetHex(unittest.TestCase):
    def test_first_eight_hex_of_a_sha256_of_the_sorted_tuples(self):
        want = hashlib.sha256(
            repr(tuple(sorted(SET_X))).encode("utf-8")).hexdigest()[:8]
        self.assertEqual(eval_trends.case_set_hex(SET_X), want)
        self.assertEqual(eval_trends.case_set_hex(tuple(reversed(SET_X))),
                         want)
        self.assertNotEqual(eval_trends.case_set_hex(SET_Y), want)


class TestClassify(unittest.TestCase):
    def mixed(self):
        return [
            row("trend-1", "2026-01-01"),
            row("trend-2", "2026-01-02"),
            row("odd-set", "2026-01-01", case_set=SET_Y),
            row("other-suite", "2026-01-01", suite=SUITE_B),
            row("rerun-1", "2026-01-03", case_set=SET_Z),
            row("rerun-2", "2026-01-03", case_set=SET_Z),
            row("small-1", "2026-01-01", case_set=SET_W, n=4, hits=1),
            row("small-2", "2026-01-02", case_set=SET_W, n=4, hits=3),
        ]

    def states(self, rows):
        return {r["file"]: (r["state"], r["reason"])
                for r in eval_trends.classify(rows)}

    def test_each_record_gets_exactly_one_state(self):
        self.assertEqual(self.states(self.mixed()), {
            "trend-1": ("trend", None), "trend-2": ("trend", None),
            "odd-set": ("single", "case sets differ"),
            "other-suite": ("single", "different suites"),
            "rerun-1": ("same-day", None), "rerun-2": ("same-day", None),
            "small-1": ("small", None), "small-2": ("small", None)})

    def test_state_counts_sum_to_the_record_count(self):
        rows = self.mixed()
        counts = {}
        for r in eval_trends.classify(rows):
            counts[r["state"]] = counts.get(r["state"], 0) + 1
        self.assertEqual(counts, {"trend": 2, "single": 2, "same-day": 2,
                                  "small": 2})
        self.assertEqual(sum(counts.values()), len(rows))

    def test_order_is_preserved_and_the_input_is_not_mutated(self):
        rows = self.mixed()
        before = copy.deepcopy(rows)
        got = eval_trends.classify(rows)
        self.assertEqual(rows, before)
        self.assertEqual([r["file"] for r in got],
                         [r["file"] for r in rows])

    def test_fewer_than_two_records_is_too_few_records(self):
        self.assertEqual(eval_trends.classify([]), [])
        self.assertEqual(self.states([row("only", "2026-01-01")]),
                         {"only": ("too few records", None)})

    def test_a_null_model_equals_only_a_null_model(self):
        null = ("claude", None, 3, 0.5)
        rows = [row("a", "2026-01-01", suite=null),
                row("b", "2026-01-02", suite=SUITE_A)]
        self.assertEqual(self.states(rows), {
            "a": ("single", "different suites"),
            "b": ("single", "different suites")})
        rows = [row("a", "2026-01-01", suite=null),
                row("b", "2026-01-02", suite=null)]
        self.assertEqual(self.states(rows), {"a": ("trend", None),
                                             "b": ("trend", None)})

    def test_two_records_on_one_day_never_pair_with_each_other(self):
        rows = [row("a", "2026-01-01"), row("b", "2026-01-01")]
        self.assertEqual(self.states(rows), {"a": ("same-day", None),
                                             "b": ("same-day", None)})

    def test_reruns_beside_another_day_make_a_trend(self):
        rows = [row("a", "2026-01-01"), row("b", "2026-01-01"),
                row("c", "2026-01-02")]
        self.assertEqual({v[0] for v in self.states(rows).values()},
                         {"trend"})

    def test_one_small_record_makes_the_whole_group_small(self):
        rows = [row("a", "2026-01-01", n=29), row("b", "2026-01-02")]
        self.assertEqual({v[0] for v in self.states(rows).values()},
                         {"small"})


if __name__ == "__main__":
    unittest.main()
