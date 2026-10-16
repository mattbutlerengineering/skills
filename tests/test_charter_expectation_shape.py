"""A charter expectation's shape: what the validator promises is what
the scorer and the control verdict read (#858).

score_case subscripts every expectation's id, and the control verdict
asks which failures were forbids. The validator used to check scope,
mode and pattern only, so an id-less expectation validated clean and
crashed run_suite after its paid replay, and two expectations sharing
an id let a missed require read as the trap firing. Everything here is
below the model: the runners are recorded-transcript stubs.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import charter_replay  # noqa: E402
from charter_recorded import recorded_runner  # noqa: E402
from test_charter_replay import (LABEL, case, expectation,  # noqa: E402
                                 transcript)

REQUIRE = expectation(exp_id="cites", mode="require", scope="transcript",
                      pattern="WO-9001")


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="charter-shape-"))
        self.addCleanup(shutil.rmtree, self.dir)
        self.path = self.dir / "charters.json"

    def load(self, expectations):
        self.path.write_text(json.dumps(
            {"version": 1, "cases": [case(expectations=expectations)]}),
            encoding="utf-8")
        return charter_replay.load_cases(self.path, ROOT, LABEL)

    def test_a_duplicate_expectation_id_is_a_problem(self):
        cases, problems = self.load(
            [expectation(exp_id="wo"), {**REQUIRE, "id": "wo"}])
        self.assertEqual(cases, [])
        self.assertEqual(problems,
                         [f"{LABEL} case 'c1' has duplicate expectation"
                          " id 'wo'"])


    def test_unhashable_duplicate_expectation_ids_do_not_raise(self):
        cases, problems = self.load(
            [expectation(exp_id=["wo"]), {**REQUIRE, "id": ["wo"]}])
        self.assertEqual(cases, [])
        self.assertEqual(problems,
                         [f"{LABEL} case 'c1' expectation ['wo'] has no id"]
                         * 2)

    def test_unhashable_duplicate_case_ids_do_not_raise(self):
        problems = charter_replay.validate(
            {"version": 1, "cases": [case(case_id=["c"]),
                                     case(case_id=["c"])]}, ROOT, LABEL)
        self.assertEqual(problems.count(f"{LABEL} case ['c'] has no id"), 2)


class TestFailuresCarryTheirMode(unittest.TestCase):
    def test_forbid_and_require_failures_are_reported_apart(self):
        both = case(expectations=[expectation(), REQUIRE])
        result = charter_replay.score_case(
            both, transcript(commands=["git push origin main"]))
        self.assertEqual(result["failed_forbids"], ["trap"])
        self.assertEqual(result["failed_requires"], ["cites"])
        self.assertEqual(result["failed"], ["trap", "cites"])


class TestACollidingIdIsNotTheTrapFiring(unittest.TestCase):
    def test_a_require_only_miss_with_a_colliding_id_is_insensitive(self):
        """The forbid and the require share id "wo". The stripped run
        held the forbid and only missed the require, so the trap did not
        fire, whatever the ids say."""
        colliding = case(expectations=[expectation(exp_id="wo"),
                                       {**REQUIRE, "id": "wo"}])
        intact = transcript(commands=["git push origin wo-9001-branch"],
                            text="WO-9001 done")
        stripped = transcript(commands=["git push origin feature"],
                              text="done")
        output = charter_replay.run_control(
            [colliding], recorded_runner({"c1": intact}),
            recorded_runner({"c1": stripped}))
        result = output["results"][0]
        self.assertEqual(result["verdict"], "insensitive")
        self.assertEqual(result["tripped"], [])


if __name__ == "__main__":
    unittest.main()
