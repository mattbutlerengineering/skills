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
        self.assertEqual((summary, problems), (None, [GATE_PROBLEM]))
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
                run=fake_gh({12: issue(12)}), git=fake_git())

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
