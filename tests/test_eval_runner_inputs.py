"""Each eval runner's offline input gets one guarded, shape-checked load.

charter_replay's --transcripts file and trigger_eval's --metrics snapshot
are user input named on the command line. Both used to be a pass-through
json.loads whose shape five functions downstream assumed, so a wrong
file raised a traceback where a problem string belongs (#746). Each now
loads through cli.read_file (ADR-0075) and checks its shape once, in its
own runner: a bad file exits 1 with exact problem strings and no
traceback, and nothing is scored or printed from it.
"""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import charter_replay  # noqa: E402
import trigger_eval  # noqa: E402

HUGE_INTEGER = "1" * 5000  # past the interpreter's int-string digit limit
OK_TRANSCRIPT = {"tool_calls": [], "text": "done"}


class InputFile(unittest.TestCase):
    def write(self, name, text):
        tmp = Path(tempfile.mkdtemp(prefix="eval-input-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def errors(self, err):
        return [line for line in err.splitlines()
                if line.startswith("error: ")]


class TestTranscriptsLoad(InputFile):
    def replay(self, value, *extra, raw=None):
        path = self.write("transcripts.json",
                          raw if raw is not None else json.dumps(value))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = charter_replay.main(["--transcripts", str(path), *extra])
        return code, path, out.getvalue(), self.errors(err.getvalue())

    def test_a_json_array_is_a_problem(self):
        code, path, out, errors = self.replay([OK_TRANSCRIPT])
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(errors, [f"error: {path} is not a JSON object"])

    def test_a_json_string_is_a_problem(self):
        code, path, out, errors = self.replay("transcripts")
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(errors, [f"error: {path} is not a JSON object"])

    def test_a_non_object_transcript_is_a_problem(self):
        code, path, out, errors = self.replay(
            {"swe-asked-to-push-main": ["not", "a", "transcript"]})
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(errors, [
            f"error: {path} 'swe-asked-to-push-main' is not a transcript"
            " object"])

    def test_a_malformed_transcript_names_each_bad_field(self):
        code, path, out, errors = self.replay(
            {"c": {"tool_calls": ["Bash"], "text": 7}})
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(errors, [
            f"error: {path} 'c' tool_calls is not a list of objects",
            f"error: {path} 'c' text is not a string"])

    def test_a_huge_integer_literal_is_reported_not_raised(self):
        code, path, out, errors = self.replay(
            None, raw='{"c": {"n": %s}}' % HUGE_INTEGER)
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith(
            f"error: {path} is not valid JSON: "), errors[0])

    def test_bytes_that_are_not_utf8_are_reported_not_raised(self):
        path = self.write("transcripts.json", "")
        path.write_bytes('{"café": 1}'.encode("latin-1"))
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = charter_replay.main(["--transcripts", str(path)])
        self.assertEqual(code, 1)
        self.assertTrue(self.errors(err.getvalue())[0].startswith(
            f"error: {path} is not valid JSON: "))

    def test_a_missing_file_is_a_problem(self):
        path = self.write("present.json", "{}").parent / "absent.json"
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = charter_replay.main(["--transcripts", str(path)])
        self.assertEqual(code, 1)
        self.assertEqual(self.errors(err.getvalue()),
                         [f"error: missing {path}"])

    def test_control_with_a_non_object_top_level_is_a_problem(self):
        code, path, out, errors = self.replay([1, 2], "--control")
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(errors, [f"error: {path} is not a JSON object"])

    def test_control_with_a_non_object_pair_is_a_problem(self):
        code, path, out, errors = self.replay({"c": "intact"}, "--control")
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(errors, [
            f"error: {path} 'c' is not an object of intact/degraded"
            " transcripts"])

    def test_control_checks_each_arm_it_carries(self):
        code, path, out, errors = self.replay(
            {"c": {"intact": OK_TRANSCRIPT, "degraded": 3}}, "--control")
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(errors, [
            f"error: {path} 'c' degraded is not a transcript object"])

    def test_a_well_shaped_file_is_returned_unchanged(self):
        data = {"c": OK_TRANSCRIPT, "d": {"text": None}}
        path = self.write("t.json", json.dumps(data))
        self.assertEqual(charter_replay.load_transcripts(str(path), False),
                         (data, []))


class TestMetricsLoad(InputFile):
    def metrics(self, value, raw=None):
        path = self.write("results.json",
                          raw if raw is not None else json.dumps(value))
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv",
                               ["trigger_eval.py", "--metrics", str(path)]), \
                contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
            code = trigger_eval.main()
        return code, path, out.getvalue(), self.errors(err.getvalue())

    def test_a_charter_snapshot_is_refused(self):
        snapshot = json.loads(
            (ROOT / "evals" / "results" / "charter-2026-09-28.json")
            .read_text(encoding="utf-8"))
        code, path, out, errors = self.metrics(snapshot)
        self.assertEqual((code, out), (1, ""))
        self.assertTrue(errors)
        self.assertEqual(errors[0], f"error: {path} result #0 is not a"
                         " trigger result (fired, kind, expected, pass)")

    def test_an_array_is_refused(self):
        code, path, out, errors = self.metrics([])
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(errors, [f"error: {path} is not a JSON object"])

    def test_an_object_without_results_is_refused(self):
        code, path, out, errors = self.metrics({"date": "2026-10-12"})
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(errors, [f"error: {path} has no results list"])

    def test_a_huge_integer_literal_is_reported_not_raised(self):
        code, path, out, errors = self.metrics(
            None, raw='{"results": [], "n": %s}' % HUGE_INTEGER)
        self.assertEqual((code, out), (1, ""))
        self.assertTrue(errors[0].startswith(
            f"error: {path} is not valid JSON: "), errors)

    def test_a_missing_file_is_refused(self):
        path = self.write("present.json", "{}").parent / "absent.json"
        with mock.patch.object(sys, "argv",
                               ["trigger_eval.py", "--metrics", str(path)]):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = trigger_eval.main()
        self.assertEqual(code, 1)
        self.assertEqual(self.errors(err.getvalue()),
                         [f"error: missing {path}"])

    def test_every_recorded_trigger_snapshot_loads_clean(self):
        paths = sorted((ROOT / "evals" / "results").glob("trigger*.json"))
        self.assertTrue(paths, "no recorded trigger snapshots to load")
        for path in paths:
            output, problems = trigger_eval.load_results(path)
            self.assertEqual(problems, [], path.name)
            self.assertIsInstance(output["results"], list)


if __name__ == "__main__":
    unittest.main()
