"""run_single_query must reap the entire claude process tree and close
its stdout pipe — early detection returns before the CLI exits, so
without process-group kill the CLI's own children are orphaned.

A fake `claude` on PATH (shell script spawning a grandchild sleep) stands
in for the real CLI; no API calls are made.
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
        fake = self.dir / "claude"
        fake.write_text(FAKE_CLAUDE, encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.pid_file = self.dir / "grandchild.pid"
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = f"{self.dir}:{self.old_path}"
        os.environ["PID_FILE"] = str(self.pid_file)

    def _cleanup(self):
        os.environ["PATH"] = self.old_path
        os.environ.pop("PID_FILE", None)
        if self.pid_file.is_file():
            pid = int(self.pid_file.read_text())
            if pid_alive(pid):
                os.kill(pid, 9)
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_grandchild_is_dead_after_timeout_return(self):
        fired = run_single_query("q", {"idea": "d"}, timeout=2,
                                 model=None, isolate=False)
        self.assertIsNone(fired)
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


if __name__ == "__main__":
    unittest.main()
