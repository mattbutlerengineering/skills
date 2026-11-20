"""A spend row the item worktree holds uncommitted: the runner metered
the run and wrote its per-run file, then the spend commit failed (#939).
"Exactly one run row and one spend row per run, always" (architecture.md,
the Worker contract): the run-time cap check counts that row (amendment
11), and close commits it before carrying a blocked item's spend, so
the scorecard finds it. Real git in a scratch repo, as the failed commit
leaves it.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import conductor_close as close
import conductor_run
import cost_ledger
import conductor_spend

sys.path.insert(0, str(Path(__file__).resolve().parent))
import git_repo  # noqa: E402
from test_conductor_flow import (NOW, START, answered, launch,  # noqa: E402
                                 moved, ran, run_id, stall_ask)

RUN = run_id("#14", "build")
STALLED = START + [launch("#14", "planned", "build"), ran("#14", "build"),
                   moved("#14", "build", "stalled", cause="delivery-failed"),
                   stall_ask("ask-2", "#14", ("retry", "block"))]
BLOCKED = STALLED + [answered("ask-2", "block", "#14"),
                     moved("#14", "stalled", "blocked",
                           cause="delivery-failed")]


class HeldSpendCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        git_repo.init(self.root, "-b", "main")
        self.sh("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                "--allow-empty", "-m", "seed")
        self.sh("update-ref", "refs/remotes/origin/main", "HEAD")
        self.sh("config", "user.name", "t")
        self.sh("config", "user.email", "t@t")
        self.worktree = self.root / ".claude/worktrees/conductor-b1-14"
        self.sh("worktree", "add", "-q", "-b", "conductor/b1-14",
                str(self.worktree), "origin/main")
        # The runner metered $3.00 and wrote its row; the commit failed.
        self.assertEqual(cost_ledger.record_isolated(
            self.worktree, cost_ledger.entry("#14", RUN, "m", 10, 3.0,
                                             "completed", "2026-10-10")),
            [])

    def sh(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args],
                              check=True, capture_output=True, text=True)

    def git(self, args):
        return self.sh(*args)

    def branch_log(self):
        return self.sh("log", "--format=%s",
                       "origin/main..conductor/b1-14").stdout.splitlines()


class TestTheCapCountsAHeldRow(HeldSpendCase):
    def test_a_stalled_item_s_held_row_counts_toward_the_month(self):
        self.assertEqual(
            conductor_run.month_spend(self.git, STALLED, "b1", NOW),
            (3.0, [], []))

    def test_a_held_row_once_committed_counts_once(self):
        self.assertIsNone(conductor_spend.commit_spend(self.git,
                                                       self.worktree, RUN))
        self.assertEqual(
            conductor_run.month_spend(self.git, STALLED, "b1", NOW),
            (3.0, [], []))

    def test_a_malformed_held_row_is_never_read_as_empty(self):
        path = self.worktree / cost_ledger.run_ledger_path(RUN)
        path.write_text("not json\n", encoding="utf-8")
        spent, unread, malformed = conductor_run.month_spend(
            self.git, STALLED, "b1", NOW)
        self.assertEqual((spent, unread), (None, []))
        self.assertEqual(len(malformed), 1)
        self.assertTrue(malformed[0].startswith(f"cd: {path}:1 "),
                        malformed)


class TestCloseCommitsAHeldRow(HeldSpendCase):
    def test_a_blocked_item_s_held_row_is_committed_and_carried(self):
        self.assertEqual(close.carry_blocked_spend(
            self.git, self.root, "b1", ["#14"], BLOCKED), [])
        self.assertEqual(self.branch_log(),
                         [f"{conductor_spend.SPEND_SUBJECT}{RUN}"])
        entries, problems = cost_ledger.read(self.root)
        self.assertEqual(problems, [])
        self.assertEqual([entry["run_id"] for entry in entries], [RUN])
        lines = list(range(1, len(BLOCKED) + 1))
        self.assertEqual(close.compute(BLOCKED, lines, "ledger.jsonl",
                                       entries, NOW)[1], [])

    def test_a_committed_row_is_not_committed_again(self):
        self.assertIsNone(conductor_spend.commit_spend(self.git,
                                                       self.worktree, RUN))
        self.assertEqual(close.carry_blocked_spend(
            self.git, self.root, "b1", ["#14"], BLOCKED), [])
        self.assertEqual(self.branch_log(),
                         [f"{conductor_spend.SPEND_SUBJECT}{RUN}"])


if __name__ == "__main__":
    unittest.main()
