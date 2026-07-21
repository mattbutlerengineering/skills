"""trigger_eval's offline seams: record(), the only trigger-path writer
through eval_schema.results_path (ADR-0031 harness marking), and
cli_version()'s error-to-None fallback. The eval runs themselves cost
money and never run in CI; everything here is file- and process-local.
"""
import json
import tempfile
import unittest
from pathlib import Path

import trigger_eval


class TestRecord(unittest.TestCase):
    def test_primary_harness_stem_stays_unmarked(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = {"date": "2026-07-21", "harness": "claude",
                      "results": []}
            path = trigger_eval.record(output, Path(tmp))
            self.assertEqual(path.name, "trigger-2026-07-21.json")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")),
                             output)

    def test_second_harness_marks_the_stem(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = {"date": "2026-07-21", "harness": "omp", "results": []}
            path = trigger_eval.record(output, Path(tmp))
            self.assertEqual(path.name, "trigger-omp-2026-07-21.json")

    def test_a_same_day_rerun_appends_a_new_snapshot(self):
        # evals/results/ is append-only (CLAUDE.md): a second run the same
        # day gets -2, and the first file is never rewritten.
        with tempfile.TemporaryDirectory() as tmp:
            output = {"date": "2026-07-21", "harness": "claude"}
            first = trigger_eval.record(output, Path(tmp))
            second = trigger_eval.record(output, Path(tmp))
            self.assertEqual(second.name, "trigger-2026-07-21-2.json")
            self.assertTrue(first.is_file())


class TestCliVersion(unittest.TestCase):
    def test_a_missing_binary_returns_none(self):
        self.assertIsNone(
            trigger_eval.cli_version(harness="no-such-harness-9f3b"))

    def test_a_present_binary_yields_its_version_line(self):
        # `echo --version` stands in for a real harness CLI: BSD echo
        # prints the flag back, GNU echo prints version text — either way
        # a non-empty line, keeping the success path offline.
        self.assertTrue(trigger_eval.cli_version(harness="echo"))
