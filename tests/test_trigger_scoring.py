"""Trigger-eval scoring seam: the pure half of trigger_eval.py — case dicts
and fired-slug counts in, scored results, summary, and confusion matrix out.

No claude CLI, no subprocess. score_case/summarize are tested through the
interface run_eval uses after orchestration collects fired counts;
_match_slug is a private detection helper, tested directly because its
first-match contract is what turns stream text into a fired slug.
"""
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from trigger_eval import _match_slug, score_case, summarize  # noqa: E402


def case(case_id="c1", kind="direct", expected="prd", query="q"):
    return {"id": case_id, "kind": kind, "expected": expected, "query": query}


class TestMatchSlug(unittest.TestCase):
    NAMES = {"prd-skill-abc123": "prd", "idea-skill-abc123": "idea"}

    def test_match_inside_larger_text(self):
        self.assertEqual(
            _match_slug('{"skill": "prd-skill-abc123"}', self.NAMES), "prd")

    def test_no_match_returns_none(self):
        self.assertIsNone(_match_slug('{"skill": "unrelated"}', self.NAMES))

    def test_empty_text_returns_none(self):
        self.assertIsNone(_match_slug("", self.NAMES))


class TestScoreCase(unittest.TestCase):
    def test_all_runs_correct_passes(self):
        result = score_case(case(), Counter({"prd": 3}), 3, 0.5)
        self.assertTrue(result["pass"])
        self.assertEqual(result["correct_rate"], 1.0)

    def test_threshold_is_inclusive(self):
        # exactly at threshold passes: correct_rate >= threshold
        result = score_case(case(), Counter({"prd": 1, "none": 1}), 2, 0.5)
        self.assertTrue(result["pass"])

    def test_below_threshold_fails(self):
        result = score_case(case(), Counter({"prd": 1, "none": 2}), 3, 0.5)
        self.assertFalse(result["pass"])
        self.assertEqual(result["correct_rate"], 0.333)

    def test_wrong_skill_firing_is_not_correct(self):
        result = score_case(case(expected="prd"), Counter({"idea": 3}), 3, 0.5)
        self.assertFalse(result["pass"])
        self.assertEqual(result["correct_rate"], 0.0)

    def test_distractor_expected_null_passes_on_none(self):
        result = score_case(case(expected=None), Counter({"none": 3}), 3, 0.5)
        self.assertTrue(result["pass"])

    def test_distractor_expected_null_fails_when_skill_fires(self):
        result = score_case(case(expected=None),
                            Counter({"review": 2, "none": 1}), 3, 0.5)
        self.assertFalse(result["pass"])

    def test_zero_runs_scores_zero_and_fails(self):
        result = score_case(case(), Counter(), 0, 0.5)
        self.assertEqual(result["correct_rate"], 0.0)
        self.assertFalse(result["pass"])


class TestSummarize(unittest.TestCase):
    def results(self):
        return [
            score_case(case("a", "direct", "prd"), Counter({"prd": 3}), 3, 0.5),
            score_case(case("b", "direct", "idea"), Counter({"none": 3}), 3, 0.5),
            score_case(case("c", "near-miss", "idea"),
                       Counter({"idea": 2, "prd": 1}), 3, 0.5),
            score_case(case("d", "distractor", None), Counter({"none": 3}), 3, 0.5),
        ]

    def test_totals(self):
        summary = summarize(self.results())["summary"]
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["passed"], 3)
        self.assertEqual(summary["failed"], 1)

    def test_by_kind_rollup(self):
        by_kind = summarize(self.results())["summary"]["by_kind"]
        self.assertEqual(by_kind["direct"], {"total": 2, "passed": 1})
        self.assertEqual(by_kind["near-miss"], {"total": 1, "passed": 1})
        self.assertEqual(by_kind["distractor"], {"total": 1, "passed": 1})

    def test_by_skill_buckets_null_expected_as_none(self):
        by_skill = summarize(self.results())["summary"]["by_skill"]
        self.assertEqual(by_skill["none"], {"total": 1, "passed": 1})
        self.assertEqual(by_skill["idea"], {"total": 2, "passed": 1})

    def test_confusion_accumulates_fired_counts_per_expected(self):
        confusion = summarize(self.results())["confusion"]
        self.assertEqual(confusion["idea"], {"none": 3, "idea": 2, "prd": 1})
        self.assertEqual(confusion["prd"], {"prd": 3})
        self.assertEqual(confusion["none"], {"none": 3})


if __name__ == "__main__":
    unittest.main()
