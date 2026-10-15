"""conductor_merge.py's merge-turn stalls: every step that cannot finish
mechanically queues a stall ask, recommending `retry` or `block`, and
leaves the branch as the runner pushed it — never a forced push, never a
retry. A facet of tests/test_conductor_merge.py (its TurnCase harness,
scratch repo and fake ports), split out so the merge-turn suites run as
parallel modules (#916).
"""
import subprocess
import sys
import unittest
from pathlib import Path

import conductor_flow as flow
import conductor_merge as merge

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_flow import (NOW, START, answered, moved,  # noqa: E402
                                 stall_ask)
from test_conductor_merge import (BRANCH, GREEN_RUN, SHIPPED,  # noqa: E402
                                  TurnCase, write)


class TestMergeTurnStalls(TurnCase):
    def assertStalled(self, summary, reason):
        self.assertEqual(summary["stall"], reason)
        self.assertEqual(self.rows[-2]["to"], "stalled")
        self.assertEqual(self.rows[-2]["reason"], reason)
        self.assertEqual(self.rows[-2]["cause"], "merge-failed")
        self.assertEqual(self.rows[-1]["ask_kind"], "stall")
        self.assertEqual(self.head("origin/" + BRANCH), self.pushed)

    def item(self, files, message="item"):
        """Committed and pushed: every stall here asserts origin's copy
        of the branch is still what the runner pushed."""
        super().item(files, message)
        self.push_item()
        self.pushed = self.head()

    def test_a_non_mechanical_conflict_stalls_and_aborts(self):
        self.item({"README.md": "item\n"})
        self.main_moves({"README.md": "main\n"})
        summary, problems = self.turn(SHIPPED)
        self.assertEqual(problems, [])
        self.assertStalled(summary, f"merging origin/main into {BRANCH}"
                           " conflicts in README.md")
        self.assertEqual(self.head(), self.pushed)
        self.assertFalse((self.repo / ".git/worktrees/conductor-b1-12/"
                          "MERGE_HEAD").exists())
        self.assertFalse(self.calls("git", "push"))
        self.assertEqual(self.rows[-1]["recommended"], "block")

    def test_a_dirty_tracked_file_stalls_with_gits_whole_reason(self):
        # #726: a merge refused before it starts has nothing to abort,
        # and its reason sits above the last stderr line, "Aborting".
        self.item({"src.txt": "x\n"})
        self.main_moves({"README.md": "main\n"})
        write(self.wt, {"README.md": "dirty\n"})
        # A retried turn: from `ship`, the clean-worktree check would
        # stall first.
        rows = SHIPPED + [moved("#12", "ship", "merging"),
                          moved("#12", "merging", "stalled"),
                          stall_ask("ask-3", "#12"),
                          answered("ask-3", "retry", "#12")]
        summary, problems = self.turn(rows)
        self.assertEqual(problems, [])
        # The refused merge changed nothing, so re-running it yields the
        # same stderr; its wording varies by git version (newer ones add
        # a strategy line after "Aborting").
        again = subprocess.run(["git", "-C", str(self.wt), "merge",
                                "--no-edit", "origin/main"],
                               capture_output=True, text=True)
        lines = [line.strip() for line in again.stderr.splitlines()
                 if line.strip()]
        self.assertIn("README.md", lines)
        self.assertIn("Aborting", lines)
        self.assertStalled(summary, f"merging origin/main into {BRANCH}"
                           f" failed: {' | '.join(lines)}")

    def test_a_red_make_check_stalls_before_any_push(self):
        self.item({"src.txt": "x\n"})
        summary, _ = self.turn(SHIPPED, tool=self.tool(fail="check"))
        self.assertStalled(summary, f"make check failed on {BRANCH}:"
                           " make: *** [check] Error 1")
        self.assertFalse(self.calls("git", "push"))

    def test_a_red_check_run_stalls_without_merging(self):
        self.item({"src.txt": "x\n"})
        red = dict(GREEN_RUN, conclusion="failure")
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(checks=[[red]]))
        self.assertStalled(summary,
                           f"checks failed on {self.head()[:12]}: validate")
        self.assertFalse(self.gh.fake.called("pr", "merge"))

    def test_checks_that_never_finish_time_out_after_30_minutes(self):
        self.item({"src.txt": "x\n"})
        pending = dict(GREEN_RUN, status="in_progress", conclusion=None)
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(checks=[[pending]]))
        self.assertStalled(summary, f"checks on {self.head()[:12]} did not"
                           " finish within 30 minutes")
        self.assertEqual(sum(self.clock.slept), 30 * 60)
        self.assertEqual(self.rows[-1]["recommended"], "retry")
        self.assertFalse(self.gh.fake.called("pr", "merge"))

    def test_pending_checks_are_waited_for(self):
        self.item({"src.txt": "x\n"})
        pending = dict(GREEN_RUN, status="queued", conclusion=None)
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(
            checks=[[], [pending], [GREEN_RUN]]))
        self.assertEqual(summary["sha"], "m1")
        self.assertEqual(self.clock.slept, [30, 30])

    def test_a_queue_is_used_when_main_has_one(self):
        self.item({"src.txt": "x\n"})
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(
            queue={"id": "q"}, views=[
                {"state": "OPEN", "isInMergeQueue": True},
                {"state": "MERGED", "mergeCommit": {"oid": "q1"}}]))
        self.assertEqual(summary["sha"], "q1")
        self.assertEqual(self.rows[-1]["to"], "merged")

    def test_an_ejection_from_the_queue_stalls(self):
        self.item({"src.txt": "x\n"})
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(
            queue={"id": "q"}, views=[
                {"state": "OPEN", "isInMergeQueue": True},
                {"state": "OPEN", "isInMergeQueue": False}]))
        self.assertStalled(summary,
                           "PR #44 was ejected from the merge queue")

    def test_a_queue_that_never_merges_times_out(self):
        self.item({"src.txt": "x\n"})
        summary, _ = self.turn(SHIPPED, gh=self.fake_gh(
            queue={"id": "q"}, views=[{"state": "OPEN",
                                       "isInMergeQueue": True}]))
        self.assertStalled(summary, "PR #44 did not merge from the queue"
                           " within 30 minutes")

    def test_a_stalled_merge_resumes_as_a_merge(self):
        rows = START + SHIPPED + [moved("#12", "ship", "merging"),
                                  moved("#12", "merging", "stalled"),
                                  stall_ask("ask-3", "#12"),
                                  answered("ask-3", "retry", "#12")]
        ready, _, _ = flow.survey(rows, NOW, 3, lambda pid: True, {})
        self.assertIn({"item": "#12", "step": "merge"}, ready)
        self.assertEqual(merge.merge_problems(rows, "#12", {}), [])


if __name__ == "__main__":
    unittest.main()
