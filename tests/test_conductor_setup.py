"""factory.json's conductor.worktree_setup (issue #850): an optional
argv a consumer repo names to install its dependencies in each ITEM
worktree before the Worker launches, so the Worker's item commits meet
hooks that need them. Off by default; a failure stalls the item with
cause setup-failed. Every call goes through a fake, and tests assert the
EXACT problem strings and rows.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

import conductor
import conductor_run
import factory_config

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_run import (BASE, Gh, Git, Harness,  # noqa: E402
                                RunCase, pr_body)

SETUP_PROBLEM = ("conductor.worktree_setup must be a non-empty list of"
                 " non-blank argument strings")


class Setup:
    """A stand-in for cli.runner: records each call's argv, cwd and
    timeout, and raises `error` when given one."""

    def __init__(self, error=None):
        self.error, self.calls = error, []

    def __call__(self, binary, timeout=None):
        def run(args, input=None, cwd=None):
            self.calls.append({"argv": [binary, *args], "cwd": cwd,
                               "timeout": timeout})
            if self.error is not None:
                raise self.error
            return subprocess.CompletedProcess([binary, *args], 0, "", "")
        return run


class TestWorktreeSetupConfig(unittest.TestCase):
    def test_absent_is_no_setup(self):
        self.assertEqual(factory_config.resolve_worktree_setup({}),
                         (None, []))

    def test_a_configured_setup_is_its_argv(self):
        self.assertEqual(factory_config.resolve_worktree_setup(
            {"conductor": {"worktree_setup": ["npm", "ci"]}}),
            (["npm", "ci"], []))

    def test_anything_but_a_list_of_strings_is_refused(self):
        for value in ([], "npm ci", ["npm", ""], ["npm", 7], {"a": "b"}):
            with self.subTest(value=value):
                self.assertEqual(factory_config.resolve_worktree_setup(
                    {"conductor": {"worktree_setup": value}}),
                    (None, [f"config: factory.json {SETUP_PROBLEM}"]))

    def test_detector_f_checks_it(self):
        self.assertEqual(factory_config.config_problems(
            {"wip_cap": 1, "monthly_cap_usd": 1,
             "conductor": {"worktree_setup": "npm ci"}}), [SETUP_PROBLEM])


class TestWorktreeSetupRun(RunCase):
    def configure(self, setup):
        path = self.root / ".github/factory.json"
        path.write_text(json.dumps({"monthly_cap_usd": 300,
                                    "conductor": {"worktree_setup": setup}}))

    def run_setup(self, setup, harness=None):
        self.ledger(*BASE)
        self.setup = setup
        self.harness = harness or Harness(act=pr_body)
        result = conductor_run.run_step(
            self.root, "b1", "#12", "spec", self.clock,
            git=Git(self.tmp.name), gh=Gh(), harness=self.harness, pid=777,
            netrc=self.no_netrc, setup=setup)
        self.rows, _ = conductor.load(self.root, "b1")
        return result

    def test_setup_runs_in_the_item_worktree_before_the_worker(self):
        self.configure(["npm", "ci"])
        seen = []
        self.run_setup(Setup(), Harness(act=lambda cwd: (
            seen.append(len(self.setup.calls)), pr_body(cwd))))
        self.assertEqual(self.setup.calls, [
            {"argv": ["npm", "ci"], "cwd": str(self.worktree("#12")),
             "timeout": 90 * 60}])
        self.assertEqual(seen, [1])

    def test_a_failed_setup_stalls_the_item_and_names_the_command(self):
        self.configure(["npm", "ci"])
        summary, problems = self.run_setup(Setup(
            subprocess.CalledProcessError(1, "npm", stderr="ERESOLVE\n")))
        reason = "worktree setup `npm ci` failed: ERESOLVE"
        self.assertEqual(problems, [])
        self.assertEqual(self.harness.calls, [])
        self.assertEqual(summary["stall"], reason)
        self.assertEqual(
            (self.rows[-2]["from"], self.rows[-2]["to"],
             self.rows[-2]["reason"], self.rows[-2]["cause"]),
            ("spec", "stalled", reason, "setup-failed"))
        self.assertEqual(self.rows[-1]["ask_kind"], "stall")
        self.assertEqual([r for r in self.rows if r["kind"] == "run"], [])

    def test_a_setup_past_the_steps_timeout_stalls_too(self):
        self.configure(["npm", "ci"])
        summary, _ = self.run_setup(Setup(
            subprocess.TimeoutExpired(["npm", "ci"], 5400)))
        self.assertEqual(self.rows[-2]["cause"], "setup-failed")
        self.assertTrue(summary["stall"].startswith(
            "worktree setup `npm ci` failed: "))
        self.assertEqual(self.harness.calls, [])

    def test_absent_setup_is_never_called(self):
        self.run_setup(Setup())
        self.assertEqual(self.setup.calls, [])
        self.assertEqual(len(self.harness.calls), 1)


if __name__ == "__main__":
    unittest.main()
