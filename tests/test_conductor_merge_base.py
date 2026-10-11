"""conductor_merge.py (PRD-0013, WO-0161): the merge base the checks
ran on is the one the squash lands on (review minor 4). Split from
test_conductor_merge.py, which sits at the 800-line ceiling; it reuses
that file's scratch-repo TurnCase, so nothing real is pushed or merged
beyond a local bare origin, and gh is FakeGh.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_merge import SHIPPED, TurnCase  # noqa: E402


class TestMainMovesDuringTheWait(TurnCase):
    def gh_moving_main(self):
        """A FakeGh whose first check-runs read sees another merge land
        on origin/main: the wait's window, in which nothing re-checks
        the base."""
        gh, moved = self.fake_gh(), []

        def port(args):
            if args[:1] == ["api"] and "graphql" not in args and not moved:
                moved.append(True)
                self.main_moves({"other.txt": "landed meanwhile\n"})
            return gh(args)
        port.fake = gh.fake
        return port

    def test_a_base_that_moved_during_the_wait_stalls_before_landing(self):
        self.item({"src.txt": "x\n"})
        base = self.head("origin/main")
        summary, problems = self.turn(SHIPPED, gh=self.gh_moving_main())
        self.assertEqual(problems, [])
        moved_to = self.head("origin/main")
        self.assertEqual(summary["stall"], (
            f"origin/main moved from {base[:12]} to {moved_to[:12]} while"
            " the checks ran; a retry merges it in and checks again"))
        self.assertEqual(self.rows[-1]["recommended"], "retry")
        self.assertFalse(self.gh.fake.called("pr", "merge"))

    def test_a_base_that_held_still_lands(self):
        self.item({"src.txt": "x\n"})
        summary, problems = self.turn(SHIPPED)
        self.assertEqual((problems, summary["sha"]), ([], "m1"))

    def test_a_queue_owns_the_base_check(self):
        # With a merge queue, the queue checks the merge-result commit
        # itself (ADR-0036 condition 1); the turn only enqueues.
        self.item({"src.txt": "x\n"})
        gh = self.gh_moving_main()
        gh.fake.answers[("api", "graphql")] = \
            '{"data": {"repository": {"mergeQueue": {"id": "q"}}}}'
        summary, _ = self.turn(SHIPPED, gh=gh)
        self.assertEqual(summary["sha"], "m1")


if __name__ == "__main__":
    unittest.main()
