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

    def test_missing_id(self):
        # The runner subscripts case["id"] everywhere it reports; an
        # id-less case must be refused here with lint's diagnostics, not
        # surface as a KeyError mid-run (ADR-0022's whole point)
        data = valid_data()
        del data["cases"][0]["id"]
        problems = eval_schema.validate(data, SKILLS, LABEL)
        self.assertIn("evals/routing.json case None has no id", problems)

    def test_falsy_present_id_is_a_value_not_a_gap(self):
        # id 0 mirrors validate_output's is-None handling
        data = valid_data()
        data["cases"][0]["id"] = 0
        self.assertNotIn("evals/routing.json case 0 has no id",
                         eval_schema.validate(data, SKILLS, LABEL))

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

    def test_null_cases_is_diagnosed_not_crashed(self):
        problems = eval_schema.validate(
            {"version": 1, "cases": None}, SKILLS, LABEL)
        self.assertIn("evals/routing.json cases is not a list", problems)

    def test_non_object_case_entry_is_diagnosed_not_crashed(self):
        problems = eval_schema.validate(
            {"version": 1, "cases": ["oops"]}, SKILLS, LABEL)
        self.assertIn("evals/routing.json cases entry #0 is not an object",
                      problems)

    def test_mixed_none_and_string_duplicate_ids_sort_safely(self):
        # two id-less cases put None in the duplicate set alongside a
        # duplicated string id — sorted() must not compare None < str
        data = valid_data()
        data["cases"][1]["id"] = data["cases"][0]["id"]
        data["cases"] += [{}, {}]
        problems = eval_schema.validate(data, SKILLS, LABEL)
        self.assertIn("evals/routing.json has duplicate case id 'next-0'",
                      problems)
        self.assertIn("evals/routing.json has duplicate case id None",
                      problems)


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

    def test_null_evals_is_diagnosed_not_crashed(self):
        problems = eval_schema.validate_output(
            {"skill_name": "decompose", "evals": None}, "decompose",
            self.LABEL)
        self.assertIn("evals/output/idea.json evals is not a list", problems)

    def test_non_object_eval_entry_is_diagnosed_not_crashed(self):
        data = valid_output_data()
        data["evals"] = ["oops"]
        problems = eval_schema.validate_output(data, "idea", self.LABEL)
        self.assertIn(
            "evals/output/idea.json evals entry #0 is not an object",
            problems)


class TestFixtureRefs(unittest.TestCase):
    """The output-eval record shape belongs to eval_schema (ADR-0024);
    fixture_refs is the accessor that keeps callers (the lint's
    fixture-existence check) from reaching into records by string key."""

    def test_yields_id_and_fixture_per_record(self):
        data = {"evals": [valid_output_record(),
                          valid_output_record(id=2, run_fixture="evals/g")]}
        self.assertEqual(eval_schema.fixture_refs(data),
                         [(1, "evals/fixtures/f"), (2, "evals/g")])

    def test_records_without_a_fixture_are_skipped(self):
        # absent and empty both mean "no fixture to check" — matching
        # _output_field_missing, where validate_output owns the complaint
        data = {"evals": [valid_output_record(run_fixture=None),
                          valid_output_record(id=2, run_fixture="")]}
        self.assertEqual(eval_schema.fixture_refs(data), [])

    def test_missing_id_is_carried_as_none(self):
        record = valid_output_record()
        del record["id"]
        self.assertEqual(eval_schema.fixture_refs({"evals": [record]}),
                         [(None, "evals/fixtures/f")])

    def test_malformed_shapes_yield_nothing(self):
        # shape complaints belong to validate_output; the accessor just
        # never crashes on what validate_output will already flag
        for data in ({}, {"evals": None}, {"evals": "oops"},
                     {"evals": ["oops"]}):
            with self.subTest(data=data):
                self.assertEqual(eval_schema.fixture_refs(data), [])


