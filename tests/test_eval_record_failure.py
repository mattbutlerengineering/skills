"""A paid run's output survives a snapshot that cannot be written
(trigger_eval and charter_replay).

main recorded before it printed the JSON output, so an unwritable
evals/results/ raised past the print: the run's spend bought nothing
the operator could see (audit 2026-11-26).
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import charter_replay
import trigger_eval

RESULT = {"results": [], "summary": {"total": 0, "passed": 0, "failed": 0}}


class TestRecordFailureKeepsTheOutput(unittest.TestCase):
    def test_an_unwritable_results_dir_prints_the_output_and_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "evals").mkdir()
            # A file where the results directory belongs: mkdir refuses.
            (root / "evals" / "results").write_text("not a dir\n")
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(trigger_eval, "ROOT", root), \
                    mock.patch.object(trigger_eval, "run_eval",
                                      return_value=RESULT), \
                    mock.patch.object(trigger_eval.cli, "version",
                                      return_value="test"), \
                    mock.patch.object(trigger_eval, "print_report"), \
                    mock.patch.object(trigger_eval, "load_descriptions",
                                      return_value={}), \
                    mock.patch.object(trigger_eval.eval_schema, "load",
                                      return_value=([], [])), \
                    contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(err):
                code = trigger_eval.main(["--eval-set", "x.json",
                                          "--record"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out.getvalue())["summary"],
                         RESULT["summary"])
        self.assertIn("error: cannot record the results:", err.getvalue())


class TestCharterRecordFailureKeepsTheOutput(unittest.TestCase):
    def test_an_unwritable_results_dir_prints_the_output_and_fails(self):
        summary = {"total": 0, "passed": 0, "failed": 0}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "evals").mkdir()
            (root / "evals" / "results").write_text("not a dir\n")
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.object(charter_replay, "ROOT", root), \
                    mock.patch.object(charter_replay, "load_cases",
                                      return_value=([], [])), \
                    mock.patch.object(charter_replay, "charter_digests",
                                      return_value={}), \
                    mock.patch.object(charter_replay, "run_suite",
                                      return_value={"results": [],
                                                    "summary": summary}), \
                    mock.patch.object(charter_replay, "print_report"), \
                    mock.patch.object(charter_replay.cli, "version",
                                      return_value="test"), \
                    contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(err):
                code = charter_replay.main(["--cases", "x.json",
                                            "--record"])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out.getvalue())["summary"], summary)
        self.assertIn("error: cannot record the results:", err.getvalue())


if __name__ == "__main__":
    unittest.main()
