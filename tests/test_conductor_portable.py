"""The Conductor in a consumer repo (issue #678): the payload-portable
conductor. A stamped repo runs the mirrored tools/factory/conductor.py,
names its own gate command in factory.json (default `make check`, this
repo's), plans against a charter directory it names, and never bumps a
plugin version or regenerates a manifest it does not own. Every git,
gh and tool call goes through a fake or a scratch repo, and tests assert
the EXACT problem strings.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import conductor
import conductor_merge as merge
import conductor_run
import factory_config

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
import test_conductor_merge as tcm  # noqa: E402
from test_conductor_plan import (AGENTS, CONFIG, clock,  # noqa: E402
                                 fake_gh, fake_git, issue)
from test_conductor_run import Harness, RunCase, pr_body  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
GATE_PROBLEM = ("config: factory.json conductor.gate_command must be one"
                " command with no shell operators")


class TestGateCommandConfig(unittest.TestCase):
    def test_an_absent_gate_command_is_make_check(self):
        self.assertEqual(factory_config.resolve_gate_command({}),
                         (["make", "check"], []))

    def test_a_configured_gate_command_is_split_into_argv(self):
        self.assertEqual(factory_config.resolve_gate_command(
            {"conductor": {"gate_command": "npm run test:ci"}}),
            (["npm", "run", "test:ci"], []))

    def test_a_shell_pipeline_or_an_empty_command_is_refused(self):
        for command in ("make check && rm -rf x", "", "  ", 7,
                        "make check; true", "a | b", "echo $HOME"):
            with self.subTest(command=command):
                self.assertEqual(factory_config.resolve_gate_command(
                    {"conductor": {"gate_command": command}}),
                    (None, [GATE_PROBLEM]))

    def test_the_conductor_table_is_checked_by_config_problems(self):
        self.assertEqual(factory_config.config_problems(
            {"wip_cap": 1, "monthly_cap_usd": 1,
             "conductor": {"gate_command": "a && b", "gate_comand": "x"}}),
            ["conductor has unknown key(s): gate_comand",
             "conductor.gate_command must be one command with no shell"
             " operators"])
        self.assertEqual(factory_config.config_problems(
            {"wip_cap": 1, "monthly_cap_usd": 1, "conductor": []}),
            ["conductor must be an object"])

    def test_this_repos_config_keeps_make_check(self):
        config, problems = factory_config.load(REPO)
        self.assertEqual(problems, [])
        self.assertEqual(config["conductor"]["gate_command"], "make check")
        self.assertEqual(factory_config.resolve_gate_command(config),
                         (["make", "check"], []))


TYPE_LABELS = {"feature": "feature", "ci-fix": "fix", "bug": "fix"}


def labelled(type_labels):
    return dict(CONFIG, conductor={"type_labels": type_labels})


class TestTypeLabels(unittest.TestCase):
    """A consumer repo labels its issues its own way (#700): factory.json's
    optional conductor.type_labels maps those labels to item types.
    Absent, the type: rule is unchanged."""

    def plan(self, issues, config):
        import conductor_plan
        return conductor_plan.plan_batch(issues, "matt", config, 0.0,
                                         {"prd": 0, "adr": 0, "wo": 0},
                                         AGENTS)

    def test_the_map_values_are_plannable_issue_types(self):
        import conductor_plan
        self.assertEqual(set(factory_config.LABEL_ITEM_TYPES),
                         set(conductor_plan.TYPE_BY_LABEL.values()))
        self.assertLessEqual(set(factory_config.LABEL_ITEM_TYPES),
                             set(conductor_plan.ITEM_STEPS))

    def test_an_absent_map_resolves_to_none(self):
        self.assertEqual(factory_config.resolve_type_labels({}), (None, []))
        self.assertEqual(factory_config.resolve_type_labels(
            {"conductor": {"gate_command": "make check"}}), (None, []))

    def test_a_configured_map_resolves_to_itself(self):
        self.assertEqual(factory_config.resolve_type_labels(
            {"conductor": {"type_labels": TYPE_LABELS}}),
            (TYPE_LABELS, []))

    def test_a_malformed_map_is_an_exact_problem(self):
        for table, problems in (
                ([], ["conductor.type_labels must map label names to"
                      " feature or fix"]),
                ({"feature": "story"},
                 ["conductor.type_labels.feature must be feature or fix"]),
                ({"ci-fix": "order", "chore": 1},
                 ["conductor.type_labels.ci-fix must be feature or fix",
                  "conductor.type_labels.chore must be feature or fix"]),
                ({" ": "fix", 3: "fix"},
                 ["conductor.type_labels keys must be non-blank label"
                  " names"])):
            with self.subTest(table=table):
                self.assertEqual(factory_config.config_problems(
                    {"wip_cap": 1, "monthly_cap_usd": 1,
                     "conductor": {"type_labels": table}}), problems)
                self.assertEqual(factory_config.resolve_type_labels(
                    {"conductor": {"type_labels": table}}),
                    (None, [f"config: factory.json {problem}"
                            for problem in problems]))

    def test_detector_f_reports_a_bad_map(self):
        import gates
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(json.dumps(
                labelled({"ci-fix": "defect"})))
            self.assertEqual(gates.check_config_shape(Path(tmp)), [
                "F: .github/factory.json conductor.type_labels.ci-fix"
                " must be feature or fix"])

    def test_the_consumers_labels_plan_items(self):
        result, problems = self.plan(
            [issue(1, ("feature", "size:M")),
             issue(2, ("ci-fix", "size:S", "frontend")),
             issue(3, ("bug", "ci-fix", "size:S"))],
            labelled(TYPE_LABELS))
        self.assertEqual(problems, [])
        self.assertEqual([(i["item"], i["type"]) for i in result["items"]],
                         [("#1", "feature"), ("#2", "fix"), ("#3", "fix")])
        self.assertEqual(result["deferred"], [])

    def test_a_map_replaces_the_type_rule(self):
        result, _ = self.plan(
            [issue(1, ("type:feature", "size:M")),
             issue(2, ("frontend", "size:S"))], labelled(TYPE_LABELS))
        self.assertEqual(result["items"], [])
        self.assertEqual(result["deferred"], [
            "#1 deferred: no label maps to an item type"
            " (conductor.type_labels)",
            "#2 deferred: no label maps to an item type"
            " (conductor.type_labels)"])

    def test_labels_naming_two_types_defer(self):
        result, _ = self.plan([issue(1, ("ci-fix", "feature", "size:S"))],
                              labelled(TYPE_LABELS))
        self.assertEqual(result["deferred"], [
            "#1 deferred: its labels map to more than one item type"
            " (ci-fix -> fix, feature -> feature)"])

    def test_the_ready_label_still_makes_an_order(self):
        result, _ = self.plan(
            [issue(1, ("feature", "wo:ready-for-agent", "size:S"))],
            labelled(TYPE_LABELS))
        self.assertEqual([i["type"] for i in result["items"]], ["order"])

    def test_a_bad_map_plans_nothing(self):
        self.assertEqual(self.plan([issue(1)], labelled({"x": "chore"})),
                         (None, ["config: factory.json"
                                 " conductor.type_labels.x must be feature"
                                 " or fix"]))


SIZE_LABELS = {"size:xs": "S", "size:s": "S", "size:m": "M",
               "size:l": "L", "size:xl": "L"}


def sized(**table):
    return dict(CONFIG, conductor=table)


class TestSizeLabels(unittest.TestCase):
    """The consumer's own size labels (conductor.size_labels) and a
    default size for an issue with none (conductor.default_size). With
    neither, the size: rule is unchanged."""

    def plan(self, issues, config):
        import conductor_plan
        return conductor_plan.plan_batch(issues, "matt", config, 0.0,
                                         {"prd": 0, "adr": 0, "wo": 0},
                                         AGENTS)

    def test_absent_keys_resolve_to_none(self):
        self.assertEqual(factory_config.resolve_size_labels({}), (None, []))
        self.assertEqual(factory_config.resolve_default_size({}),
                         (None, []))

    def test_configured_keys_resolve_to_themselves(self):
        config = {"conductor": {"size_labels": SIZE_LABELS,
                                "default_size": "M"}}
        self.assertEqual(factory_config.resolve_size_labels(config),
                         (SIZE_LABELS, []))
        self.assertEqual(factory_config.resolve_default_size(config),
                         ("M", []))

    def test_malformed_keys_are_exact_problems(self):
        for table, problems in (
                ({"size_labels": []},
                 ["conductor.size_labels must map label names to S, M"
                  " or L"]),
                ({"size_labels": {"size:m": "medium", "big": 3}},
                 ["conductor.size_labels.size:m must be S, M or L",
                  "conductor.size_labels.big must be S, M or L"]),
                ({"size_labels": {"": "S"}},
                 ["conductor.size_labels keys must be non-blank label"
                  " names"]),
                ({"default_size": "XL"},
                 ["conductor.default_size must be S, M or L"]),
                ({"default_size": None},
                 ["conductor.default_size must be S, M or L"])):
            with self.subTest(table=table):
                self.assertEqual(factory_config.config_problems(
                    {"wip_cap": 1, "monthly_cap_usd": 1,
                     "conductor": table}), problems)
                prefixed = [f"config: factory.json {problem}"
                            for problem in problems]
                self.assertEqual(factory_config.resolve_size_labels(
                    {"conductor": table}), (None, prefixed))
                self.assertEqual(factory_config.resolve_default_size(
                    {"conductor": table}), (None, prefixed))

    def test_detector_f_reports_a_bad_default(self):
        import gates
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(json.dumps(
                sized(default_size="m")))
            self.assertEqual(gates.check_config_shape(Path(tmp)), [
                "F: .github/factory.json conductor.default_size must be"
                " S, M or L"])

    def test_the_consumers_size_labels_price_items(self):
        result, problems = self.plan(
            [issue(1, ("type:feature", "size:xl")),
             issue(2, ("type:defect", "size:s", "size:xs"))],
            sized(size_labels=SIZE_LABELS))
        self.assertEqual(problems, [])
        self.assertEqual([(i["item"], i["size"], i["estimate_usd"])
                          for i in result["items"]],
                         [("#1", "L", 40), ("#2", "S", 5)])

    def test_a_size_map_replaces_the_size_rule(self):
        result, _ = self.plan([issue(1, ("type:feature", "size:M"))],
                              sized(size_labels=SIZE_LABELS))
        self.assertEqual(result["deferred"], [
            "#1 deferred: no label maps to a size (conductor.size_labels)"])

    def test_labels_naming_two_sizes_defer(self):
        result, _ = self.plan(
            [issue(1, ("type:feature", "size:s", "size:l"))],
            sized(size_labels=SIZE_LABELS, default_size="M"))
        self.assertEqual(result["deferred"], [
            "#1 deferred: its labels map to more than one size"
            " (size:s -> S, size:l -> L)"])

    def test_the_default_applies_only_with_no_size_label(self):
        result, _ = self.plan(
            [issue(1, ("type:feature",)), issue(2, ("type:feature",
                                                    "size:L"))],
            sized(default_size="S"))
        self.assertEqual([(i["item"], i["size"]) for i in result["items"]],
                         [("#1", "S"), ("#2", "L")])
        result, _ = self.plan([issue(1, ("type:feature", "size:xs"))],
                              sized(size_labels=SIZE_LABELS,
                                    default_size="L"))
        self.assertEqual(result["items"][0]["size"], "S")

    def test_neither_key_keeps_the_size_rule(self):
        result, _ = self.plan([issue(1, ("type:feature",)),
                               issue(2, ("type:feature", "size:xl"))],
                              CONFIG)
        self.assertEqual(result["deferred"], ["#1 deferred: no size: label",
                                              "#2 deferred: no size: label"])


class TestWorkerGate(RunCase):
    def config(self, cap, gate=None):
        path = self.root / ".github/factory.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        config = {"monthly_cap_usd": cap}
        if gate is not None:
            config["conductor"] = {"gate_command": gate}
        path.write_text(json.dumps(config))

    def test_the_allowed_tools_name_the_gate_command(self):
        tools = conductor_run.allowed_tools(["npm", "test"])
        self.assertIn("Bash(npm test)", tools)
        self.assertFalse([t for t in tools if "make" in t])
        self.assertEqual(conductor_run.allowed_tools(["make", "check"]),
                         conductor_run.ALLOWED_TOOLS)

    def test_a_worker_runs_under_the_configured_gate_command(self):
        self.config(300, gate="npm test")
        self.run_step("#12", "spec", Harness(act=pr_body))
        cmd = self.harness.calls[0]["cmd"]
        tools = cmd[cmd.index("--allowedTools") + 1:]
        self.assertEqual(tools,
                         list(conductor_run.allowed_tools(["npm", "test"])))
        self.assertIn("Bash(npm test)", cmd[2])

    def test_a_bad_gate_command_launches_nothing(self):
        self.config(300, gate="make check && true")
        summary, problems = self.run_step("#12", "spec",
                                          Harness(act=pr_body))
        # A refusal no retry fixes pauses dispatch (#709).
        self.assertEqual((summary, problems), (None, [
            GATE_PROBLEM, "cd: launching #12 spec was refused; dispatch is"
            " paused behind ask-2"]))
        self.assertEqual(self.harness.calls, [])


class GateTool:
    """A tool port that records each call's argv and cwd; `fail` names
    an argument whose call exits nonzero."""

    def __init__(self, fail=None):
        self.calls, self.fail = [], fail

    def __call__(self, args, cwd=None):
        self.calls.append((list(args), str(Path(cwd).resolve())))
        if self.fail and self.fail in args:
            raise subprocess.CalledProcessError(1, args, stderr="red\n")
        return subprocess.CompletedProcess(args, 0, "", "")


class TestMergeGate(tcm.TurnCase):
    def merge(self, config=None, tool=None):
        self.ledger(tcm.START + self.filled(tcm.SHIPPED))
        self.gate = tool or GateTool()
        summary, problems = merge.merge_turn(
            self.root, "b1", "#12", self.clock, self.git, self.fake_gh(),
            self.gate, self.clock.sleep, pid=555, config=config)
        return summary, problems

    def test_the_default_gate_is_make_check_in_the_item_worktree(self):
        self.item({"src.txt": "x\n"})
        summary, problems = self.merge()
        self.assertEqual((problems, summary["stall"]), ([], None))
        self.assertEqual(self.gate.calls, [(["make", "check"],
                                            str(self.wt.resolve()))])

    def test_the_configured_gate_command_runs_in_the_item_worktree(self):
        self.item({"src.txt": "x\n"})
        summary, _ = self.merge(
            config={"conductor": {"gate_command": "npm test"}})
        self.assertIsNone(summary["stall"])
        self.assertEqual(self.gate.calls,
                         [(["npm", "test"], str(self.wt.resolve()))])

    def test_a_red_gate_stalls_naming_the_command(self):
        self.item({"src.txt": "x\n"})
        summary, _ = self.merge(
            config={"conductor": {"gate_command": "npm test"}},
            tool=GateTool(fail="test"))
        self.assertEqual(summary["stall"],
                         f"npm test failed on {tcm.BRANCH}: red")


class ConsumerTurnCase(tcm.TurnCase):
    """The scratch repo as a consumer repo: a plugin.json of its own, a
    stamped manifest, and no factory_init.py at its root."""

    def setUp(self):
        consumer = {path: text for path, text in tcm.SEED.items()
                    if path != "factory_init.py"}
        with mock.patch.dict(tcm.SEED, consumer, clear=True):
            super().setUp()


class TestConsumerMerge(ConsumerTurnCase):
    def test_a_skills_change_bumps_no_version_in_a_consumer_repo(self):
        self.item({"skills/x/SKILL.md": "x\n"})
        summary, problems = self.turn(tcm.SHIPPED)
        self.assertEqual((problems, summary["stall"]), ([], None))
        self.assertIn('"version": "0.7.3"',
                      (self.wt / ".claude-plugin/plugin.json").read_text())
        self.assertFalse(self.calls("tool", "update-manifest"))
        self.assertFalse([row for row in self.rows
                          if row.get("what") == "plugin-version"])

    def test_a_manifest_conflict_is_a_stall_in_a_consumer_repo(self):
        self.item({"factory/manifest.json": '{"files": "item"}\n'})
        self.main_moves({"factory/manifest.json": '{"files": "main"}\n'})
        summary, _ = self.turn(tcm.SHIPPED)
        self.assertEqual(summary["stall"],
                         f"merging origin/main into {tcm.BRANCH} conflicts"
                         " in factory/manifest.json")
        self.assertFalse(self.calls("tool", "update-manifest"))


class TestFactorySource(tcm.TurnCase):
    def test_only_a_root_with_factory_init_and_plugin_json_is_the_source(
            self):
        self.assertTrue(merge.factory_source(self.wt))
        (self.wt / "factory_init.py").unlink()
        self.assertFalse(merge.factory_source(self.wt))
        self.assertTrue(merge.factory_source(REPO))


class TestPlanCharters(unittest.TestCase):
    """A consumer repo has no factory/agents/ (ADR-0055): plan and open
    read the charter bands from the directory --agents names."""

    def run_cli(self, argv):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(json.dumps(CONFIG))
            return cli_contract.capture(
                conductor.main, argv, env={}, clock=clock, root=tmp,
                run=fake_gh({12: issue(12)}), git=fake_git(),
                netrc=Path(tmp) / "netrc")

    def test_plan_reads_charters_from_the_named_directory(self):
        code, out = self.run_cli(["plan", "--agents", str(AGENTS), "#12"])
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines()[0], "cd: 1 item(s) planned")

    def test_open_reads_charters_from_the_named_directory(self):
        code, out = self.run_cli(["open", "b1", "--agents", str(AGENTS),
                                  "#12"])
        self.assertEqual(code, 0, out)

    def test_without_it_a_consumer_repo_has_no_charters(self):
        code, out = self.run_cli(["plan", "#12"])
        self.assertEqual(code, 1)
        self.assertIn("factory/agents/factory-architect.md is missing", out)


if __name__ == "__main__":
    unittest.main()
