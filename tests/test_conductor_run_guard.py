"""conductor_run.py (PRD-0013, re-review R3): the fail-closed launch
guard for the Worker's two known push gaps. pushInsteadOf skips a
remote's explicit pushurl, and git's https transport reads ~/.netrc, so
the runner refuses to launch a Worker while either could carry a
credential. git is a fake or a scratch repo, gh is FakeGh, and the
harness never runs a model.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import conductor
import conductor_run

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_run import BASE, Gh, Git, Harness, RunCase, \
    pr_body  # noqa: E402

PUSHURL = "remote.origin.pushurl https://t@github.com/o/r.git\n"


class GuardCase(RunCase):
    def setUp(self):
        super().setUp()
        self.netrc = Path(self.tmp.name) / "netrc"

    def launch(self, git=None):
        harness = Harness(act=pr_body)
        self.ledger(*BASE)
        summary, problems = conductor_run.run_step(
            self.root, "b1", "#12", "spec", self.clock,
            git=git or Git(self.tmp.name), gh=Gh(), harness=harness,
            pid=777, netrc=self.netrc)
        return summary, problems, harness


def configured(tmp, out):
    """The scratch Git port, answering `config --get-regexp` with
    `out`."""
    git = Git(tmp)

    def run(args):
        if "--get-regexp" in args:
            git.calls.append(args)
            return subprocess.CompletedProcess(args, 0, stdout=out,
                                               stderr="")
        return git(args)
    run.calls = git.calls
    return run


class TestPushGuard(GuardCase):
    def assertRefused(self, result, problem):
        summary, problems, harness = result
        self.assertEqual((summary, problems), (None, [problem]))
        self.assertEqual(harness.calls, [])
        self.assertEqual(self.load_kinds(), [r["kind"] for r in BASE])

    def load_kinds(self):
        rows, _ = conductor.load(self.root, "b1")
        return [r["kind"] for r in rows]

    def test_an_explicit_pushurl_refuses_the_launch(self):
        self.assertRefused(
            self.launch(configured(self.tmp.name, PUSHURL)),
            "cd: launch refused: remote origin has an explicit pushurl,"
            " which the Worker's push block does not rewrite; unset"
            " remote.origin.pushurl while a batch runs")

    def test_a_github_netrc_entry_refuses_the_launch(self):
        for host in ("github.com", "api.github.com"):
            self.netrc.write_text(f"machine {host} login x password t\n")
            self.assertRefused(
                self.launch(),
                f"cd: launch refused: {self.netrc} has a {host} entry,"
                " which git's https transport would hand a Worker's push;"
                " move it aside while a batch runs")

    def test_a_default_netrc_entry_refuses_the_launch(self):
        self.netrc.write_text("default login x password t\n")
        self.assertRefused(
            self.launch(),
            f"cd: launch refused: {self.netrc} has a default entry, which"
            " git's https transport would hand a Worker's push; move it"
            " aside while a batch runs")

    def test_an_unreadable_netrc_fails_closed(self):
        self.netrc.write_text("machine\n")
        summary, problems, harness = self.launch()
        self.assertIsNone(summary)
        self.assertTrue(problems[0].startswith(
            f"cd: launch refused: cannot read {self.netrc}:"), problems)
        self.assertEqual(harness.calls, [])

    def test_another_hosts_netrc_entry_and_no_pushurl_launch(self):
        self.netrc.write_text("machine example.com login x password t\n")
        summary, problems, harness = self.launch()
        self.assertEqual((problems, summary["stall"]), ([], None))
        self.assertEqual(len(harness.calls), 1)


class TestPushGapsOnARealRepo(unittest.TestCase):
    """The guard's git read against a real git: exit 1 is "no pushurl",
    and a configured one is found."""

    def test_a_real_repo_with_and_without_a_pushurl(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "w"
            subprocess.run(["git", "init", "-q", str(work)], check=True)

            def git(args):
                return subprocess.run(["git", *args], check=True,
                                      capture_output=True, text=True)
            netrc = Path(tmp) / "absent"
            self.assertEqual(conductor_run.push_gaps(git, work, netrc), [])
            subprocess.run(["git", "-C", str(work), "config",
                            "remote.up.pushurl", "https://h/r.git"],
                           check=True)
            self.assertEqual(conductor_run.push_gaps(git, work, netrc), [
                "cd: launch refused: remote up has an explicit pushurl,"
                " which the Worker's push block does not rewrite; unset"
                " remote.up.pushurl while a batch runs"])


if __name__ == "__main__":
    unittest.main()
