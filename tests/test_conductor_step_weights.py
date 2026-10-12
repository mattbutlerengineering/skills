"""Weighted step ceilings (issue #724): an item's size estimate is
split across its steps by weight, not evenly. The spec step writes
every stage artifact from idea to breakdown at the top band, and an
even $3 share of a size-M item ran out of budget 3 times out of 3.
The default weights live in factory_config; factory.json's optional
conductor.step_weights overrides a step's weight. Tests assert the
EXACT ceilings and problem strings.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import conductor_plan
import conductor_run
import factory_config

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_plan import AGENTS, CONFIG, issue  # noqa: E402

ZERO = {"prd": 0, "adr": 0, "wo": 0}
WEIGHT_PROBLEM = "conductor.step_weights.spec must be a positive number"


def plan(issues, config=CONFIG):
    return conductor_plan.plan_batch(issues, "matt", config, 0.0, ZERO,
                                     AGENTS)


def ceilings(item):
    return [(s["step"], s["ceiling_usd"]) for s in item["steps"]]


def weighted(**weights):
    return dict(CONFIG, conductor={"step_weights": weights})


class TestDefaultWeights(unittest.TestCase):
    def test_the_default_gives_spec_three_shares(self):
        self.assertEqual(factory_config.resolve_step_weights({}), (
            {"spec": 3, "build": 1, "verify": 1, "review": 1, "ship": 1},
            []))

    def test_a_feature_items_spec_gets_the_larger_share(self):
        result, problems = plan([issue(12)])
        self.assertEqual(problems, [])
        self.assertEqual(ceilings(result["items"][0]), [
            ("spec", 6.44), ("build", 2.14), ("verify", 2.14),
            ("review", 2.14), ("ship", 2.14)])

    def test_the_ceilings_sum_to_the_item_estimate(self):
        for labels in (("type:feature", "size:M"), ("type:defect", "size:S"),
                       ("type:chore", "size:L"),
                       ("wo:ready-for-agent", "size:M")):
            with self.subTest(labels=labels):
                result, _ = plan([issue(1, labels)])
                item = result["items"][0]
                self.assertAlmostEqual(
                    sum(s["ceiling_usd"] for s in item["steps"]),
                    item["estimate_usd"], places=9)

    def test_an_order_with_no_spec_splits_evenly(self):
        result, _ = plan([issue(1, ("wo:ready-for-agent", "size:M"))])
        self.assertEqual(ceilings(result["items"][0]), [
            ("build", 3.75), ("verify", 3.75), ("review", 3.75),
            ("ship", 3.75)])

    def test_the_batch_estimate_stays_the_size_budget(self):
        result, _ = plan([issue(1), issue(2, ("type:defect", "size:S"))])
        self.assertEqual(result["estimate_usd"], 20)
        self.assertEqual([i["estimate_usd"] for i in result["items"]],
                         [15, 5])

    def test_the_plan_line_shows_the_spec_share(self):
        result, _ = plan([issue(12)])
        lines = conductor_plan.compose_plan(result)
        self.assertEqual(lines[2], "    spec    architect  architecture_review"
                         "  fable  high  $6.44")
        self.assertEqual(lines[3], "    build   swe        implementation     "
                         "  sonnet  medium  $2.14")


class TestConfiguredWeights(unittest.TestCase):
    def test_a_configured_weight_replaces_that_steps_default(self):
        self.assertEqual(factory_config.resolve_step_weights(
            {"conductor": {"step_weights": {"spec": 1, "build": 2.5}}}),
            ({"spec": 1, "build": 2.5, "verify": 1, "review": 1,
              "ship": 1}, []))

    def test_equal_weights_restore_the_even_split(self):
        result, problems = plan([issue(12)], weighted(spec=1))
        self.assertEqual(problems, [])
        self.assertEqual(ceilings(result["items"][0]), [
            ("spec", 3.0), ("build", 3.0), ("verify", 3.0),
            ("review", 3.0), ("ship", 3.0)])

    def test_a_malformed_table_is_an_exact_problem(self):
        for table, problem in (
                ([3], "conductor.step_weights must map spec, build, verify,"
                      " review or ship to positive numbers"),
                ({"plan": 2, "deploy": 1},
                 "conductor.step_weights has unknown step(s): deploy, plan"),
                ({"spec": 0}, WEIGHT_PROBLEM),
                ({"spec": -1}, WEIGHT_PROBLEM),
                ({"spec": True}, WEIGHT_PROBLEM),
                ({"spec": "3"}, WEIGHT_PROBLEM)):
            with self.subTest(table=table):
                self.assertEqual(factory_config.config_problems(
                    {"wip_cap": 1, "monthly_cap_usd": 1,
                     "conductor": {"step_weights": table}}), [problem])
                self.assertEqual(factory_config.resolve_step_weights(
                    {"conductor": {"step_weights": table}}),
                    (None, [f"config: factory.json {problem}"]))

    def test_detector_f_reports_a_bad_table(self):
        import gates
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(json.dumps(
                weighted(spec=0)))
            self.assertEqual(gates.check_config_shape(Path(tmp)), [
                f"F: .github/factory.json {WEIGHT_PROBLEM}"])

    def test_a_bad_table_plans_nothing(self):
        self.assertEqual(plan([issue(1)], weighted(spec=0)),
                         (None, [f"config: factory.json {WEIGHT_PROBLEM}"]))


class TestSpecBrief(unittest.TestCase):
    """Run 1 of batch b20261012 committed a whole blueprint and lost it
    to a missing pr-body.md: the spec brief says to keep it current."""

    def brief(self, step):
        return conductor_run.compose_brief(
            step, "#12", "feature", "/wt", "conductor/b1/12", {}, None,
            None, "BODY", 6.44)

    def test_a_spec_brief_says_to_write_the_pr_body_before_the_ceiling(self):
        self.assertIn(
            "Keep the pull request body in pr-body.md current as each"
            " artifact is committed, and stop once the breakdown is"
            " committed: a run that reaches its $6.44 ceiling without"
            " pr-body.md opens no pull request.", self.brief("spec"))

    def test_other_briefs_do_not_carry_it(self):
        self.assertNotIn("Keep the pull request body", self.brief("build"))


if __name__ == "__main__":
    unittest.main()
