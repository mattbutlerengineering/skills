"""conductor_close.merge_closing against the consumer repo's own
auto-merge (#807): the closing PR can land between the Conductor's push
and its own merge. Run through FakeGit and FakeGh only; tests assert the
EXACT summaries and problem strings. Fixtures are test_conductor_close's.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import conductor
import conductor_close as close

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_gh import FakeGh  # noqa: E402
from fake_git import FakeGit  # noqa: E402
from test_conductor_close import CLOSED, GREEN_GH, MERGED_LIST, NOW, \
    answer, at, lines, write  # noqa: E402


class TestRepoMergedTheClosingPr(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.here = ["-C", str(self.root)]

    def repo_merged(self, head, ancestor=True):
        """The repo's auto-merge landed the closing PR (merged at `head`)
        after the Conductor pushed, so no open PR is left."""
        rows = CLOSED + [answer("ask-5", "merge", at(17))]
        write(self.root, lines(rows))
        self.git = FakeGit(
            {(*self.here, "rev-parse", "HEAD"): "c105ed\n",
             (*self.here, "rev-parse", "origin/main"): "a11ce0\n"},
            failing=None if ancestor else [*self.here, "merge-base",
                                           "--is-ancestor"],
            error=subprocess.CalledProcessError(1, "git", stderr=""))
        self.gh = FakeGh({
            **GREEN_GH,
            ("pr", "list", "--head", "conductor/b1", "--state", "open"):
                "[]",
            MERGED_LIST: json.dumps([{"number": 6, "headRefOid": head,
                                      "mergeCommit": {"oid": "5qa5h"}}])})
        return close.merge_closing(self.root, "b1", lambda: NOW,
                                   self.git, self.gh, lambda seconds: None)

    def test_a_pr_the_repo_merged_at_the_pushed_head_succeeds(self):
        self.assertEqual(self.repo_merged("c105ed"), (
            {"batch": "b1", "pr": 6, "sha": "5qa5h", "by": "repo"}, []))
        self.assertFalse(self.gh.called("pr", "merge"))

    def test_a_pr_merged_with_the_pushed_head_on_main_succeeds(self):
        self.assertEqual(self.repo_merged("01dead"), (
            {"batch": "b1", "pr": 6, "sha": "5qa5h", "by": "repo"}, []))
        self.assertIn(self.here + ["merge-base", "--is-ancestor", "c105ed",
                                   "origin/main"], self.git.calls)

    def test_a_pr_merged_without_the_pushed_head_names_the_gap(self):
        self.assertEqual(self.repo_merged("01dead", ancestor=False), (
            None, ["cd: closing merge: PR #6 was merged by the repo at"
                   " 01dead, without c105ed, the head the Conductor"
                   " pushed: what that head adds is missing from main"]))
        self.assertFalse(self.gh.called("pr", "merge"))

    def test_an_unreadable_ancestry_stalls_for_a_retry(self):
        rows = CLOSED + [answer("ask-5", "merge", at(17))]
        write(self.root, lines(rows))
        git = FakeGit({(*self.here, "rev-parse", "HEAD"): "c105ed\n",
                       (*self.here, "rev-parse", "origin/main"):
                           "a11ce0\n"},
                      failing=[*self.here, "merge-base", "--is-ancestor"])
        gh = FakeGh({**GREEN_GH, ("pr", "list", "--head", "conductor/b1",
                                  "--state", "open"): "[]",
                     MERGED_LIST: json.dumps([{
                         "number": 6, "headRefOid": "01dead",
                         "mergeCommit": {"oid": "5qa5h"}}])})
        self.assertEqual(close.merge_closing(
            self.root, "b1", lambda: NOW, git, gh, lambda seconds: None),
            (None, ["cd: closing merge: reading whether origin/main holds"
                    " c105ed failed: fatal: rejected"]))

    def test_the_cli_reports_a_pr_the_repo_already_merged(self):
        # The race one step later: the PR merged between the check wait
        # and gh pr merge, which then fails.
        rows = CLOSED + [answer("ask-5", "merge", at(17))]
        write(self.root, lines(rows))
        git = FakeGit({(*self.here, "rev-parse", "HEAD"): "c105ed\n",
                       (*self.here, "rev-parse", "origin/main"):
                           "a11ce0\n"})
        gh = FakeGh({**GREEN_GH, MERGED_LIST: json.dumps([{
            "number": 6, "headRefOid": "c105ed",
            "mergeCommit": {"oid": "5qa5h"}}])}, failing=["pr", "merge"])
        code, out = cli_contract.capture(
            conductor.main, ["close", "b1", "--merge"], env={},
            clock=lambda: NOW, root=self.root, run=gh, git=git,
            sleep=lambda seconds: None)
        self.assertEqual((code, out), (0, (
            "cd: batch b1's closing PR #6 was already merged by the repo"
            " as 5qa5h\n"
            "cd: 0 problem(s)\n")))


if __name__ == "__main__":
    unittest.main()
