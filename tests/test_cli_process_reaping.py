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
import subprocess
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


_PROC_STAT = Path("/proc/self/stat").is_file()


def process_state(pid):
    """The scheduler state letter for `pid`, or None when no process
    table entry exists at all. Linux publishes it in /proc; everywhere
    else `ps` reports it."""
    if _PROC_STAT:
        try:
            data = Path(f"/proc/{pid}/stat").read_bytes()
        except OSError:
            return None
        # comm sits in parentheses and may itself contain spaces and
        # parentheses, so state is the first field after the final ")".
        return data.rsplit(b")", 1)[1].split()[0].decode()
    listing = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)],
                             capture_output=True, text=True)
    return listing.stdout.strip() or None


def pid_alive(pid):
    """True only while `pid` is still running.

    `os.kill(pid, 0)` asks whether a process-table entry exists, and a
    zombie — terminated, not yet collected — still has one. The grace
    loops below poll this predicate to decide whether a killed
    grandchild is gone, so counting a zombie as alive reports a
    grandchild that is already dead as a survivor.
    """
    state = process_state(pid)
    return state is not None and not state.startswith("Z")


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


class TestPidAlivePredicate(unittest.TestCase):
    """`pid_alive` must answer "is it running", not "does the PID exist".

    A terminated process keeps its process-table entry until something
    collects it, and `os.kill(pid, 0)` succeeds for that entry — so a
    predicate built on the signal alone calls a dead process alive. The
    grace loops above poll this predicate to decide whether a killed
    grandchild is gone, which is why that error surfaces as "grandchild
    survived" on a grandchild that is already dead.
    """

    def zombie(self):
        """A pid that has exited and has NOT been collected.

        The pipe is the synchronisation: the child's write end closes
        only when it exits, so the parent's read returning EOF proves
        termination without `wait()`ing — which would collect it and
        destroy the very state under test.
        """
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:                      # child
            os.close(read_fd)
            os._exit(0)
        os.close(write_fd)
        self.assertEqual(os.read(read_fd, 1), b"", "child did not exit")
        os.close(read_fd)
        self.addCleanup(self._collect, pid)
        return pid

    def _collect(self, pid):
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass

    def test_an_uncollected_dead_process_is_not_alive(self):
        pid = self.zombie()
        # Precondition: the table entry survives, so the naive predicate
        # has something to be wrong about. Without this the test could
        # pass for the uninteresting reason that the pid is fully gone.
        os.kill(pid, 0)
        self.assertFalse(pid_alive(pid),
                         "a terminated process must read as dead")