class TestResultsPath(unittest.TestCase):
    """One owner for the append-only results naming grammar: trigger runs
    as trigger-<date>[-N].json, output gradings as output/<slug>-<date>[-N]/,
    -N starting at 2 on same-day collision."""

    def setUp(self):
        self.results = Path(tempfile.mkdtemp(prefix="results-naming-"))
        self.addCleanup(shutil.rmtree, self.results)

    def test_trigger_no_collision_is_unsuffixed(self):
        self.assertEqual(
            eval_schema.results_path(self.results, "trigger", "2026-07-02"),
            self.results / "trigger-2026-07-02.json")

    def test_trigger_collisions_suffix_from_2(self):
        (self.results / "trigger-2026-07-02.json").write_text(
            "{}", encoding="utf-8")
        self.assertEqual(
            eval_schema.results_path(self.results, "trigger", "2026-07-02"),
            self.results / "trigger-2026-07-02-2.json")
        (self.results / "trigger-2026-07-02-2.json").write_text(
            "{}", encoding="utf-8")
        self.assertEqual(
            eval_schema.results_path(self.results, "trigger", "2026-07-02"),
            self.results / "trigger-2026-07-02-3.json")

    def test_output_no_collision_is_unsuffixed_dir(self):
        self.assertEqual(
            eval_schema.results_path(self.results, "output", "2026-07-02",
                                     slug="decompose"),
            self.results / "output" / "decompose-2026-07-02")

    def test_output_collision_suffixes_from_2(self):
        (self.results / "output" / "decompose-2026-07-02").mkdir(parents=True)
        self.assertEqual(
            eval_schema.results_path(self.results, "output", "2026-07-02",
                                     slug="decompose"),
            self.results / "output" / "decompose-2026-07-02-2")

    def test_charter_replay_snapshot_is_dated_and_suffixed(self):
        """charter_replay.py records through the same grammar (WO-0016)."""
        self.assertEqual(
            eval_schema.results_path(self.results, "charter", "2026-07-12"),
            self.results / "charter-2026-07-12.json")
        (self.results / "charter-2026-07-12.json").write_text(
            "{}", encoding="utf-8")
        self.assertEqual(
            eval_schema.results_path(self.results, "charter", "2026-07-12"),
            self.results / "charter-2026-07-12-2.json")

    def test_output_without_slug_fails_loud(self):
        with self.assertRaises(ValueError):
            eval_schema.results_path(self.results, "output", "2026-07-02")

    def test_unknown_kind_fails_loud(self):
        with self.assertRaises(ValueError):
            eval_schema.results_path(self.results, "routing", "2026-07-02")

    def test_omp_harness_marks_the_trigger_stem(self):
        self.assertEqual(
            eval_schema.results_path(self.results, "trigger", "2026-07-02",
                                     harness="omp"),
            self.results / "trigger-omp-2026-07-02.json")

    def test_omp_collisions_suffix_from_2_without_touching_claude(self):
        (self.results / "trigger-omp-2026-07-02.json").write_text(
            "{}", encoding="utf-8")
        self.assertEqual(
            eval_schema.results_path(self.results, "trigger", "2026-07-02",
                                     harness="omp"),
            self.results / "trigger-omp-2026-07-02-2.json")
        # the same-day claude stem is a different name, so no collision
        self.assertEqual(
            eval_schema.results_path(self.results, "trigger", "2026-07-02",
                                     harness="claude"),
            self.results / "trigger-2026-07-02.json")

    def test_claude_harness_stays_unmarked(self):
        self.assertEqual(
            eval_schema.results_path(self.results, "trigger", "2026-07-02",
                                     harness="claude"),
            self.results / "trigger-2026-07-02.json")

    def test_unknown_harness_fails_loud(self):
        with self.assertRaises(ValueError):
            eval_schema.results_path(self.results, "trigger", "2026-07-02",
                                     harness="opencode")


class TestResultsGrammarRoundTrip(unittest.TestCase):
    """The '-N starts at 2' collision rule is encoded twice inside this
    module — the _SUFFIX regex (validator side) and the results_path
    counter (generator side). This round-trip pins them together: every
    path the generator mints must be a link the validator accepts."""

    def setUp(self):
        self.results = Path(tempfile.mkdtemp(prefix="results-roundtrip-"))
        self.addCleanup(shutil.rmtree, self.results)

    def link(self, path):
        return f"evals/results/{path.relative_to(self.results).as_posix()}"

    def test_generated_trigger_paths_validate_through_collisions(self):
        for _ in range(3):  # unsuffixed, -2, -3
            path = eval_schema.results_path(self.results, "trigger",
                                            "2026-07-21")
            path.write_text("{}", encoding="utf-8")
            self.assertTrue(eval_schema.valid_results_link(self.link(path)),
                            self.link(path))

    def test_a_generated_output_grading_validates(self):
        path = eval_schema.results_path(self.results, "output",
                                        "2026-07-21", slug="idea")
        link = self.link(path) + "/grading.json"
        self.assertTrue(eval_schema.valid_results_link(link), link)


class TestValidResultsLink(unittest.TestCase):
    """LEDGER evidence links must follow the results naming grammar, not
    merely sit under evals/results/ (the lint validates through this)."""

    def test_trigger_links_with_and_without_suffix_are_valid(self):
        for target in ("evals/results/trigger-2026-07-01.json",
                       "evals/results/trigger-2026-07-01-2.json"):
            with self.subTest(target=target):
                self.assertTrue(eval_schema.valid_results_link(target))

    def test_output_grading_links_are_valid(self):
        for target in (
                "evals/results/output/decompose-2026-07-01/grading.json",
                "evals/results/output/decompose-2026-07-01-2/grading.json"):
            with self.subTest(target=target):
                self.assertTrue(eval_schema.valid_results_link(target))

    def test_omp_trigger_links_with_and_without_suffix_are_valid(self):
        for target in ("evals/results/trigger-omp-2026-07-01.json",
                       "evals/results/trigger-omp-2026-07-01-2.json"):
            with self.subTest(target=target):
                self.assertTrue(eval_schema.valid_results_link(target))

    def test_off_grammar_links_are_invalid(self):
        for target in (
                "evals/results/output",                # bare directory
                "evals/results/notes.md",              # arbitrary file
                "evals/results/trigger-2026-07-01",    # missing .json
                "evals/results/output/decompose-2026-07-01",  # no grading.json
                "evals/results/trigger-July-1.json",   # not an ISO date
                "evals/results/trigger-2026-07-01-1.json",   # -N starts at 2
                "evals/results/trigger-2026-07-01-0.json",
                # claude is the unmarked primary; unknown harness tokens
                # are off-grammar too
                "evals/results/trigger-claude-2026-07-01.json",
                "evals/results/trigger-opencode-2026-07-01.json",
                "evals/results/output/decompose-2026-07-01-007/grading.json"):
            with self.subTest(target=target):
                self.assertFalse(eval_schema.valid_results_link(target))


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


