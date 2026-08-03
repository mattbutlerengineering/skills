"""cli seam tests (ADR-0037, ADR-0040): the failure vocabulary, the
one-line detail formatter, and the harness-IO trio — child_env, version,
write_outputs — asserted at the seam's own interface. The caller suites
(label_sync, validator, budget_guard, trigger_eval, charter_replay,
assembler, cost_report) keep testing their composition — problem-string
labels around a failing runner, step outputs a workflow consumes —
without each re-proving what the seam does.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cli


class TestWriteOutputs(unittest.TestCase):
    def test_multiline_values_use_a_heredoc_delimiter(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.txt"
            cli.write_outputs(
                {"GITHUB_OUTPUT": str(out)},
                {"dispatch": "true", "prompt": "line one\nline two"})
            text = out.read_text(encoding="utf-8")
            self.assertIn("dispatch=true", text)
            self.assertIn("prompt<<", text)
            self.assertIn("line one\nline two", text)

    def test_the_delimiter_carries_no_tool_branding(self):
        # The seam serves every tool that writes step outputs (assembler,
        # cost_report); the delimiter must not name one of them.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.txt"
            cli.write_outputs({"GITHUB_OUTPUT": str(out)},
                              {"prompt": "a\nb"})
            self.assertNotIn("ASM", out.read_text(encoding="utf-8"))

    def test_no_github_output_is_a_silent_no_op(self):
        # Local/hand runs have no GITHUB_OUTPUT; nothing to write, no error.
        cli.write_outputs({}, {"dispatch": "false"})


class TestDetail(unittest.TestCase):
    def test_last_stderr_line_when_the_command_ran(self):
        err = subprocess.CalledProcessError(
            1, ["gh", "issue", "list"],
            stderr="warning: something\nGraphQL: rate limited\n")
        self.assertEqual(cli.detail(err), "GraphQL: rate limited")

    def test_the_os_error_when_the_binary_is_missing(self):
        err = FileNotFoundError(2, "No such file or directory: 'gh'")
        self.assertEqual(cli.detail(err), str(err))

    def test_empty_stderr_falls_back_to_the_error(self):
        err = subprocess.CalledProcessError(1, ["git", "push"], stderr="  \n")
        self.assertEqual(cli.detail(err), str(err))


class TestFailureVocabulary(unittest.TestCase):
    def test_covers_ran_and_failed_and_never_ran(self):
        # The three ways a shell-out goes wrong: ran-and-failed and
        # never-ran raise CLI_FAILURES; ran-but-said-nonsense is gh_json's
        # (None, suffix). Callers catch CLI_FAILURES, never a bare
        # Exception — JSONDecodeError (a ValueError) stays excluded so the
        # third mode can't hide inside the first two.
        self.assertTrue(issubclass(subprocess.CalledProcessError,
                                   cli.CLI_FAILURES))
        self.assertTrue(issubclass(FileNotFoundError, cli.CLI_FAILURES))
        self.assertFalse(issubclass(ValueError, cli.CLI_FAILURES))


class TestGhJson(unittest.TestCase):
    def test_covers_ran_succeeded_and_said_nonsense(self):
        value, suffix = cli.gh_json([], run=lambda args: "gh: banner text")
        self.assertIsNone(value)
        self.assertEqual(suffix, "returned unparseable JSON: Expecting"
                         " value: line 1 column 1 (char 0)")

    def test_a_wrong_top_level_shape_is_a_suffix_not_a_crash(self):
        value, suffix = cli.gh_json([], run=lambda args: "{}", expect=list)
        self.assertEqual((value, suffix),
                         (None, "returned dict where list was expected"))

    def test_parsed_json_of_the_expected_shape_passes_through(self):
        value, suffix = cli.gh_json([], run=lambda args: '[{"a": 1}]',
                                    expect=list)
        self.assertEqual((value, suffix), ([{"a": 1}], None))

    def test_a_failed_gh_still_raises_for_the_callers_catch(self):
        def failing(args):
            raise subprocess.CalledProcessError(1, ["gh", *args])
        with self.assertRaises(subprocess.CalledProcessError):
            cli.gh_json(["issue", "list"], run=failing)


class TestFullWindow(unittest.TestCase):
    def test_a_full_window_is_a_problem_suffix(self):
        self.assertEqual(
            cli.full_window([{}] * 1000, 1000),
            "returned a full 1000-entry window — older entries"
            " are invisible; raise the window or narrow the query")

    def test_a_partial_window_is_fine(self):
        self.assertIsNone(cli.full_window([{}], 1000))


class TestChildEnv(unittest.TestCase):
    def test_strips_the_nesting_guard_and_keeps_the_rest(self):
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1",
                                          "KEEP_ME": "x"}):
            env = cli.child_env()
        self.assertNotIn("CLAUDECODE", env)
        self.assertEqual(env["KEEP_ME"], "x")

    def test_returns_a_copy_not_the_environ(self):
        env = cli.child_env()
        env["MUTATED"] = "locally"
        self.assertNotIn("MUTATED", os.environ)


class TestVersion(unittest.TestCase):
    def test_a_missing_binary_probes_to_none(self):
        self.assertIsNone(cli.version("definitely-not-a-binary-xyzzy"))

    def test_a_present_binary_reports_its_version_line(self):
        # echo prints its argv back, so the probe sees non-empty stdout;
        # asserting truthiness keeps this portable across BSD/GNU echo.
        self.assertTrue(cli.version("echo"))


class TestRunner(unittest.TestCase):
    def test_a_missing_binary_raises_into_the_vocabulary(self):
        run = cli.runner("definitely-not-a-binary-xyzzy")
        with self.assertRaises(cli.CLI_FAILURES):
            run(["--version"])

    def test_a_real_run_returns_the_completed_process(self):
        run = cli.runner("true")
        self.assertEqual(run([]).returncode, 0)


class TestGhRunner(unittest.TestCase):
    def test_the_gh_port_returns_stdout_and_forwards_args(self):
        # The port over runner("gh"): callers get stdout, failures raise
        # CLI_FAILURES for them to label. Patched because a real gh call
        # is network + auth; the caller suites inject fakes end to end.
        fake = mock.Mock(return_value=subprocess.CompletedProcess(
            ["gh"], 0, stdout="[]", stderr=""))
        with mock.patch.object(cli, "_gh", fake):
            self.assertEqual(cli.gh_runner(["label", "list"]), "[]")
        fake.assert_called_once_with(["label", "list"])


class TestReadEvent(unittest.TestCase):
    def test_no_event_path_is_a_silent_none(self):
        # Absence is a fact, not an error: a hand/local run has no event.
        # Each caller judges it (detector B skips; the assembler objects).
        self.assertEqual(cli.read_event({}), (None, None))

    def test_a_payload_object_comes_back_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text('{"action": "labeled"}', encoding="utf-8")
            self.assertEqual(
                cli.read_event({"GITHUB_EVENT_PATH": str(path)}),
                ({"action": "labeled"}, None))

    def test_an_unreadable_path_is_an_unlabeled_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "nope" / "event.json")
            event, error = cli.read_event({"GITHUB_EVENT_PATH": missing})
            self.assertIsNone(event)
            self.assertTrue(error.startswith(
                f"cannot read GITHUB_EVENT_PATH {missing}:"), error)

    def test_malformed_json_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text("{not json", encoding="utf-8")
            event, error = cli.read_event({"GITHUB_EVENT_PATH": str(path)})
            self.assertIsNone(event)
            self.assertTrue(error.startswith(
                f"cannot read GITHUB_EVENT_PATH {path}:"), error)

    def test_a_non_object_payload_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text("[1, 2]", encoding="utf-8")
            self.assertEqual(
                cli.read_event({"GITHUB_EVENT_PATH": str(path)}),
                (None, f"GITHUB_EVENT_PATH {path} is not a JSON object"))


if __name__ == "__main__":
    unittest.main()
