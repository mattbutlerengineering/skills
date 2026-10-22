"""eval_trends.py — fail-closed cases found in the review of the run
docs/features/eval-trends/ (review.md). Each test builds its record in a
temp tree the test owns; no model, CLI or network call."""
import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_trends  # noqa: E402
import eval_trends_fixture as fx  # noqa: E402


class Tree(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="eval-trends-rev-"))
        self.addCleanup(shutil.rmtree, self.root)

    def load(self):
        return eval_trends.load_rows(self.root)

    def trigger(self, name, date, **kw):
        data = fx.trigger_record(date, fx.numbered_cases(30, 15), **kw)
        fx.write_json(self.root, f"evals/results/{name}", data)
        return data


class TestDateFields(Tree):
    def test_a_trigger_date_that_disagrees_with_its_name_is_a_problem(self):
        self.trigger("trigger-2026-10-05.json", "2026-10-01")
        self.assertEqual(self.load(), ([], [
            "eval-trends: evals/results/trigger-2026-10-05.json date "
            "disagrees with its name"]))

    def test_a_charter_date_that_disagrees_with_its_name_is_a_problem(self):
        fx.write_json(self.root, "evals/results/charter-2026-09-28.json",
                      fx.charter_record("2026-09-29",
                                        [("x", "swe", "sensitive")]))
        self.assertEqual(self.load(), ([], [
            "eval-trends: evals/results/charter-2026-09-28.json date "
            "disagrees with its name"]))

    def test_a_signals_date_that_disagrees_with_its_name_is_a_problem(self):
        fx.write_json(self.root,
                      "evals/results/decompose-signals-2026-10-18.json",
                      fx.signals_record("2026-10-19"))
        rows, problems = self.load()
        self.assertEqual(rows, [])
        self.assertEqual(len(problems), 1)

    def test_a_plugin_start_day_that_disagrees_with_its_name_is_a_problem(self):
        fx.write_json(self.root, "plugin-evals/records/2026-10-10.json",
                      fx.plugin_record("2026-10-11T01:00:00Z",
                                       [("a", "p", [])]))
        self.assertEqual(self.load(), ([], [
            "eval-trends: plugin-evals/records/2026-10-10.json startedAt "
            "disagrees with its name"]))

    def test_an_impossible_calendar_date_is_a_problem(self):
        self.trigger("trigger-2026-13-45.json", "2026-13-45")
        rows, problems = self.load()
        self.assertEqual(rows, [])
        self.assertEqual(len(problems), 1)


class TestUnhashableValues(Tree):
    def test_an_object_model_is_a_problem_not_a_traceback(self):
        self.trigger("trigger-2026-10-05.json", "2026-10-05",
                     model={"a": 1})
        rows, problems = self.load()
        self.assertEqual(rows, [])
        self.assertEqual(problems, [
            "eval-trends: evals/results/trigger-2026-10-05.json "
            "malformed field values"])

    def test_a_list_id_is_a_problem_not_a_traceback(self):
        data = fx.trigger_record("2026-10-05", fx.numbered_cases(30, 15))
        data["results"][0]["id"] = [1]
        fx.write_json(self.root, "evals/results/trigger-2026-10-05.json",
                      data)
        rows, problems = self.load()
        self.assertEqual(rows, [])
        self.assertEqual(len(problems), 1)


class TestPluginCounts(Tree):
    def write(self, passed, total=None):
        data = fx.plugin_record("2026-10-10T01:00:00Z", [("a", "p", [])],
                                passed=passed)
        if total is not None:
            data["aggregates"]["casesTotal"] = total
        fx.write_json(self.root, "plugin-evals/records/2026-10-10.json", data)

    def test_more_passed_than_total_is_a_problem(self):
        self.write(passed=5, total=3)
        self.assertEqual(self.load(), ([], [
            "eval-trends: plugin-evals/records/2026-10-10.json "
            "aggregates disagree with its cases"]))

    def test_a_total_that_is_not_the_case_count_is_a_problem(self):
        self.write(passed=1, total=40)
        self.assertEqual(len(self.load()[1]), 1)


class TestWording(Tree):
    def lines(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            eval_trends.main([str(self.root)])
        return buf.getvalue().splitlines()

    def test_a_separating_verdict_also_says_it_is_not_a_significance_test(self):
        for name, date, hits in (("trigger-2026-10-01.json", "2026-10-01", 6),
                                 ("trigger-2026-10-05.json", "2026-10-05", 27)):
            fx.write_json(self.root, f"evals/results/{name}",
                          fx.trigger_record(date,
                                            fx.numbered_cases(30, hits)))
        (trend,) = [ln for ln in self.lines() if " trigger trend set " in ln]
        self.assertIn("; intervals do not overlap (descriptive, not a "
                      "significance test) (", trend)

    def test_a_charter_spread_says_the_sensitive_case_may_differ(self):
        for name, sensitive in (("charter-2026-09-28.json", "x"),
                                ("charter-2026-09-28-2.json", "y")):
            results = [(i, "swe", "sensitive" if i == sensitive
                        else "inconclusive") for i in "xy"]
            fx.write_json(self.root, f"evals/results/{name}",
                          fx.charter_record("2026-09-28", results))
        (spread,) = [ln for ln in self.lines()
                     if "charter rerun spread" in ln]
        self.assertIn("sensitive 1..1 of 2 over 2 run(s)", spread)
        self.assertTrue(spread.endswith(
            "; counts only, the sensitive case may differ between runs"))


if __name__ == "__main__":
    unittest.main()
