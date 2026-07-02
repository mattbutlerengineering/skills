"""Eval-schema seam: the routing eval-set's kinds, case shape, and
load-plus-validate live in eval_schema; lint and the trigger-eval runner
are thin callers with identical diagnostics (ADR-0022).

validate/load are tested through the interface both callers use; the
runner's refusal path is pinned end-to-end (diagnostics on stderr, no
traceback) because that behavior — not the strings alone — is the
acceptance criterion.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import eval_schema  # noqa: E402

SKILLS = ["next", "idea", "prd"]
LABEL = "evals/routing.json"


def valid_cases():
    cases = [{"id": f"{slug}-{n}", "kind": "direct",
              "expected": slug, "query": "q"}
             for slug in SKILLS for n in range(3)]
    cases += [{"id": f"none-{n}", "kind": "distractor",
               "expected": None, "query": "q"} for n in range(3)]
    return cases


def valid_data():
    return {"version": 1, "cases": valid_cases()}


class TestValidate(unittest.TestCase):
    def test_valid_set_has_no_problems(self):
        self.assertEqual(eval_schema.validate(valid_data(), SKILLS, LABEL), [])

    def test_missing_version_is_the_only_problem_reported(self):
        self.assertEqual(
            eval_schema.validate({"cases": []}, SKILLS, LABEL),
            ["evals/routing.json missing 'version' field"])

    def test_duplicate_case_id(self):
        data = valid_data()
        data["cases"][1]["id"] = data["cases"][0]["id"]
        problems = eval_schema.validate(data, SKILLS, LABEL)
        self.assertIn("evals/routing.json has duplicate case id 'next-0'",
                      problems)

    def test_invalid_expected(self):
        data = valid_data()
        data["cases"][0]["expected"] = "bogus"
        problems = eval_schema.validate(data, SKILLS, LABEL)
        self.assertIn("evals/routing.json case 'next-0' has invalid "
                      "expected 'bogus'", problems)

    def test_invalid_kind(self):
        data = valid_data()
        data["cases"][0]["kind"] = "sideways"
        problems = eval_schema.validate(data, SKILLS, LABEL)
        self.assertIn("evals/routing.json case 'next-0' has invalid "
                      "kind 'sideways'", problems)

    def test_missing_query(self):
        data = valid_data()
        del data["cases"][0]["query"]
        problems = eval_schema.validate(data, SKILLS, LABEL)
        self.assertIn("evals/routing.json case 'next-0' has no query",
                      problems)

    def test_thin_skill_coverage(self):
        data = valid_data()
        data["cases"] = [c for c in data["cases"] if c["id"] != "idea-0"]
        problems = eval_schema.validate(data, SKILLS, LABEL)
        self.assertIn("evals/routing.json covers skill 'idea' in only "
                      "2 case(s), need >= 3", problems)

    def test_thin_distractor_coverage(self):
        data = valid_data()
        data["cases"] = [c for c in data["cases"] if c["id"] != "none-0"]
        problems = eval_schema.validate(data, SKILLS, LABEL)
        self.assertIn("evals/routing.json has only 2 distractor case(s) "
                      "(expected: null), need >= 3", problems)

    def test_label_prefixes_every_problem(self):
        data = valid_data()
        data["cases"][0]["kind"] = "sideways"
        problems = eval_schema.validate(data, SKILLS, "other/set.json")
        self.assertEqual(
            [p for p in problems if not p.startswith("other/set.json")], [])


class TestLoad(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="eval-schema-"))
        self.addCleanup(shutil.rmtree, self.dir)
        self.path = self.dir / "routing.json"

    def test_valid_set_returns_cases_and_no_problems(self):
        self.path.write_text(json.dumps(valid_data()), encoding="utf-8")
        cases, problems = eval_schema.load(self.path, SKILLS, LABEL)
        self.assertEqual(problems, [])
        self.assertEqual(cases, valid_cases())

    def test_missing_file(self):
        cases, problems = eval_schema.load(self.path, SKILLS, LABEL)
        self.assertEqual(cases, [])
        self.assertEqual(problems, ["missing evals/routing.json"])

    def test_invalid_json(self):
        self.path.write_text("{nope", encoding="utf-8")
        cases, problems = eval_schema.load(self.path, SKILLS, LABEL)
        self.assertEqual(cases, [])
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            "evals/routing.json is not valid JSON: "))

    def test_invalid_set_returns_no_cases(self):
        self.path.write_text(json.dumps({"cases": []}), encoding="utf-8")
        cases, problems = eval_schema.load(self.path, SKILLS, LABEL)
        self.assertEqual(cases, [])
        self.assertEqual(problems,
                         ["evals/routing.json missing 'version' field"])


def valid_output_record(**overrides):
    record = {"id": 1, "prompt": "p", "run_fixture": "evals/fixtures/f",
              "run_scale": "feature:x", "expected_output": "o",
              "expectations": ["e"]}
    record.update(overrides)
    return record


def valid_output_data():
    return {"skill_name": "idea", "evals": [valid_output_record()]}


class TestValidateOutput(unittest.TestCase):
    LABEL = "evals/output/idea.json"

    def test_valid_set_has_no_problems(self):
        self.assertEqual(
            eval_schema.validate_output(valid_output_data(), "idea",
                                        self.LABEL), [])

    def test_every_documented_field_is_required(self):
        for field in eval_schema.OUTPUT_FIELDS:
            with self.subTest(field=field):
                data = valid_output_data()
                del data["evals"][0][field]
                problems = eval_schema.validate_output(data, "idea",
                                                       self.LABEL)
                expected_id = None if field == "id" else 1
                self.assertIn(f"evals/output/idea.json eval {expected_id!r} "
                              f"missing field: {field}", problems)

    def test_falsy_present_values_are_not_missing(self):
        # id 0 (or any falsy-but-present value) is a value, not a gap —
        # mirrors validate()'s is-None handling of expected
        data = valid_output_data()
        data["evals"][0]["id"] = 0
        self.assertEqual(
            eval_schema.validate_output(data, "idea", self.LABEL), [])

    def test_empty_expectations_counts_as_missing(self):
        data = valid_output_data()
        data["evals"][0]["expectations"] = []
        self.assertEqual(
            eval_schema.validate_output(data, "idea", self.LABEL),
            ["evals/output/idea.json eval 1 missing field: expectations"])

    def test_skill_name_mismatch(self):
        data = valid_output_data()
        data["skill_name"] = "prd"
        self.assertEqual(
            eval_schema.validate_output(data, "idea", self.LABEL),
            ["evals/output/idea.json skill_name is 'prd', expected 'idea'"])

    def test_duplicate_eval_ids(self):
        data = valid_output_data()
        data["evals"].append(valid_output_record())
        self.assertEqual(
            eval_schema.validate_output(data, "idea", self.LABEL),
            ["evals/output/idea.json has duplicate eval id 1"])

    def test_label_prefixes_every_problem(self):
        data = valid_output_data()
        data["skill_name"] = "prd"
        del data["evals"][0]["prompt"]
        problems = eval_schema.validate_output(data, "idea", "other.json")
        self.assertEqual(
            [p for p in problems if not p.startswith("other.json")], [])


class TestRunnerRefusesMalformedSet(unittest.TestCase):
    """The trigger-eval runner inherits eval_schema's diagnostics: a
    malformed set is refused with lint's problem strings on stderr and
    exit 1 — never a traceback."""

    def run_runner(self, eval_set_path):
        return subprocess.run(
            [sys.executable, str(ROOT / "trigger_eval.py"),
             "--eval-set", str(eval_set_path)],
            capture_output=True, text=True, timeout=60)

    def test_malformed_set_reports_lint_diagnostics_not_traceback(self):
        with tempfile.TemporaryDirectory(prefix="eval-schema-") as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps(
                {"version": 1,
                 "cases": [{"id": "c1", "kind": "sideways",
                            "expected": None}]}), encoding="utf-8")
            proc = self.run_runner(bad)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("case 'c1' has invalid kind 'sideways'", proc.stderr)
        self.assertIn("case 'c1' has no query", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_missing_set_reports_missing_not_traceback(self):
        proc = self.run_runner(Path("/nonexistent/routing.json"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("missing", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
