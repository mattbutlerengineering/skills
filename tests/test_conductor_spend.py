"""conductor_spend.py (#937): the spend row a Worker run leaves on its
item branch, the commit subject that names it, the fail-closed ceiling
outcomes, and the row `next` writes for a runner found dead. git goes
through FakeGit; tests assert the EXACT rows, calls and problem strings.
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import conductor_spend as spend
import cost_ledger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_git import FakeGit  # noqa: E402
from test_conductor_flow import START, launch  # noqa: E402

NOW = datetime(2026, 10, 10, 12, 30, tzinfo=timezone.utc)
RID = "conductor-b1-14-build-1"
REL = f"docs/factory/costs/runs/{RID}.jsonl"


def lost_row(step="build", model="m", run_id=RID):
    return {"at": "2026-10-10T12:30:00Z", "kind": "run", "item": "#14",
            "step": step, "charter": "c", "band": "implementation",
            "model": model, "models_reported": [], "effort": "medium",
            "run_id": run_id, "pid": 9, "outcome": spend.LOST}


class TestVocabulary(unittest.TestCase):
    def test_every_ceiling_ending_says_the_figure_is_the_ceiling(self):
        self.assertEqual(spend.CEILING_OUTCOME, {
            "timeout": "killed:cost-at-ceiling",
            "unaccounted": "unaccounted:cost-at-ceiling",
            "lost": "runner-lost:cost-at-ceiling"})
        self.assertEqual(spend.LOST, "runner-lost:cost-at-ceiling")

    def test_spend_run_reads_only_the_subject_the_writer_writes(self):
        self.assertEqual(spend.spend_run(f"chore(cost): {RID}"), RID)
        self.assertIsNone(spend.spend_run("chore(cost): raise the cap"))
        self.assertIsNone(spend.spend_run(f"docs: {RID}"))


class TestRecordSpend(unittest.TestCase):
    def test_writes_the_run_file_then_adds_and_commits_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = FakeGit({})
            self.assertIsNone(spend.record_spend(
                git, Path(tmp), "#14", RID, "m", 12, 1.5, "completed", NOW))
            self.assertEqual(
                (Path(tmp) / REL).read_text(),
                json.dumps(cost_ledger.entry("#14", RID, "m", 12, 1.5,
                                             "completed", "2026-10-10"))
                + "\n")
            self.assertEqual(git.calls, [
                ["-C", tmp, "add", REL],
                ["-C", tmp, "commit", "-m", f"chore(cost): {RID}"]])

    def test_a_duplicate_row_is_refused_unless_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = FakeGit({})
            spend.record_spend(git, Path(tmp), "#14", RID, "m", 12, 1.5,
                               "completed", NOW)
            self.assertEqual(
                spend.record_spend(git, Path(tmp), "#14", RID, "m", 0, 3.0,
                                   spend.LOST, NOW),
                f"refusing to record the spend row of {RID}: run_id"
                f" '{RID}' is already in the ledger — recording it twice"
                " would double-count the run against the monthly cap")
            self.assertIsNone(spend.record_spend(
                git, Path(tmp), "#14", RID, "m", 0, 3.0, spend.LOST, NOW,
                skip_existing=True))
            self.assertEqual((Path(tmp) / REL).read_text().count("\n"), 1)

    def test_a_failing_commit_is_the_stall_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = FakeGit({}, failing=["-C", tmp, "commit"])
            self.assertEqual(
                spend.record_spend(git, Path(tmp), "#14", RID, "m", 12, 1.5,
                                   "completed", NOW),
                f"committing the spend row of {RID} failed: fatal:"
                " rejected")


class TestRecordLost(unittest.TestCase):
    """The ceiling row for a dead runner's run, on its item branch."""

    def lost(self, writes, log="", failing=None, worktree=True, rows=None):
        with tempfile.TemporaryDirectory() as tmp:
            wt = Path(tmp) / ".claude/worktrees/conductor-b1-14"
            if worktree:
                wt.mkdir(parents=True)
            git = FakeGit({("rev-parse",): f"{tmp}/.git\n", ("log",): log},
                          failing=failing)
            rows = rows if rows is not None else START + [
                launch("#14", "planned", "build", pid=9)]
            problems = spend.record_lost(git, "b1", rows, writes, NOW)
            text = (wt / REL).read_text() if (wt / REL).is_file() else None
            return problems, git.calls, text, str(wt)

    def test_charges_the_steps_ceiling_at_zero_tokens(self):
        problems, calls, text, wt = self.lost([lost_row()])
        self.assertEqual(problems, [])
        self.assertEqual(text, json.dumps({
            "wo": "#14", "run_id": RID, "model": "m", "tokens": 0,
            "cost": 3.0, "outcome": spend.LOST, "at": "2026-10-10"}) + "\n")
        self.assertEqual(calls, [
            ["rev-parse", "--path-format=absolute", "--git-common-dir"],
            ["log", "--format=%s", "origin/main..conductor/b1-14"],
            ["-C", wt, "add", REL],
            ["-C", wt, "commit", "-m", f"chore(cost): {RID}"]])

    def test_only_lost_run_rows_are_charged(self):
        other = dict(lost_row(), outcome="agent-failed")
        problems, calls, text, _ = self.lost([other, {
            "at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#14",
            "from": "build", "to": "stalled", "reason": "r"}])
        self.assertEqual((problems, calls, text), ([], [], None))

    def test_a_run_the_branch_already_names_is_skipped(self):
        problems, calls, text, _ = self.lost(
            [lost_row()], log=f"docs: later\nchore(cost): {RID}\n")
        self.assertEqual((problems, text), ([], None))
        self.assertEqual([c[0] for c in calls], ["rev-parse", "log"])

    def test_a_missing_worktree_is_an_exact_problem(self):
        problems, calls, text, wt = self.lost([lost_row()], worktree=False)
        self.assertEqual(problems, [
            f"cd: #14's worktree {wt} is gone, so its lost run {RID} cannot"
            " be charged its ceiling"])
        self.assertEqual([c[0] for c in calls], ["rev-parse"])

    def test_a_failing_log_read_is_a_problem(self):
        problems, _, text, _ = self.lost([lost_row()], failing=["log"])
        self.assertEqual(problems, [
            "cd: #14: reading conductor/b1-14's commits failed: fatal:"
            " rejected"])
        self.assertIsNone(text)

    def test_a_failing_checkout_read_is_a_problem(self):
        problems, _, _, _ = self.lost([lost_row()], failing=["rev-parse"])
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("cd: git rev-parse failed:"),
                        problems[0])


if __name__ == "__main__":
    unittest.main()
