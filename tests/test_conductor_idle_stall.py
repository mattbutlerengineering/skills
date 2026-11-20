"""An idle stall whose runner is still alive (stall rule 4): the step had
no state change for twice its wall-clock limit, but its runner may yet
finish. The stall row names the launch's run and pid, so the run stays
in flight — its ceiling counted (amendment 11), its worktree its own —
until its finishing run row lands or its runner is found dead: "a second
runner from a stale next never shares its worktree" (conductor_flow).
A facet of tests/test_conductor_flow.py (its fixtures), split out so the
suites run as parallel modules.
"""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import conductor_flow as flow
import conductor_run

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_flow import (START, alive, answered, dead,  # noqa: E402
                                 launch, ran, run_id)

LAUNCHED = START + [launch("#14", "planned", "build", pid=777,
                           at="2026-10-10T09:00:00Z")]
# 210 minutes after the launch: over twice #14's 90-minute limit.
LATER = datetime(2026, 10, 10, 12, 30, tzinfo=timezone.utc)
RELAUNCH = {"run_id": run_id("#14", "build", 2), "pid": 888}


def idle_stalled():
    _, writes, problems = flow.survey(LAUNCHED, LATER, 3, alive, {})
    assert problems == [], problems
    return LAUNCHED + writes


def retried():
    rows = idle_stalled()
    return rows + [answered(rows[-1]["id"], "retry", "#14")]


def ready_items(rows, probe):
    ready, writes, problems = flow.survey(rows, LATER, 3, probe, {})
    assert problems == [], problems
    return ready, writes


class TestTheIdleStallNamesItsRun(unittest.TestCase):
    def test_the_stall_row_carries_the_launch_s_run_and_pid(self):
        row = idle_stalled()[-2]
        self.assertEqual(row, {
            "at": "2026-10-10T12:30:00Z", "kind": "state", "item": "#14",
            "from": "build", "to": "stalled",
            "reason": "no state change for over 180 minutes",
            "cause": "runner-lost", "run_id": run_id("#14", "build"),
            "pid": 777})

    def test_its_ceiling_stays_counted(self):
        self.assertEqual(conductor_run._in_flight_usd(idle_stalled()), 3.0)

    def test_a_dead_runner_s_stall_names_no_run(self):
        _, writes, _ = flow.survey(LAUNCHED, LATER, 3, dead, {})
        self.assertNotIn("run_id", writes[1])


class TestARetryWaitsForTheLiveRun(unittest.TestCase):
    def test_a_live_run_is_not_relaunched_and_holds_its_slot(self):
        ready, writes = ready_items(retried(), alive)
        self.assertEqual(writes, [])
        self.assertEqual(ready, [{"item": "#12", "step": "spec"},
                                 {"item": "#13", "step": "spec"}])
        # Two slots, one held by the live run.
        self.assertEqual(flow.survey(retried(), LATER, 2, alive, {})[0],
                         [{"item": "#12", "step": "spec"}])

    def test_the_launch_is_refused_under_the_lock(self):
        self.assertEqual(
            flow.transition_problems(retried(), "#14", "build", RELAUNCH),
            ["cd: #14's build run conductor-b1-14-build-1 is still in"
             " flight"])

    def test_its_finishing_row_frees_the_resume(self):
        rows = retried() + [dict(ran("#14", "build"), pid=777)]
        self.assertEqual(conductor_run._in_flight_usd(rows), 0.0)
        self.assertIn({"item": "#14", "step": "build"},
                      ready_items(rows, alive)[0])
        self.assertEqual(
            flow.transition_problems(rows, "#14", "build", RELAUNCH), [])

    def test_a_runner_found_dead_gets_its_lost_run_row_then_resumes(self):
        rows = retried()
        ready, writes = ready_items(rows, dead)
        self.assertNotIn({"item": "#14", "step": "build"}, ready)
        self.assertEqual(writes, [{
            "at": "2026-10-10T12:30:00Z", "kind": "run", "item": "#14",
            "step": "build", "charter": "swe", "band": "implementation",
            "model": "m", "models_reported": [], "effort": "medium",
            "run_id": run_id("#14", "build"), "pid": 777,
            "outcome": "runner-lost:cost-at-ceiling"}])
        self.assertIn({"item": "#14", "step": "build"},
                      ready_items(rows + writes, dead)[0])


if __name__ == "__main__":
    unittest.main()
