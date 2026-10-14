"""The Conductor's default git port skips the repo's hooks (#833).

Every git call the Conductor makes itself goes through the one port
conductor.main builds, and that port adds `-c core.hooksPath=<devnull>`:
the Conductor commits only generated evidence, and land_branch waits for
green CI on the pushed head. The Worker's item commits run inside its
harness, a separate process, and are untouched.
"""
import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import conductor
import conductor_plan

NO_HOOKS = ["-c", f"core.hooksPath={os.devnull}"]


def clock():
    return datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)


def default_port(root):
    """The git port conductor.main builds when none is injected, caught
    where main hands it to its first capability."""
    seen = []

    def plan_cli(root, args, now, run, git):
        seen.append(git)
        return []

    with mock.patch.object(conductor_plan, "plan_cli", plan_cli), \
            contextlib.redirect_stdout(io.StringIO()):
        conductor.main(["plan"], env={}, clock=clock, root=root)
    return seen[0]


def sh(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True,
                          capture_output=True, text=True)


class DefaultPortSkipsHooks(unittest.TestCase):
    def test_every_call_gets_the_no_hooks_prefix(self):
        calls = []

        def fake_runner(binary, timeout=None):
            def run(args, input=None):
                calls.append((binary, list(args), input))
                return SimpleNamespace(stdout="", returncode=0)
            return run

        with mock.patch.object(conductor, "runner", fake_runner):
            git = default_port(Path("/nowhere"))
        git(["-C", "/w", "commit", "-m", "x"])
        git(["push", "-u", "origin", "b"], input="in")
        self.assertEqual(calls, [
            ("git", [*NO_HOOKS, "-C", "/w", "commit", "-m", "x"], None),
            ("git", [*NO_HOOKS, "push", "-u", "origin", "b"], "in")])

    def test_a_failing_pre_commit_hook_does_not_block_bookkeeping(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, hooks = Path(tmp) / "repo", Path(tmp) / "hooks"
            hooks.mkdir()
            hook = hooks / "pre-commit"
            hook.write_text("#!/bin/sh\necho 'hook ran' >&2\nexit 1\n")
            hook.chmod(0o755)
            sh(tmp, "init", "-q", str(repo))
            for key, value in (("user.email", "t@example.com"),
                               ("user.name", "t"),
                               ("commit.gpgsign", "false"),
                               ("core.hooksPath", str(hooks))):
                sh(repo, "config", key, value)
            (repo / "costs.jsonl").write_text('{"usd": 1}\n')
            sh(repo, "add", "costs.jsonl")
            # The repo's hook really rejects a plain commit.
            with self.assertRaises(subprocess.CalledProcessError):
                sh(repo, "commit", "-q", "-m", "plain")
            git = default_port(repo)
            git(["-C", str(repo), "commit", "-q", "-m",
                 "chore(conductor): close batch b1"])
            self.assertEqual(sh(repo, "log", "--format=%s").stdout,
                             "chore(conductor): close batch b1\n")


if __name__ == "__main__":
    unittest.main()
