"""Per-skill precision/recall/F1 derived from summarize()'s confusion
matrix — a second pass over already-recorded results, never a re-run
(docs/research/eval-and-memory.md shortlist item 5).

Pure arithmetic over a dict, so every test feeds a fixture confusion
matrix (or a fixture results record) and asserts the numbers. The
zero-denominator contract is pinned explicitly: an undefined ratio is
None, never a silent 0.0 that would read as "measured and failed".
"""
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from trigger_eval import main, metrics_report, skill_metrics  # noqa: E402

# expected -> fired, in summarize()'s shape.
CONFUSION = {
    "prd": {"prd": 3, "none": 1},
    "idea": {"idea": 1, "prd": 1},
    "none": {"none": 2, "idea": 2},
    "ux-design": {"mermaid": 3},
}


class TestSkillMetrics(unittest.TestCase):
    def setUp(self):
        self.metrics = skill_metrics(CONFUSION)

    def test_none_is_the_negative_class_not_a_skill(self):
        self.assertEqual(sorted(self.metrics),
                         ["idea", "mermaid", "prd", "ux-design"])

    def test_counts_read_rows_as_expected_and_columns_as_fired(self):
        self.assertEqual(
            {k: self.metrics["prd"][k] for k in ("tp", "fp", "fn")},
            {"tp": 3, "fp": 1, "fn": 1})
        self.assertEqual(
            {k: self.metrics["idea"][k] for k in ("tp", "fp", "fn")},
            {"tp": 1, "fp": 2, "fn": 1})

    def test_precision_recall_f1(self):
        prd = self.metrics["prd"]
        self.assertAlmostEqual(prd["precision"], 0.75)
        self.assertAlmostEqual(prd["recall"], 0.75)
        self.assertAlmostEqual(prd["f1"], 0.75)
        idea = self.metrics["idea"]
        self.assertAlmostEqual(idea["precision"], 1 / 3)
        self.assertAlmostEqual(idea["recall"], 0.5)
        self.assertAlmostEqual(idea["f1"], 0.4)

    def test_never_fired_skill_has_undefined_precision(self):
        ux = self.metrics["ux-design"]
        self.assertEqual((ux["tp"], ux["fp"], ux["fn"]), (0, 0, 3))
        self.assertIsNone(ux["precision"])
        self.assertEqual(ux["recall"], 0.0)
        self.assertIsNone(ux["f1"])

    def test_never_expected_skill_has_undefined_recall(self):
        mermaid = self.metrics["mermaid"]
        self.assertEqual((mermaid["tp"], mermaid["fp"], mermaid["fn"]),
                         (0, 3, 0))
        self.assertEqual(mermaid["precision"], 0.0)
        self.assertIsNone(mermaid["recall"])
        self.assertIsNone(mermaid["f1"])

    def test_zero_precision_and_recall_gives_zero_f1(self):
        metrics = skill_metrics({"a": {"b": 1}, "b": {"a": 1}})
        self.assertEqual(metrics["a"]["precision"], 0.0)
        self.assertEqual(metrics["a"]["recall"], 0.0)
        self.assertEqual(metrics["a"]["f1"], 0.0)

    def test_empty_confusion_gives_no_skills(self):
        self.assertEqual(skill_metrics({}), {})

    def test_input_is_not_mutated(self):
        confusion = {"prd": {"prd": 1}}
        skill_metrics(confusion)
        self.assertEqual(confusion, {"prd": {"prd": 1}})


def result(case_id, kind, expected, fired):
    return {"id": case_id, "kind": kind, "expected": expected,
            "query": "q", "fired": fired, "runs": sum(fired.values()),
            "errors": 0, "correct_rate": 0.0, "pass": False}


class TestMetricsReport(unittest.TestCase):
    OUTPUT = {"results": [
        result("nm-1", "near-miss", "prd", {"prd": 1, "none": 2}),
        result("nm-2", "near-miss", "ux-design", {"mermaid": 3}),
        result("nm-3", "near-miss", None, {"none": 3}),
        result("d-1", "direct", "prd", {"prd": 3}),
    ]}

    def test_whole_record_micro_recall(self):
        lines = metrics_report(self.OUTPUT)
        self.assertIn("micro recall: 4/9 = 0.444", lines)

    def test_kind_filter_recomputes_confusion_from_that_kind_only(self):
        lines = metrics_report(self.OUTPUT, kind="near-miss")
        self.assertEqual(lines[0], "kind: near-miss (3 case(s))")
        self.assertIn("micro recall: 1/6 = 0.167", lines)
        self.assertIn("  prd: tp=1 fp=0 fn=2 precision=1.000 "
                      "recall=0.333 f1=0.500", lines)
        self.assertIn("  ux-design: tp=0 fp=0 fn=3 precision=n/a "
                      "recall=0.000 f1=n/a", lines)

    def test_unknown_kind_reports_no_cases(self):
        self.assertEqual(metrics_report(self.OUTPUT, kind="router"),
                         ["kind: router (0 case(s))",
                          "micro recall: n/a (no skill-expected runs)"])


class TestMetricsCli(unittest.TestCase):
    """--metrics reads a recorded file and runs nothing — the only way the
    verb touches evals/results/ is a read."""

    def run_main(self, argv):
        out, err = StringIO(), StringIO()
        # main() is bare (the factory verb table routes it so, ADR-0054),
        # so the argv goes where it reads it.
        with mock.patch.object(sys, "argv", ["trigger_eval.py", *argv]), \
                redirect_stdout(out), redirect_stderr(err):
            code = main()
        return code, out.getvalue(), err.getvalue()

    def test_prints_the_report_for_a_recorded_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trigger-omp-2026-07-05.json"
            record = {"harness": "omp", **TestMetricsReport.OUTPUT}
            path.write_text(json.dumps(record), encoding="utf-8")
            before = path.read_bytes()
            code, out, _ = self.run_main(
                ["--metrics", str(path), "--kind", "near-miss"])
            self.assertEqual(path.read_bytes(), before)
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[:3], [
            "trigger-omp-2026-07-05.json (harness: omp)",
            "kind: near-miss (3 case(s))",
            "micro recall: 1/6 = 0.167"])

    def test_unreadable_file_exits_nonzero_with_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent.json"
            code, out, err = self.run_main(["--metrics", str(missing)])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("error: cannot read results file", err)


if __name__ == "__main__":
    unittest.main()
