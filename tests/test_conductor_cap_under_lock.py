"""The run-time cap check reads the month's spend under the ledger lock
(amendment 11: "under the ledger lock, before it writes the launch
row"). A run that finishes between a launch's first read and its lock
has committed its spend row and appended its run row, so its ceiling is
no longer in flight: a figure read before the lock misses the spend,
and the launch would pass a cap it breaks.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import cost_ledger
import conductor_run

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_git import FakeGit  # noqa: E402
from test_conductor_flow import (LEDGER, NOW, START, launch,  # noqa: E402
                                 moved, ran, run_id)

RUNS = cost_ledger.RUNS_DIR
A_RUN = run_id("#12", "build")
A_FILE = f"{RUNS}/{A_RUN}.jsonl"
# #12's build finished: its $3.00 spend row is on its branch, and its
# run row is in the ledger, so nothing is in flight.
FINISHED = START + [moved("#12", "planned", "spec"),
                    launch("#12", "spec", "build", pid=1),
                    ran("#12", "build")]
LAUNCH = {"item": "#14", "step": "build", "ceiling": 3.0,
          "fields": {"run_id": run_id("#14", "build"), "pid": 2}}


def finished_git():
    spent = cost_ledger.entry("#12", A_RUN, "m", 1, 3.0, "completed",
                              "2026-10-10")
    return FakeGit({
        ("ls-tree", "-r", "--name-only", "conductor/b1-12"): A_FILE + "\n",
        ("show", f"conductor/b1-12:{A_FILE}"): json.dumps(spent) + "\n"})


class TestTheCapCheckReadsUnderTheLock(unittest.TestCase):
    def launch(self, cap):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / LEDGER
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(r) + "\n" for r in FINISHED))
            problems = conductor_run._launch(tmp, "b1", NOW, LAUNCH,
                                             finished_git(), cap)
            last = json.loads(path.read_text().splitlines()[-1])
        return problems, last

    def test_spend_committed_before_the_lock_counts(self):
        problems, last = self.launch(5.0)
        self.assertEqual(problems, [
            "cd: launching #14 build ($3.00 ceiling) would put the month at"
            " $6.00 against its $5.00 cap; dispatch is paused behind ask-2"])
        self.assertEqual((last["kind"], last["ask_kind"]), ("ask", "spend"))

    def test_a_launch_within_the_cap_is_written(self):
        problems, last = self.launch(6.0)
        self.assertEqual(problems, [])
        self.assertEqual((last["item"], last["to"], last["reason"]),
                         ("#14", "build", "launched"))

    def test_an_unreadable_branch_under_the_lock_launches_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / LEDGER
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(r) + "\n" for r in FINISHED))
            problems = conductor_run._launch(
                tmp, "b1", NOW, LAUNCH, FakeGit(failing=["ls-tree"]), 300.0)
            self.assertEqual(len(path.read_text().splitlines()),
                             len(FINISHED))
        self.assertEqual(problems, [
            "cd: git ls-tree origin/main failed: fatal: rejected"])


if __name__ == "__main__":
    unittest.main()
