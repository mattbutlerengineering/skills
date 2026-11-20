"""conductor_close.close_batch over an item branch whose local ref is
ahead of origin's: spend committed on the item branch and never pushed
(record_lost and commit_held commit locally only, and a delivery's push
can fail). A facet of tests/test_conductor_close.py, whose fixtures it
reuses, split out by concern.

- An item merged outside the batch (blocked → merged at close, or
  stalled → merged on a `merged` answer, ADR-0105) has its branch's spend
  carried like a blocked item's: the merged PR carried only what was
  pushed, and a run with no spend row fails the scorecard forever.
- The remote delete of a spend-only blocked branch is leased on
  origin's sha, once it is an ancestor of the local sha inspected: a
  lease on the local sha is rejected whenever local is ahead.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import conductor_close as close
import conductor_landed
import conductor_spend

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_gh import FakeGh  # noqa: E402
from fake_git import FakeGit  # noqa: E402
import git_repo  # noqa: E402
from test_conductor_close import (BLOCKED_SPEND, BRANCH_SHA, COSTS,  # noqa: E402
                                  COST_ONLY_LOG, HAS_NEEDS_HUMAN, LABEL_LIST,
                                  LANDED_GH, LANDED_ROW, MERGED_CALL,
                                  NO_LANDED, ORIGIN_SHA, ROWS, SPEND,
                                  CloseCase, answer, ask, at, head_call,
                                  lines, log_call, ls_call, ls_remote_call,
                                  run, state)

# #13's build runner died; record_lost charged it on the item branch,
# locally, and nothing pushed that commit.
LOST_BUILD = dict(run("#13", "build", "implementation", "s", "medium", []),
                  outcome=conductor_spend.LOST)
LOST_ROWS = ROWS[:11] + [LOST_BUILD] + ROWS[11:]
# #13 stalled on its merged PR and the Owner answered `merged`.
STALLED_MERGED = ROWS[:11] + [
    LOST_BUILD,
    state("#13", "build", "stalled", at(12), "PR #6541 merged outside the"
          " batch", cause=conductor_landed.CAUSE, pr=6541),
    ask("ask-3", "#13", "stall", at(12), tuple(conductor_landed.OPTIONS)),
    answer("ask-3", "merged", at(12, 30), "#13"),
    state("#13", "stalled", "merged", at(12, 30), "merged outside the batch"
          " as PR #6541", pr=6541, sha="f00d", checks={}),
] + ROWS[16:]


class TestMergedOutsideSpendIsCarried(CloseCase):
    def test_a_landed_items_unpushed_spend_is_carried(self):
        # main holds what the PR carried (13-spec-1), not the lost run's
        # row the branch holds locally.
        summary, problems = self.close(LOST_ROWS, costs=SPEND,
                                       gh=FakeGh(LANDED_GH))
        self.assertEqual(problems, [])
        self.assertEqual((summary["landed"], summary["blocked"]),
                         (["#13"], []))
        self.assertEqual(self.run_file_ids(), ["conductor-b1-13-build-1"])
        self.assertEqual(self.ledger()[-2]["kind"], "close")
        # Merged, so never deleted, labelled or kept.
        self.assertEqual(self.git.called("-C", str(self.root), "push",
                                         "--force-with-lease="
                                         "refs/heads/conductor/b1-13:"
                                         f"{ORIGIN_SHA}"), [])
        self.assertEqual([call[:2] for call in self.gh.calls],
                         [MERGED_CALL[:2], ["pr", "create"]])

    def test_a_stalled_then_merged_items_unpushed_spend_is_carried(self):
        summary, problems = self.close(STALLED_MERGED, costs=SPEND,
                                       gh=FakeGh(NO_LANDED))
        self.assertEqual(problems, [])
        self.assertEqual((summary["merged"], summary["blocked"]),
                         (["#12", "#13", "#14"], []))
        self.assertEqual(self.run_file_ids(), ["conductor-b1-13-build-1"])

    def test_the_closing_pr_names_the_merged_outside_items_carried(self):
        # #2211: not "its blocked items (none)" when #13's was carried.
        self.close(STALLED_MERGED, costs=SPEND, gh=FakeGh(NO_LANDED))
        self.assertEqual(self.gh.calls[-1][-1], "Conductor batch b1's"
                         " closing PR: its batch ledger, run evidence,"
                         " scorecard, and the spend rows of its items"
                         " merged outside the batch (#13).\n\nCloses #12"
                         "\nCloses #13\nCloses #14\n\nNo work order: the"
                         " Conductor's closing PR for batch b1.")

    def test_the_closing_pr_names_blocked_and_merged_outside_items(self):
        self.assertEqual(close.pr_body(
            "b1", {"merged": ["#12", "#14"], "blocked": ["#13"]},
            outside=["#14"]), "Conductor batch b1's closing PR: its batch"
            " ledger, run evidence, scorecard, and the spend rows of its"
            " blocked items (#13) and of its items merged outside the batch"
            " (#14).\n\nCloses #12\nCloses #14\n\nNo work order: the"
            " Conductor's closing PR for batch b1.")

    def test_a_conductor_merged_items_branch_is_not_read(self):
        # Its merge turn pushed the head it landed: nothing is local only.
        self.close(ROWS)
        self.assertEqual(self.git.called("-C", str(self.root), "ls-tree",
                                         "--name-only", "conductor/b1-12"),
                         [])


class TestDeleteLeasedOnOrigin(CloseCase):
    def test_the_delete_is_leased_on_origins_sha(self):
        summary, problems = self.close(ROWS)
        self.assertEqual(problems, [])
        here = ["-C", str(self.root)]
        self.assertEqual(self.git.calls[6:10], [
            here + ["log", "--format=%s", f"origin/main..{BRANCH_SHA}"],
            here + ["ls-remote", "origin", "refs/heads/conductor/b1-13"],
            here + ["fetch", "origin", "refs/heads/conductor/b1-13"],
            here + ["merge-base", "--is-ancestor", ORIGIN_SHA, BRANCH_SHA]])
        self.assertEqual(self.git.calls[-1], here + [
            "push", f"--force-with-lease=refs/heads/conductor/b1-13:"
            f"{ORIGIN_SHA}", "origin", ":refs/heads/conductor/b1-13"])

    def fake(self, origin, failing=None, error=None):
        return FakeGit({
            ("-C", str(self.root), "show",
             f"conductor/b1-13:{COSTS}"): lines(BLOCKED_SPEND),
            ls_call(self.root): COSTS + "\n",
            head_call(self.root): BRANCH_SHA + "\n",
            log_call(self.root): COST_ONLY_LOG,
            ls_remote_call(self.root): origin}, failing=failing, error=error)

    def test_a_branch_never_pushed_is_neither_deleted_nor_kept(self):
        summary, problems = self.close(ROWS, git=self.fake(""))
        self.assertEqual(problems, [])
        self.assertEqual(self.git.called("-C", str(self.root), "push",
                                         "origin"), [])
        self.assertEqual(self.git.called("-C", str(self.root),
                                         "merge-base"), [])
        self.assertNotIn("Kept on origin", self.gh.calls[2][-1])

    def test_origin_ahead_of_the_local_ref_keeps_the_branch(self):
        # Origin holds a commit close never inspected.
        behind = subprocess.CalledProcessError(1, "git", stderr="")
        summary, problems = self.close(ROWS, git=self.fake(
            f"{ORIGIN_SHA}\trefs/heads/conductor/b1-13\n",
            failing=["-C", str(self.root), "merge-base"], error=behind))
        self.assertEqual(problems, [])
        self.assertEqual([c for c in self.git.calls if "--force-with-lease="
                          f"refs/heads/conductor/b1-13:{ORIGIN_SHA}" in c],
                         [])
        self.assertIn("Kept on origin, holding work beyond spend rows:"
                      " conductor/b1-13.", self.gh.calls[2][-1])

    def test_an_unreadable_origin_branch_refuses_the_close(self):
        summary, problems = self.close(ROWS, git=self.fake(
            "", failing=["-C", str(self.root), "ls-remote"]))
        self.assertEqual((summary, problems), (None, [
            "cd: close refused: reading origin's conductor/b1-13 failed:"
            " fatal: rejected"]))
        self.assertEqual(self.ledger(), ROWS)

    def test_a_failed_ancestry_read_refuses_the_close(self):
        summary, problems = self.close(ROWS, git=self.fake(
            f"{ORIGIN_SHA}\trefs/heads/conductor/b1-13\n",
            failing=["-C", str(self.root), "merge-base"]))
        self.assertEqual((summary, problems), (None, [
            "cd: close refused: reading whether conductor/b1-13 holds"
            f" origin's {ORIGIN_SHA} failed: fatal: rejected"]))


GIT = ["-c", "user.email=t@example.com", "-c", "user.name=t", "-c",
       "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null"]


class TestLeaseAgainstRealGit(unittest.TestCase):
    """The lease against a real origin: the local ref holds a spend
    commit origin lacks, the routine case after record_lost."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        git_repo.init(base / "origin.git", "--bare")
        self.root = git_repo.clone(base / "origin.git", base / "repo")
        self.sh("commit", "-q", "--allow-empty", "-m", "seed")
        self.sh("push", "-q", "origin", "HEAD:main")
        self.sh("fetch", "-q", "origin")
        self.sh("checkout", "-q", "-b", "conductor/b1-13")
        self.spend("conductor-b1-13-spec-1")
        self.sh("push", "-q", "origin", "conductor/b1-13")
        self.spend("conductor-b1-13-build-1")
        self.sh("checkout", "-q", "-b", "conductor/b1", "origin/main")

    def sh(self, *args):
        return subprocess.run(["git", *GIT, "-C", str(self.root), *args],
                              check=True, capture_output=True,
                              text=True).stdout

    def git(self, args):
        return subprocess.run(["git", *GIT, *args], check=True,
                              capture_output=True, text=True)

    def spend(self, run_id):
        self.sh("commit", "-q", "--allow-empty", "-m",
                conductor_spend.SPEND_SUBJECT + run_id)

    def origin_heads(self):
        return self.sh("ls-remote", "--heads", "origin")

    def test_a_spend_only_branch_ahead_of_origin_is_deleted(self):
        branches, problems = close.sort_blocked_branches(
            self.git, self.root, "b1", ["#13"])
        self.assertEqual(problems, [])
        origin = self.sh("rev-parse", "origin/conductor/b1-13").strip()
        self.assertEqual(branches, {"delete": [("conductor/b1-13", origin)],
                                    "keep": []})
        self.assertIn("refs/heads/conductor/b1-13", self.origin_heads())
        for path in ("docs/factory/batches/b1/ledger.jsonl",
                     close.SCORECARDS):
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            (self.root / path).write_text("{}\n")
        gh = FakeGh({LABEL_LIST: HAS_NEEDS_HUMAN})
        self.assertEqual(close._publish(
            self.root, "b1", self.git, gh, {"merged": [], "blocked": ["#13"]},
            {"#13": "r"}, branches), [])
        self.assertNotIn("refs/heads/conductor/b1-13", self.origin_heads())

    def test_a_commit_pushed_after_the_read_refuses_the_delete(self):
        branches, _ = close.sort_blocked_branches(self.git, self.root, "b1",
                                                  ["#13"])
        # Someone pushes to origin's branch between the read and delete.
        self.sh("push", "-q", "origin", "conductor/b1-13")
        branch, sha = branches["delete"][0]
        self.assertNotEqual(sha, self.sh("rev-parse",
                                         "conductor/b1-13").strip())
        with self.assertRaises(subprocess.CalledProcessError):
            self.sh("push", f"--force-with-lease=refs/heads/{branch}:{sha}",
                    "origin", f":refs/heads/{branch}")
        self.assertIn("refs/heads/conductor/b1-13", self.origin_heads())


if __name__ == "__main__":
    unittest.main()
