"""factory_config.py (the ADR-0034/0037 factory-config seam) —
pure-function + fixture tests.

Same discipline as test_assembler: every accessor is exercised through its
public interface and tests assert the EXACT problem strings callers will
print. The resolver classes here absorbed the tests that used to live
beside each accessor's old home: TestResolveModel (test_assembler),
TestResolveBudget (test_budget_guard), TestResolveCap (test_cost_report) —
one schema, one home, one test file.
"""
import json
import tempfile
import unittest
from pathlib import Path

import factory_config

CONFIG = {
    "budgets_usd": {"S": 5, "M": 15, "L": 40},
    "routing": {"mechanical": "claude-haiku-4-5",
                "implementation": "claude-sonnet-5",
                "architecture_review": "claude-fable-5"},
    "wip_cap": 3,
    "monthly_cap_usd": 300,
}


class TestLoad(unittest.TestCase):
    def write(self, root, rel, text):
        path = Path(root) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_loads_the_template_payload_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "factory/templates/factory.json",
                       json.dumps(CONFIG))
            self.assertEqual(factory_config.load(tmp), (CONFIG, []))

    def test_an_installed_config_wins_over_the_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            installed = dict(CONFIG, monthly_cap_usd=50)
            self.write(tmp, ".github/factory.json", json.dumps(installed))
            self.write(tmp, "factory/templates/factory.json",
                       json.dumps(CONFIG))
            config, problems = factory_config.load(tmp)
            self.assertEqual(problems, [])
            self.assertEqual(config["monthly_cap_usd"], 50)

    def test_a_missing_config_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(factory_config.load(tmp), (None, [
                "config: missing factory.json (.github/factory.json or"
                " factory/templates/factory.json)"]))

    def test_invalid_json_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, ".github/factory.json", "not json")
            config, problems = factory_config.load(tmp)
            self.assertIsNone(config)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                "config: .github/factory.json is not valid JSON:"), problems)


class TestResolveModel(unittest.TestCase):
    """band -> model through the repo's factory.json routing table, the
    single routing source of truth (ADR-0004/0034)."""

    def test_each_band_resolves_to_its_model(self):
        for band, model in (("mechanical", "claude-haiku-4-5"),
                            ("implementation", "claude-sonnet-5"),
                            ("architecture_review", "claude-fable-5")):
            self.assertEqual(factory_config.resolve_model(band, CONFIG),
                             (model, []), band)

    def test_a_band_the_table_does_not_route_is_a_problem(self):
        self.assertEqual(
            factory_config.resolve_model("mechanical", {"routing": {}}),
            (None, ["config: factory.json routes no model to the"
                    " mechanical band"]))

    def test_a_config_without_a_routing_table_is_a_problem(self):
        self.assertEqual(
            factory_config.resolve_model("implementation", {}),
            (None, ["config: factory.json has no routing table"]))


class TestResolveBudget(unittest.TestCase):
    def test_each_size_resolves_to_its_dollar_ceiling(self):
        for size, dollars in (("S", 5), ("M", 15), ("L", 40)):
            self.assertEqual(factory_config.resolve_budget(size, CONFIG),
                             (dollars, []), size)

    def test_an_uncovered_size_is_a_problem(self):
        self.assertEqual(
            factory_config.resolve_budget("XL", CONFIG),
            (None, ["config: factory.json names no positive budget for size"
                    " 'XL'"]))

    def test_a_config_without_a_budgets_table_is_a_problem(self):
        self.assertEqual(
            factory_config.resolve_budget("S", {}),
            (None, ["config: factory.json has no budgets_usd table"]))

    def test_a_non_positive_budget_is_a_problem(self):
        self.assertEqual(
            factory_config.resolve_budget("S", {"budgets_usd": {"S": 0}}),
            (None, ["config: factory.json names no positive budget for size"
                    " 'S'"]))

    def test_a_bool_budget_is_a_problem(self):
        # bool is an int subclass in Python; True/False must not pass as $.
        self.assertEqual(
            factory_config.resolve_budget("S", {"budgets_usd": {"S": True}}),
            (None, ["config: factory.json names no positive budget for size"
                    " 'S'"]))


class TestResolveCap(unittest.TestCase):
    def test_resolves_the_configured_cap(self):
        self.assertEqual(factory_config.resolve_cap(CONFIG), (300, []))

    def test_a_config_without_a_cap_is_a_problem(self):
        self.assertEqual(
            factory_config.resolve_cap({}),
            (None, ["config: factory.json names no positive"
                    " monthly_cap_usd"]))

    def test_a_non_positive_cap_is_a_problem(self):
        self.assertEqual(
            factory_config.resolve_cap({"monthly_cap_usd": 0}),
            (None, ["config: factory.json names no positive"
                    " monthly_cap_usd"]))

    def test_a_bool_cap_is_a_problem(self):
        # bool is an int subclass in Python; True/False must not pass as $.
        self.assertEqual(
            factory_config.resolve_cap({"monthly_cap_usd": True}),
            (None, ["config: factory.json names no positive"
                    " monthly_cap_usd"]))


if __name__ == "__main__":
    unittest.main()
