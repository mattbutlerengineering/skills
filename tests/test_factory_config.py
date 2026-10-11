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
import os
import sys
import tempfile
import unittest
from pathlib import Path

import factory_config

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling factory_fixture import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from factory_fixture import CONFIG, FixtureTree  # noqa: E402


class TestBands(unittest.TestCase):
    """The routing-band vocabulary's one home (ADR-0048): gates' detector
    F and the WO-0007 routing evidence read this tuple instead of
    restating it."""

    def test_the_three_bands_in_routing_order(self):
        self.assertEqual(factory_config.BANDS,
                         ("mechanical", "implementation",
                          "architecture_review"))


class TestArtifactPaths(unittest.TestCase):
    """The installed-vs-payload path grammar's one home (ADR-0048): each
    dual-home artifact's ordered candidate paths, installed first, with
    the payload-side .github/ asymmetry stated exactly once."""

    def test_factory_json_candidates_are_installed_first(self):
        root = Path("/repo")
        self.assertEqual(
            factory_config.artifact_paths(root, "factory.json"),
            ((root / ".github" / "factory.json", True),
             (root / "factory" / "templates" / "factory.json", False)))

    def test_labels_json_payload_home_keeps_its_github_segment(self):
        root = Path("/repo")
        self.assertEqual(
            factory_config.artifact_paths(root, "labels.json"),
            ((root / ".github" / "labels.json", True),
             (root / "factory" / "templates" / ".github" / "labels.json",
              False)))

    def test_a_string_root_is_accepted(self):
        paths = factory_config.artifact_paths("/repo", "factory.json")
        self.assertEqual(paths[0][0], Path("/repo/.github/factory.json"))


