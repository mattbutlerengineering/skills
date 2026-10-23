"""eval_trends.py — a read-only eval-trend view over recorded history.

The run is docs/features/eval-trends/ (ADR-0115). Every expected value
here is worked by hand in this file or recomputed from the fixture files
the test itself wrote; none is copied from the tool. Fixture trees are
temp directories, never files under evals/ or plugin-evals/. No test
calls a model, `claude` or the network.
"""
import copy
import hashlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_trends  # noqa: E402
import eval_trends_fixture as fx  # noqa: E402
import test_dual_membership  # noqa: E402

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


class TempRoot(unittest.TestCase):
    """A temp repo root the test writes record files into."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="eval-trends-"))
        self.addCleanup(shutil.rmtree, self.root)

    def load(self):
        return eval_trends.load_rows(self.root)

    def rows_of(self, surface):
        rows, _ = self.load()
        return [r for r in rows if r["surface"] == surface]


class TestLoadTrigger(TempRoot):
    def test_a_record_becomes_one_row(self):
        cases = [("a", "idea", "qa", True), ("b", "prd", "qb", False),
                 ("c", "idea", "qc", True)]
        fx.write_json(self.root, "evals/results/trigger-2026-07-05-3.json",
                      fx.trigger_record("2026-07-05", cases, model="m1",
                                        runs=5, threshold=0.5))
        rows, problems = self.load()
        self.assertEqual(problems, [])
        self.assertEqual(rows, [{
            "surface": "trigger", "file": "trigger-2026-07-05-3.json",
            "day": "2026-07-05",
            "suite": ("claude", "m1", 5, 0.5),
            "case_set": (("a", "idea", "qa"), ("b", "prd", "qb"),
                         ("c", "idea", "qc")),
            "n": 3, "hits": 2, "cost": None}])

    def test_the_harness_comes_from_the_name_and_a_null_model_stays_null(self):
        fx.write_json(self.root, "evals/results/trigger-omp-2026-07-05.json",
                      fx.trigger_record("2026-07-05", fx.numbered_cases(2, 1),
                                        model=None, harness="omp"))
        (row,) = self.rows_of("trigger")
        self.assertEqual(row["suite"], ("omp", None, 3, 0.5))

    def test_a_record_harness_that_disagrees_with_its_name_is_a_problem(self):
        fx.write_json(self.root, "evals/results/trigger-2026-07-05.json",
                      fx.trigger_record("2026-07-05", fx.numbered_cases(2, 1),
                                        harness="omp"))
        rows, problems = self.load()
        self.assertEqual(rows, [])
        self.assertEqual(problems, [
            "eval-trends: evals/results/trigger-2026-07-05.json harness "
            "'omp' disagrees with its name"])

    def test_files_are_listed_in_sorted_path_order(self):
        for name in ("trigger-2026-07-05-2.json", "trigger-2026-07-03.json",
                     "trigger-2026-07-05.json"):
            fx.write_json(self.root, f"evals/results/{name}",
                          fx.trigger_record(name[8:18],
                                            fx.numbered_cases(1, 1)))
        self.assertEqual([r["file"] for r in self.rows_of("trigger")], [
            "trigger-2026-07-03.json", "trigger-2026-07-05-2.json",
            "trigger-2026-07-05.json"])

    def test_malformed_trigger_records_are_labelled_problems(self):
        base = fx.trigger_record("2026-07-05", fx.numbered_cases(3, 2))
        disagree = {**base, "summary": {**base["summary"], "passed": 3}}
        total = {**base, "summary": {**base["summary"], "total": 4}}
        errors = fx.trigger_record("2026-07-05", fx.numbered_cases(3, 2),
                                   errors=2)
        no_results = {k: v for k, v in base.items() if k != "results"}
        no_date = {k: v for k, v in base.items() if k != "date"}
        for name, data in (("trigger-2026-07-01.json", disagree),
                           ("trigger-2026-07-02.json", total),
                           ("trigger-2026-07-03.json", errors),
                           ("trigger-2026-07-04.json", no_results),
                           ("trigger-2026-07-06.json", no_date),
                           ("trigger-2026-07-07.json", ["not", "an", "obj"])):
            if isinstance(data, dict) and "date" in data:
                data = {**data, "date": name[8:18]}  # the name's own day
            fx.write_json(self.root, f"evals/results/{name}", data)
        (self.root / "evals/results/trigger-2026-07-08.json").write_text(
            "{not json", encoding="utf-8")
        rows, problems = self.load()
        self.assertEqual(rows, [])
        pre = "eval-trends: evals/results/"
        self.assertEqual(problems[:6], [
            f"{pre}trigger-2026-07-01.json summary disagrees with its "
            "results",
            f"{pre}trigger-2026-07-02.json summary disagrees with its "
            "results",
            f"{pre}trigger-2026-07-03.json records 2 error(s)",
            f"{pre}trigger-2026-07-04.json missing field results",
            f"{pre}trigger-2026-07-06.json missing field date",
            f"{pre}trigger-2026-07-07.json is not a JSON object"])
        self.assertTrue(problems[6].startswith(
            f"{pre}trigger-2026-07-08.json is not valid JSON: "), problems)
        self.assertEqual(len(problems), 7)

    def test_an_unparseable_name_is_a_problem(self):
        fx.write_json(self.root, "evals/results/trigger-2026-07-05-0.json",
                      fx.trigger_record("2026-07-05", fx.numbered_cases(1, 1)))
        rows, problems = self.load()
        self.assertEqual((rows, problems), ([], [
            "eval-trends: evals/results/trigger-2026-07-05-0.json name "
            "fits no results grammar"]))


class TestLoadCharter(TempRoot):
    def test_hits_are_sensitive_verdicts_and_the_suite_carries_the_arm(self):
        fx.write_json(self.root, "evals/results/charter-2026-09-28-2.json",
                      fx.charter_record("2026-09-28", [
                          ("x", "swe", "sensitive"),
                          ("y", "planner", "inconclusive"),
                          ("z", "swe", "insensitive")],
                          arm="control", model="haiku",
                          charters={"swe": "bb", "planner": "aa"}))
        (row,) = self.rows_of("charter")
        self.assertEqual(row, {
            "surface": "charter", "file": "charter-2026-09-28-2.json",
            "day": "2026-09-28",
            "suite": ("control", "haiku", (("planner", "aa"), ("swe", "bb"))),
            "case_set": (("x", "swe"), ("y", "planner"), ("z", "swe")),
            "n": 3, "hits": 1, "cost": None})

    def test_a_missing_field_is_a_problem(self):
        data = fx.charter_record("2026-09-28", [("x", "swe", "sensitive")])
        del data["arm"]
        fx.write_json(self.root, "evals/results/charter-2026-09-28.json",
                      data)
        self.assertEqual(self.load(), ([], [
            "eval-trends: evals/results/charter-2026-09-28.json missing "
            "field arm"]))


class TestLoadOutput(TempRoot):
    def test_date_and_slug_come_from_the_directory_name(self):
        fx.write_json(
            self.root, "evals/results/output/decompose-2026-07-01-2/"
            "grading.json",
            fx.output_record([("b says x", True), ("a says y", False)]))
        (row,) = self.rows_of("output")
        self.assertEqual(row, {
            "surface": "output", "file": "decompose-2026-07-01-2",
            "day": "2026-07-01", "suite": ("decompose",),
            "case_set": (("a says y",), ("b says x",)),
            "n": 2, "hits": 1, "cost": None})

    def test_a_summary_that_disagrees_is_a_problem(self):
        data = fx.output_record([("a", True), ("b", True)])
        data["summary"]["passed"] = 1
        fx.write_json(self.root, "evals/results/output/x-2026-07-01/"
                      "grading.json", data)
        self.assertEqual(self.load(), ([], [
            "eval-trends: evals/results/output/x-2026-07-01/grading.json "
            "summary disagrees with its results"]))

    def test_a_directory_without_a_grading_file_is_not_a_record(self):
        (self.root / "evals/results/output/x-2026-07-01").mkdir(parents=True)
        self.assertEqual(self.load(), ([], []))


class TestLoadPlugin(TempRoot):
    def test_a_record_becomes_one_row_with_its_recorded_cost(self):
        cases = [("b-case", "prompt b", [("g2", "md2"), ("g1", None)]),
                 ("a-case", "prompt a", [("g1", "md1")])]
        fx.write_json(self.root, "plugin-evals/records/2026-10-10-3.json",
                      fx.plugin_record("2026-10-10T23:26:53.370Z", cases,
                                       tags=("lean", "implement"),
                                       cost=4.057434, passed=1))
        (row,) = self.rows_of("plugin")
        self.assertEqual(row, {
            "surface": "plugin", "file": "2026-10-10-3.json",
            "day": "2026-10-10",
            "suite": (("implement", "lean"), "none", "claude-sonnet-5",
                      "claude-haiku-4-5", 1),
            "case_set": (("a-case", "prompt a", (("g1", "md1"),)),
                         ("b-case", "prompt b", (("g1", ""), ("g2", "md2")))),
            "n": 2, "hits": 1, "cost": 4.057434})

    def test_a_partial_record_is_a_problem(self):
        fx.write_json(self.root, "plugin-evals/records/2026-10-10.json",
                      fx.plugin_record("2026-10-10T01:00:00Z",
                                       [("a", "p", [])], partial=True))
        self.assertEqual(self.load(), ([], [
            "eval-trends: plugin-evals/records/2026-10-10.json is partial"]))

    def test_a_record_without_a_cost_has_cost_none(self):
        data = fx.plugin_record("2026-10-10T01:00:00Z", [("a", "p", [])])
        del data["costUsd"]
        fx.write_json(self.root, "plugin-evals/records/2026-10-10.json", data)
        (row,) = self.rows_of("plugin")
        self.assertIsNone(row["cost"])

    def test_a_missing_aggregate_is_a_problem(self):
        data = fx.plugin_record("2026-10-10T01:00:00Z", [("a", "p", [])])
        del data["aggregates"]
        fx.write_json(self.root, "plugin-evals/records/2026-10-10.json", data)
        self.assertEqual(self.load(), ([], [
            "eval-trends: plugin-evals/records/2026-10-10.json missing "
            "field aggregates"]))


class TestLoadDecomposeSignals(TempRoot):
    def test_a_record_is_an_inventory_row_with_no_measure(self):
        fx.write_json(
            self.root, "evals/results/decompose-signals-2026-10-18.json",
            fx.signals_record("2026-10-18"))
        (row,) = self.rows_of("decompose-signals")
        self.assertEqual(row, {
            "surface": "decompose-signals",
            "file": "decompose-signals-2026-10-18.json",
            "day": "2026-10-18", "suite": None, "case_set": None,
            "n": None, "hits": None, "cost": None})

    def test_an_absent_location_is_an_empty_surface_not_an_error(self):
        self.assertEqual(self.load(), ([], []))

    def test_a_signals_record_with_a_bad_name_is_a_problem(self):
        fx.write_json(
            self.root, "evals/results/decompose-signals-2026-10-18-0.json",
            fx.signals_record("2026-10-18"))
        self.assertEqual(self.load(), ([], [
            "eval-trends: evals/results/decompose-signals-2026-10-18-0.json"
            " name fits no results grammar"]))

    def test_the_surface_can_never_reach_classify(self):
        """Two signals records on different days share a None suite and a
        None case set; measured() leaves them out, so no trend, rerun
        spread or cost line can be built from them."""
        for day in ("2026-10-17", "2026-10-18"):
            fx.write_json(
                self.root, f"evals/results/decompose-signals-{day}.json",
                fx.signals_record(day))
        rows, problems = self.load()
        self.assertEqual((len(rows), problems), (2, []))
        self.assertEqual(eval_trends.measured(rows), [])
        mixed = rows + [row("t", "2026-01-01")]
        self.assertEqual([r["file"] for r in eval_trends.measured(mixed)],
                         ["t"])


class TestUnreadableLocations(TempRoot):
    """A symlinked record or directory, or an oversize file, is one
    labelled problem and no row; it is refused before any read."""

    def record(self, rel="evals/results/trigger-2026-07-01.json"):
        fx.write_json(self.root, rel, fx.trigger_record(
            "2026-07-01", fx.numbered_cases(3, 1)))
        return self.root / rel

    def outside(self):
        out = Path(tempfile.mkdtemp(prefix="eval-trends-outside-"))
        self.addCleanup(shutil.rmtree, out)
        return out

    def test_a_symlinked_record_is_a_problem_not_a_row(self):
        target = self.outside() / "t.json"
        target.write_text(self.record().read_text())
        (self.root / "evals/results/trigger-2026-07-01.json").unlink()
        (self.root / "evals/results/trigger-2026-07-01.json").symlink_to(
            target)
        self.assertEqual(self.load(), ([], [
            "eval-trends: evals/results/trigger-2026-07-01.json "
            "is a symlink; not read"]))

    def test_a_dangling_symlink_is_a_problem_too(self):
        (self.root / "evals/results").mkdir(parents=True)
        (self.root / "evals/results/trigger-2026-07-01.json").symlink_to(
            self.outside() / "gone.json")
        _, problems = self.load()
        self.assertEqual(problems, [
            "eval-trends: evals/results/trigger-2026-07-01.json "
            "is a symlink; not read"])

    def test_a_symlinked_directory_above_a_record_is_a_problem(self):
        real = self.outside() / "decompose-2026-07-01"
        real.mkdir()
        (real / "grading.json").write_text("{}")
        (self.root / "evals/results/output").mkdir(parents=True)
        (self.root / "evals/results/output/decompose-2026-07-01").symlink_to(
            real, target_is_directory=True)
        self.assertEqual(self.load(), ([], [
            "eval-trends: evals/results/output/decompose-2026-07-01/"
            "grading.json is under a symlinked directory; not read"]))

    def test_one_byte_over_the_bound_is_refused_unparsed(self):
        path = self.record()
        size = path.stat().st_size
        with mock.patch.object(eval_trends, "MAX_RECORD_BYTES", size - 1), \
                mock.patch.object(eval_trends, "read_file") as read:
            rows, problems = self.load()
        read.assert_not_called()
        self.assertEqual(rows, [])
        self.assertEqual(problems, [
            f"eval-trends: evals/results/trigger-2026-07-01.json is "
            f"{size} bytes, above the {size - 1}-byte bound; not read"])

    def test_a_file_at_the_bound_is_read(self):
        size = self.record().stat().st_size
        with mock.patch.object(eval_trends, "MAX_RECORD_BYTES", size):
            rows, problems = self.load()
        self.assertEqual((len(rows), problems), (1, []))

    def test_the_bound_is_a_clear_multiple_of_the_largest_real_record(self):
        self.assertGreaterEqual(eval_trends.MAX_RECORD_BYTES, 50 * 70641)


class TestDualMembershipPin(unittest.TestCase):
    """Red until S6 adds the import: the pin names the new edge."""

    def test_the_pin_holds_the_eval_trends_edge_and_55_pairs(self):
        pinned = test_dual_membership.ROOT_ONLY_IMPORTS_MIRRORED
        self.assertIn(("eval_trends", "cli"), pinned)
        self.assertEqual(len(pinned), 55)


if __name__ == "__main__":
    unittest.main()
