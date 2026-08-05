"""run_single_query must signal the entire claude process group and
close its stdout pipe — early detection returns before the CLI exits,
so without a group kill the CLI's own children are orphaned. The group
must be signalled whether the leader is still running or already
exited: a dead leader's grandchildren keep the group alive and would
otherwise outlive the run. Signalled, not reaped — killed grandchildren
are collected by init, hence the grace loops.

Fake `claude` shell scripts on PATH stand in for the real CLI; no API
calls are made. setUp installs a poison fake so even a test that
forgets install_fake can never reach a real `claude`.
"""
import os
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from trigger_eval import run_single_query  # noqa: E402

FAKE_CLAUDE = """#!/bin/sh
# Spawn a grandchild that outlives us unless the caller kills our group.
sleep 300 &
echo $! > "$PID_FILE"
sleep 300
"""

FAKE_EXITING_CLAUDE = """#!/bin/sh
# Leader exits immediately; the grandchild inherits the stdout pipe and
# keeps the process group alive after the leader is gone.
sleep 300 &
echo $! > "$PID_FILE"
exit 0
"""

FAKE_VANISHING_CLAUDE = """#!/bin/sh
# Exit with nothing spawned and nothing written: the whole group is
# gone by cleanup time.
exit 0
"""

FAKE_POISON = """#!/bin/sh
exit 97
"""


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


class TestProcessTreeReaping(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="reap-"))
        self.addCleanup(self._cleanup)
        self.pid_file = self.dir / "grandchild.pid"
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = f"{self.dir}:{self.old_path}"
        os.environ["PID_FILE"] = str(self.pid_file)
        self.install_fake(FAKE_POISON)

    def install_fake(self, script):
        fake = self.dir / "claude"
        fake.write_text(script, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    def _cleanup(self):
        os.environ["PATH"] = self.old_path
        os.environ.pop("PID_FILE", None)
        if self.pid_file.is_file():
            pid = int(self.pid_file.read_text())
            if pid_alive(pid):
                os.kill(pid, 9)
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def assert_grandchild_reaped(self):
        deadline = time.time() + 2
        while time.time() < deadline and not self.pid_file.is_file():
            time.sleep(0.05)
        self.assertTrue(self.pid_file.is_file(),
                        "fake claude never started")
        pid = int(self.pid_file.read_text())
        # brief grace for the kill to land
        deadline = time.time() + 2
        while time.time() < deadline and pid_alive(pid):
            time.sleep(0.05)
        self.assertFalse(pid_alive(pid),
                         "grandchild survived run_single_query")

    def test_grandchild_is_dead_after_timeout_return(self):
        self.install_fake(FAKE_CLAUDE)
        fired = run_single_query("q", {"idea": "d"}, timeout=2,
                                 model=None, isolate=False)
        self.assertIsNone(fired)
        self.assert_grandchild_reaped()

    def test_grandchild_of_an_exited_leader_is_still_reaped(self):
        # Deterministic by control flow, not timing: the fake writes
        # nothing and its grandchild holds the stdout write end open, so
        # the reader can only leave its loop by observing the exit — the
        # cleanup therefore always runs against a dead leader.
        self.install_fake(FAKE_EXITING_CLAUDE)
        fired = run_single_query("q", {"idea": "d"}, timeout=2,
                                 model=None, isolate=False)
        self.assertIsNone(fired)
        self.assert_grandchild_reaped()

    def test_a_fully_exited_group_is_tolerated(self):
        # No grandchild: the reader's poll reaps the leader, leaving the
        # group empty, so the cleanup's group kill has nothing to signal
        # and must swallow the lookup failure rather than crash the run.
        self.install_fake(FAKE_VANISHING_CLAUDE)
        fired = run_single_query("q", {"idea": "d"}, timeout=2,
                                 model=None, isolate=False)
        self.assertIsNone(fired)


if __name__ == "__main__":
    unittest.main()
