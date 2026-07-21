"""run_single_query's cleanup contract with the harness process stubbed
out. The version probe lives at the cli seam (tests/test_cli.py) and the
record()/collision pin at tests/test_trigger_scoring.py. The eval runs
themselves cost money and never run in CI; everything here is file- and
process-local.
"""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import trigger_eval


class FakeProcess:
    """A Popen stand-in still running when the finally block reaches it."""

    pid = 424242

    def __init__(self):
        self.stdout = mock.Mock()
        self.killed = False
        self.waited = False

    def poll(self):
        return None if not self.killed else -9

    def kill(self):
        self.killed = True

    def wait(self):
        self.waited = True


class TestRunSingleQueryCleanup(unittest.TestCase):
    """The finally block's contract: whatever happens to the harness
    process — it never spawned, or it outlived its watcher — the
    per-run project dir is removed and the process is dead. A leaked
    dir per query times hundreds of runs is the failure this pins."""

    DESCRIPTIONS = {"next": "Route to the next stage."}

    def project_dirs(self):
        """mkdtemp wrapper recording every project dir the run makes."""
        created = []
        real = tempfile.mkdtemp

        def record(*args, **kwargs):
            path = real(*args, **kwargs)
            created.append(Path(path))
            return path
        return created, record

    def test_a_harness_that_never_spawns_still_removes_the_project_dir(self):
        created, record = self.project_dirs()

        def fake_popen(*args, **kwargs):
            raise OSError("no harness binary")
        with mock.patch.object(tempfile, "mkdtemp", record), \
                mock.patch.object(subprocess, "Popen", fake_popen):
            with self.assertRaises(OSError):
                trigger_eval.run_single_query("q", self.DESCRIPTIONS, 5,
                                              None, True)
        self.assertEqual(len(created), 1)
        self.assertEqual([p for p in created if p.exists()], [])

    def test_a_process_that_outlives_its_watcher_is_killed(self):
        created, record = self.project_dirs()
        process = FakeProcess()

        def refuse_killpg(pgid, sig):
            # force the fallback so no real signal leaves the test
            raise ProcessLookupError
        with mock.patch.object(tempfile, "mkdtemp", record), \
                mock.patch.object(subprocess, "Popen",
                                  lambda *a, **k: process), \
                mock.patch.object(trigger_eval.os, "killpg",
                                  refuse_killpg), \
                mock.patch.object(trigger_eval, "_watch_stream",
                                  lambda *a, **k: "next"):
            fired = trigger_eval.run_single_query("q", self.DESCRIPTIONS,
                                                  5, None, True)
        self.assertEqual(fired, "next")
        self.assertTrue(process.killed)
        self.assertTrue(process.waited)
        process.stdout.close.assert_called_once_with()
        self.assertEqual([p for p in created if p.exists()], [])


if __name__ == "__main__":
    unittest.main()