class TestLoad(unittest.TestCase):
    def test_loads_the_template_payload_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            FixtureTree(tmp).factory()
            self.assertEqual(factory_config.load(tmp), (CONFIG, []))

    def test_an_installed_config_wins_over_the_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            installed = dict(CONFIG, monthly_cap_usd=50)
            tree.write(".github/factory.json", json.dumps(installed))
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
            FixtureTree(tmp).write(".github/factory.json", "not json")
            config, problems = factory_config.load(tmp)
            self.assertIsNone(config)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                "config: .github/factory.json is not valid JSON:"), problems)

    def test_a_config_that_is_not_an_object_is_a_problem(self):
        """A JSON document's top level is legally an array, string,
        number, boolean or null. json.loads returns each untouched, and
        the seam's contract is (value, problems) — so a non-object must
        arrive as a problem, never as a `config` the accessors then
        subscript. Same fail-closed direction as the invalid-JSON case
        above, one step later in the same read."""
        for text in ("null", "[]", '"factory"', "5", "true"):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                FixtureTree(tmp).write(".github/factory.json", text)
                self.assertEqual(factory_config.load(tmp), (None, [
                    "config: .github/factory.json is not a JSON object"]))

    def test_a_non_object_config_never_reaches_an_accessor(self):
        """The contract the guard exists for: every accessor may assume
        `load` handed it an object. Before the guard, `null` came back as
        (None, []) — no problem at all — and the first accessor to touch
        it raised AttributeError inside a gate."""
        with tempfile.TemporaryDirectory() as tmp:
            FixtureTree(tmp).write(".github/factory.json", "null")
            config, problems = factory_config.load(tmp)
            self.assertIsNone(config)
            self.assertTrue(problems)

    def test_a_config_that_is_not_utf8_is_a_problem(self):
        # Valid JSON, invalid UTF-8 — what an editor saving latin-1
        # produces. A JSON document must be UTF-8 (RFC 8259 §8.1), so
        # the bytes are a defect in the document — the same problem as
        # text that will not parse, not a read failure (ADR-0075).
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".github" / "factory.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'{"routing": {"mechanical": "caf\xe9"}}')
            self.assertEqual(factory_config.load(tmp), (None, [
                "config: .github/factory.json is not valid JSON: 'utf-8'"
                " codec can't decode byte 0xe9 in position 31: invalid"
                " continuation byte"]))

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-000 file")
    def test_a_config_the_process_may_not_read_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = FixtureTree(tmp).write(".github/factory.json",
                                          json.dumps(CONFIG))
            path.chmod(0)
            try:
                self.assertEqual(factory_config.load(tmp), (None, [
                    "config: cannot read .github/factory.json: [Errno 13]"
                    f" Permission denied: '{path}'"]))
            finally:
                path.chmod(0o644)

    def test_an_empty_config_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            FixtureTree(tmp).write(".github/factory.json", "")
            self.assertEqual(factory_config.load(tmp), (None, [
                "config: .github/factory.json is not valid JSON:"
                " Expecting value: line 1 column 1 (char 0)"]))

    def test_a_broken_installed_config_is_reported_not_skipped(self):
        """First home wins (ADR-0048), broken or not: an installed copy
        that is present but does not parse is the result. It never falls
        through to a clean payload copy — the repo's own curated config
        would be silently replaced by the shipped default."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp).factory()
            tree.write(".github/factory.json", "{nope")
            self.assertEqual(factory_config.load(tmp), (None, [
                "config: .github/factory.json is not valid JSON:"
                " Expecting property name enclosed in double quotes:"
                " line 1 column 2 (char 1)"]))


class TestInfiniteAmountsAreRefused(unittest.TestCase):
    """An infinite cap cannot be crossed, so it is not a cap: `total >=
    inf` is false at every spend and the ADR-0034 breaker returns
    CONTINUE forever. json.loads accepts a bare Infinity literal, so
    this arrives straight from factory.json. cost_report.decide already
    refuses a non-finite SPEND for exactly this reason; the comparison
    has two sides."""

    def test_an_infinite_cap_does_not_resolve(self):
        cap, problems = factory_config.resolve_cap(
            {"monthly_cap_usd": float("inf")})
        self.assertIsNone(cap)
        self.assertEqual(problems, [
            "config: factory.json names no positive monthly_cap_usd"])

    def test_an_infinite_budget_does_not_resolve(self):
        budget, problems = factory_config.resolve_budget(
            "L", {"budgets_usd": {"S": 1, "M": 2, "L": float("inf")}})
        self.assertIsNone(budget)
        self.assertEqual(len(problems), 1)

    def test_config_problems_reports_infinite_amounts(self):
        # config_problems is what detector F prints, so an infinite
        # amount must not pass CI either.
        problems = factory_config.config_problems({
            "monthly_cap_usd": float("inf"),
            "budgets_usd": {"S": 1, "M": 2, "L": float("inf")},
            "routing": {band: "m" for band in factory_config.BANDS},
            "wip_cap": 2,
        })
        self.assertTrue(problems, "an infinite amount passed detector F")

    def test_finite_positives_are_unaffected(self):
        self.assertEqual(
            factory_config.resolve_cap({"monthly_cap_usd": 100}), (100, []))
        self.assertEqual(
            factory_config.resolve_budget(
                "M", {"budgets_usd": {"S": 1, "M": 2.5, "L": 9}}), (2.5, []))


class TestConfigProblems(unittest.TestCase):
    """The whole-config field grammar, owned here (twin of
    cost_ledger.line_problems): detector F prefixes these and layers its
    key-set cross-checks on top, so gate and runtime accessors can never
    diverge on what a valid field is."""

    def test_the_shipped_config_is_clean(self):
        self.assertEqual(factory_config.config_problems(CONFIG), [])

    def test_a_bool_budget_is_flagged(self):
        # True is an int in Python; the accessors reject it, so the
        # grammar must too — this was detector F's hole.
        config = dict(CONFIG, budgets_usd={"S": True, "M": 15, "L": 40})
        self.assertEqual(factory_config.config_problems(config),
                         ["budgets_usd.S must be a positive number"])

    def test_a_bool_cap_and_bool_wip_cap_are_flagged(self):
        config = dict(CONFIG, wip_cap=True, monthly_cap_usd=True)
        self.assertEqual(factory_config.config_problems(config),
                         ["wip_cap must be a positive integer",
                          "monthly_cap_usd must be a positive number"])

    def test_an_empty_routing_model_is_flagged(self):
        routing = dict(CONFIG["routing"], mechanical="")
        config = dict(CONFIG, routing=routing)
        self.assertEqual(factory_config.config_problems(config),
                         ["routing.mechanical must name a model id"])

    def test_key_set_completeness_stays_with_detector_f(self):
        # a missing size/band is the gate's whole-shape concern, not
        # field grammar — the accessors fail closed per lookup instead
        config = dict(CONFIG, budgets_usd={"S": 5})
        self.assertEqual(factory_config.config_problems(config), [])


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



class TestResolveEffort(unittest.TestCase):
    """band -> effort through factory.json's effort table, beside routing
    and fail-closed in resolve_model's shape (PRD-0013, architecture's
    Policy component)."""

    def test_each_band_resolves_to_its_shipped_effort(self):
        for band, effort in (("mechanical", "low"),
                             ("implementation", "medium"),
                             ("architecture_review", "high")):
            self.assertEqual(factory_config.resolve_effort(band, CONFIG),
                             (effort, []), band)

    def test_a_band_the_table_does_not_cover_is_a_problem(self):
        self.assertEqual(
            factory_config.resolve_effort("mechanical", {"effort": {}}),
            (None, ["config: factory.json names no effort for the"
                    " mechanical band"]))

    def test_an_effort_outside_the_vocabulary_is_a_problem(self):
        self.assertEqual(
            factory_config.resolve_effort(
                "mechanical", {"effort": {"mechanical": "extreme"}}),
            (None, ["config: factory.json names no effort for the"
                    " mechanical band"]))

    def test_a_config_without_an_effort_table_is_a_problem(self):
        self.assertEqual(
            factory_config.resolve_effort("implementation", {}),
            (None, ["config: factory.json has no effort table"]))


class TestEffortProblems(unittest.TestCase):
    def test_an_effort_outside_the_vocabulary_is_flagged(self):
        config = dict(CONFIG, effort=dict(CONFIG["effort"],
                                          mechanical="extreme"))
        self.assertEqual(factory_config.config_problems(config), [
            "effort.mechanical must be one of low, medium, high, xhigh,"
            " max"])

    def test_every_vocabulary_value_is_clean(self):
        for value in ("low", "medium", "high", "xhigh", "max"):
            config = dict(CONFIG, effort={"mechanical": value})
            self.assertEqual(factory_config.config_problems(config), [],
                             value)

    def test_an_absent_effort_table_is_silent(self):
        config = {key: value for key, value in CONFIG.items()
                  if key != "effort"}
        self.assertEqual(factory_config.config_problems(config), [])

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
