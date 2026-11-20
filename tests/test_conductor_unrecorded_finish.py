"""A finished run with no follow-up row (stall rule 1): its runner
appended its `run` row, then died before it recorded the stall or the
review verdict that row called for. `next` writes that row itself once
the runner is gone, so the item never sits in its step with nothing in
flight, no ask and nothing ready. A facet of tests/test_conductor_flow.py
(its fixtures), split out so the suites run as parallel modules.
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import conductor
import conductor_flow as flow

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_gh import FakeGh  # noqa: E402
from fake_git import FakeGit, raw_diff  # noqa: E402
from test_conductor_flow import (LEDGER, NOW, START, alive,  # noqa: E402
                                 clock, dead, launch, ran,
                                 run_id)

REVIEWED = [launch("#14", "planned", "build"), ran("#14", "build"),
            launch("#14", "build", "verify"), ran("#14", "verify"),
            dict(launch("#14", "verify", "review"), reviewed_head="h0"),
            ran("#14", "review")]


def survey(rows, probe, facts=None, now=NOW):
    ready, writes, problems = flow.survey(START + rows, now, 3, probe,
                                          facts or {})
    return ready, writes, problems


class TestAFailedRunWithNoStall(unittest.TestCase):
    ROWS = [launch("#14", "planned", "build"),
            ran("#14", "build", outcome="agent-failed")]

    def test_a_dead_runner_s_failed_run_stalls(self):
        ready, writes, problems = survey(self.ROWS, dead)
        self.assertEqual(problems, [])
        self.assertNotIn("#14", [entry["item"] for entry in ready])
        reason = ("its run conductor-b1-14-build-1 ended agent-failed, and"
                  " its runner (pid 100) is gone with nothing recorded"
                  " after it")
        self.assertEqual(writes, [
            {"at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#14",
             "from": "build", "to": "stalled", "reason": reason,
             "cause": "agent-failed"},
            {"at": "2026-10-10T12:30:00Z", "kind": "ask", "item": "#14",
             "id": "ask-2", "ask_kind": "stall",
             "question": f"#14 stalled in build: {reason}. Retry, retry"
                         " one band up, or block?",
             "options": ["retry", "retry-up", "block"],
             "recommended": "retry", "why": flow.WORKER_WHY}])

    def test_a_live_runner_may_still_record_its_own_stall(self):
        self.assertEqual(survey(self.ROWS, alive)[1], [])

    def test_a_live_runner_silent_past_twice_the_limit_stalls(self):
        # #14 is size M: a 90-minute limit, so 180 minutes idle stalls.
        start = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(
            survey(self.ROWS, alive, now=start + timedelta(minutes=180))[1],
            [])
        writes = survey(self.ROWS, alive,
                        now=start + timedelta(minutes=181))[1]
        self.assertEqual((writes[0]["reason"], writes[0]["cause"]), (
            "its run conductor-b1-14-build-1 ended agent-failed, and"
            " nothing was recorded after it for over 180 minutes",
            "agent-failed"))

    def test_a_stalled_item_is_never_stalled_again(self):
        rows = self.ROWS + survey(self.ROWS, dead)[1]
        self.assertEqual(survey(rows, dead)[1], [])


class TestACompletedReviewWithNoVerdictRow(unittest.TestCase):
    def test_a_dead_runner_s_pass_verdict_is_recorded(self):
        _, writes, problems = survey(REVIEWED, dead,
                                     {"#14": {"verdict": "pass"}})
        self.assertEqual(problems, [])
        self.assertEqual(writes, [{
            "at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#14",
            "from": "review", "to": "reviewed",
            "reason": "the reviewer passed it", "verdict": "pass",
            "author_runs": [run_id("#14", "build"), run_id("#14", "verify")],
            "reviewer_run": run_id("#14", "review"),
            "reviewed_head": "h0"}])

    def test_a_dead_runner_s_changes_verdict_returns_to_build(self):
        writes = survey(REVIEWED, dead, {"#14": {"verdict": "changes"}})[1]
        self.assertEqual([(w["from"], w["to"]) for w in writes],
                         [("review", "build")])

    def test_no_verdict_in_review_md_stalls(self):
        writes = survey(REVIEWED, dead, {"#14": {"verdict": None}})[1]
        self.assertEqual((writes[0]["to"], writes[0]["reason"],
                          writes[0]["cause"]),
                         ("stalled", "review.md carries no verdict:"
                          " pass|changes line", "agent-failed"))
        self.assertEqual(writes[1]["ask_kind"], "stall")

    def test_a_launch_with_no_reviewed_head_stalls(self):
        rows = REVIEWED[:4] + [launch("#14", "verify", "review"),
                               ran("#14", "review")]
        writes = survey(rows, dead, {"#14": {"verdict": "pass"}})[1]
        self.assertEqual(writes[0]["reason"],
                         "review run conductor-b1-14-review-1's launch"
                         " recorded no reviewed head, so its verdict cannot"
                         " be recorded")

    def test_no_verdict_read_yet_waits(self):
        self.assertEqual(survey(REVIEWED, dead)[1], [])

    def test_a_live_runner_may_still_record_its_own_verdict(self):
        self.assertEqual(
            survey(REVIEWED, alive, {"#14": {"verdict": "pass"}})[1], [])

    def test_only_an_unrecorded_review_needs_its_verdict_read(self):
        self.assertEqual(flow.unrecorded_reviews(START + REVIEWED), ["#14"])
        self.assertEqual(flow.unrecorded_reviews(START + REVIEWED[:-1]), [])


class TestNextReadsTheVerdict(unittest.TestCase):
    def test_next_records_a_dead_runner_s_verdict_from_review_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / LEDGER
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(r) + "\n"
                                    for r in START + REVIEWED))
            Path(tmp, ".github").mkdir()
            Path(tmp, ".github/factory.json").write_text(
                json.dumps({"wip_cap": 2}))
            review = "docs/fixes/x/review.md"
            worktree = Path(tmp, ".claude/worktrees/conductor-b1-14")
            (worktree / review).parent.mkdir(parents=True)
            (worktree / review).write_text("---\nverdict: changes\n---\n")
            code, out = cli_contract.capture(
                conductor.main, ["next", "b1"], env={}, clock=clock,
                root=tmp, run=FakeGh({
                    ("issue", "view"): json.dumps({"state": "OPEN"}),
                    ("pr", "list"): "[]"}),
                git=FakeGit({("rev-parse",): f"{tmp}/.git\n",
                             ("diff",): raw_diff([review])}),
                alive=dead)
            rows, _ = conductor.load(tmp, "b1")
        self.assertEqual(code, 0, out)
        self.assertEqual((rows[-1]["from"], rows[-1]["to"]),
                         ("review", "build"))


if __name__ == "__main__":
    unittest.main()
