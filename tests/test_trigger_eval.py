"""run_single_query's cleanup contract with the harness stream stubbed
out at the cli seam (ADR-0045) — no stdlib monkeypatching. The process
lifecycle (group kill, wait, pipe close) is cli.harness_run's contract,
pinned at tests/test_cli.py; the real-subprocess composition is pinned
at tests/test_process_reaping.py. What remains run_single_query's own
duty — and what this module pins — is the per-run project dir: created
once, removed whatever the stream does. A leaked dir per query times
hundreds of runs is the failure this guards. The version probe lives at
the cli seam (tests/test_cli.py) and the record()/collision pin at
tests/test_trigger_scoring.py.
"""
import contextlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cli
import trigger_eval


class TestRunSingleQueryCleanup(unittest.TestCase):
    """The finally block's contract: whether the harness stream never
    spawned or ran to a verdict, the per-run project dir is removed and
    the detection result passes through untouched."""

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

        @contextlib.contextmanager
        def no_spawn(cmd, cwd, timeout, env=None, spawn=None):
            raise OSError("no harness binary")
            yield  # pragma: no cover — the raise is the point
        with mock.patch.object(tempfile, "mkdtemp", record), \
                mock.patch.object(cli, "harness_run", no_spawn):
            with self.assertRaises(OSError):
                trigger_eval.run_single_query("q", self.DESCRIPTIONS, 5,
                                              None, True)
        self.assertEqual(len(created), 1)
        self.assertEqual([p for p in created if p.exists()], [])

    def test_the_detection_result_passes_through_and_the_dir_is_removed(self):
        created, record = self.project_dirs()
        seen = {}

        @contextlib.contextmanager
        def fake_run(cmd, cwd, timeout, env=None, spawn=None):
            seen["cmd"], seen["cwd"] = cmd, Path(cwd)
            yield iter(())

        def fake_detect(events, name_to_slug):
            return "next"
        adapter = trigger_eval.HARNESSES["claude"]._replace(
            detect=fake_detect)
        with mock.patch.object(tempfile, "mkdtemp", record), \
                mock.patch.object(cli, "harness_run", fake_run), \
                mock.patch.dict(trigger_eval.HARNESSES,
                                {"claude": adapter}):
            fired = trigger_eval.run_single_query("q", self.DESCRIPTIONS,
                                                  5, None, True)
        self.assertEqual(fired, "next")
        # the registry invocation is what ran: its project dir was the
        # cwd, its command carried the query, and the dir is gone now
        self.assertEqual(len(created), 1)
        self.assertEqual(seen["cwd"], created[0])
        self.assertIn("q", seen["cmd"])
        self.assertEqual([p for p in created if p.exists()], [])


if __name__ == "__main__":
    unittest.main()
