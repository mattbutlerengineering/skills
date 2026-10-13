"""conductor_merge.land_branch (#770): the one owner of landing a
checked head — push, head, PR, checks, main held unless queued, land —
which the merge turn and the closing merge both call. Driven through
FakeGh ports only, asserting the EXACT stall reasons and calls.
"""
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import conductor_merge as merge

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_gh import FakeGh  # noqa: E402

NOW = datetime(2026, 10, 10, 16, 0, tzinfo=timezone.utc)
WT = "/wt"
BRANCH = "conductor/b1-12"
HERE = ["-C", WT]
CHECKS = ("api", "repos/{owner}/{repo}/commits/c0ffee/check-runs"
          "?per_page=100")


def gh_port(queue=None):
    return FakeGh({
        ("pr", "list", "--head", BRANCH): json.dumps([{"number": 44}]),
        CHECKS: json.dumps({"check_runs": [
            {"name": "ci", "status": "completed",
             "conclusion": "success"}]}),
        ("api", "graphql"): json.dumps(
            {"data": {"repository": {"mergeQueue": queue}}}),
        ("pr", "view", "44"): json.dumps(
            {"state": "MERGED", "mergeCommit": {"oid": "m1"}})})


class TestLandBranch(unittest.TestCase):
    def land(self, main="a11ce0", gh=None):
        """Lands BRANCH with its base at a11ce0; `main` is what
        origin/main reads once the checks are green."""
        self.git = FakeGh({(*HERE, "rev-parse", "HEAD"): "c0ffee\n",
                           (*HERE, "rev-parse", "origin/main"):
                               f"{main}\n"})
        self.gh = gh or gh_port()

        def git(args):
            return subprocess.CompletedProcess(args, 0, self.git(args), "")
        return merge.land_branch(git, self.gh, WT, BRANCH, "a11ce0",
                                 lambda: NOW, lambda seconds: None)

    def test_main_held_lands_the_checked_head(self):
        self.assertEqual(self.land(), (44, "m1", {"ci": "success"}))
        self.assertEqual(self.git.calls, [
            HERE + ["push", "origin", BRANCH],
            HERE + ["rev-parse", "HEAD"],
            HERE + ["fetch", "origin", "main"],
            HERE + ["rev-parse", "origin/main"]])
        self.assertEqual(self.gh.called("pr", "merge"), [[
            "pr", "merge", "44", "--squash", "--match-head-commit",
            "c0ffee"]])

    def test_main_moving_while_the_checks_ran_lands_nothing(self):
        with self.assertRaises(merge.Stall) as stalled:
            self.land(main="b0b0b0")
        self.assertEqual((stalled.exception.reason,
                          stalled.exception.recommended), (
            "origin/main moved from a11ce0 to b0b0b0 while the checks"
            " ran; a retry merges it in and checks again", merge.RETRY))
        self.assertFalse(self.gh.called("pr", "merge"))

    def test_a_queue_checks_the_merge_result_so_main_is_not_read(self):
        self.assertEqual(self.land(main="b0b0b0", gh=gh_port({"id": "q"})),
                         (44, "m1", {"ci": "success"}))
        self.assertFalse(self.git.called(*HERE, "fetch"))


if __name__ == "__main__":
    unittest.main()