# Everything json.loads can return at a file's top level that is not an
# object. A file may legally hold any of these, so every validator has to
# survive them.
NON_OBJECTS = (None, 0, 5, True, False, "", "version", [], ["version"],
               [{"id": "x"}])


class TestNonObjectPayloads(unittest.TestCase):
    """A file that parses to a non-object is a defect to report, not an
    exception to raise — `entries`' docstring states the contract for the
    whole module: "Validators return problem strings; they never raise."
    """

    def test_validate_reports_one_problem_and_does_not_raise(self):
        for payload in NON_OBJECTS:
            with self.subTest(payload=payload):
                self.assertEqual(
                    eval_schema.validate(payload, SKILLS, LABEL),
                    [f"{LABEL} is not a JSON object"])

    def test_validate_output_reports_one_problem_and_does_not_raise(self):
        for payload in NON_OBJECTS:
            with self.subTest(payload=payload):
                self.assertEqual(
                    eval_schema.validate_output(payload, "idea", LABEL),
                    [f"{LABEL} is not a JSON object"])

    def test_fixture_refs_yields_nothing_and_does_not_raise(self):
        # Its docstring already promises this: "malformed shapes yield
        # nothing rather than raising, mirroring entries".
        for payload in NON_OBJECTS:
            with self.subTest(payload=payload):
                self.assertEqual(eval_schema.fixture_refs(payload), [])

    def test_a_string_file_does_not_masquerade_as_a_coverage_failure(self):
        # The regression that motivated this: `"version" not in data` is a
        # substring test on a str, so the version gate passed and the run
        # continued into 26 derived coverage problems about a file whose
        # only real defect is its shape.
        problems = eval_schema.validate("version", SKILLS, LABEL)
        self.assertEqual(len(problems), 1, problems)
        self.assertNotIn("covers skill", problems[0])

    def test_load_refuses_a_non_object_file_without_raising(self):
        for text in ("null", "5", "true", '"version"', "[]"):
            with self.subTest(text=text):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "routing.json"
                    path.write_text(text, encoding="utf-8")
                    cases, problems = eval_schema.load(path, SKILLS, LABEL)
                    self.assertEqual(cases, [])
                    self.assertEqual(problems,
                                     [f"{LABEL} is not a JSON object"])



class TestLoadCaseSetGuardsItsValidators(unittest.TestCase):
    """The loader — not each validator — is what guarantees a validator
    receives an object.

    `load_case_set` is the shared entry point (the routing loader and
    charter_replay's `load_cases` are both thin callers), and it ends by
    reaching for `data.get("cases")`. A validator that does not itself
    reject a non-object therefore hands the loader a string or a list to
    call `.get` on. charter_replay's validator is exactly that: on a
    bare-string file it returns no problems at all, so the set reads as
    valid and the crash lands in the loader.
    """

    def load(self, text, validate):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            path.write_text(text, encoding="utf-8")
            return eval_schema.load_case_set(path, LABEL, validate)

    def test_a_permissive_validator_cannot_make_the_loader_raise(self):
        # Stands in for any validator that does not guard shape itself.
        for text in ("null", "5", "true", '"version"', "[]"):
            with self.subTest(text=text):
                cases, problems = self.load(text, lambda data: [])
                self.assertEqual(cases, [])
                self.assertEqual(problems,
                                 [f"{LABEL} is not a JSON object"])

    def test_the_validator_is_not_called_for_a_non_object(self):
        # The guard runs first, so a validator may assume an object.
        seen = []

        def validate(data):
            seen.append(data)
            return []

        cases, problems = self.load('"version"', validate)
        self.assertEqual(seen, [], "validator was handed a non-object")
        self.assertEqual(problems, [f"{LABEL} is not a JSON object"])

    def test_a_valid_object_still_reaches_the_validator(self):
        seen = []

        def validate(data):
            seen.append(data)
            return []

        cases, problems = self.load('{"cases": [{"id": "a"}]}', validate)
        self.assertEqual(problems, [])
        self.assertEqual(cases, [{"id": "a"}])
        self.assertEqual(seen, [{"cases": [{"id": "a"}]}])



if __name__ == "__main__":
    unittest.main()
