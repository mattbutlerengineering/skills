"""cli seam tests (ADR-0037, ADR-0040, ADR-0045, ADR-0051): the failure
vocabulary, the one-line detail formatter, the harness-IO
conventions — child_env, version, write_outputs, decode_events, and the
harness_run process-lifecycle contract — and the report epilogue,
asserted at the seam's own
interface. The caller suites (label_sync, validator, budget_guard,
trigger_eval, charter_replay, assembler, cost_report) keep testing their
composition — problem-string labels around a failing runner, step
outputs a workflow consumes — without each re-proving what the seam
does.

harness_run's fakes are real shell scripts run as real subprocesses (the
tests/test_process_reaping.py technique), so the group-kill contract is
proven against live process groups, not mocks; the one mock-driven test
is the kill fallback, where a real stray SIGKILL must never leave the
test.
"""
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import cli

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling capture-helper import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402


class TestReport(unittest.TestCase):
    def test_prints_each_problem_then_the_computed_summary(self):
        code, out = cli_contract.capture(
            cli.report, "tool", ["t: first", "t: second"])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(),
                         ["t: first", "t: second", "tool: 2 problem(s)"])

    def test_no_problems_is_the_zero_summary_and_exit_zero(self):
        code, out = cli_contract.capture(cli.report, "tool", [])
        self.assertEqual(code, 0)
        self.assertEqual(out, "tool: 0 problem(s)\n")

    def test_the_count_is_computed_never_a_literal(self):
        # The budget_guard fork this seam closes: its error path hand-typed
        # "1 problem(s)". Any list length must print through the same
        # computation.
        for problems in (["bg: x"], ["bg: x", "bg: y", "bg: z"]):
            code, out = cli_contract.capture(cli.report, "bg", problems)
            self.assertEqual(code, 1)
            self.assertEqual(out.splitlines()[-1],
                             f"bg: {len(problems)} problem(s)")

    def test_prefix_decorates_before_the_count_clause(self):
        # sweeps' filed clause sits between the label and the count.
        code, out = cli_contract.capture(
            cli.report, "sweeps", [], prefix="3 issue(s) filed, ")
        self.assertEqual(code, 0)
        self.assertEqual(out, "sweeps: 3 issue(s) filed, 0 problem(s)\n")

    def test_suffix_decorates_after_the_count_clause(self):
        # lint's `across N skills` coda.
        code, out = cli_contract.capture(
            cli.report, "lint", ["LINT: bad"], suffix=" across 12 skills")
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(),
                         ["LINT: bad", "lint: 1 problem(s) across 12 skills"])


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


class TestLabelNames(unittest.TestCase):
    def test_names_come_off_an_issue_payload_in_order(self):
        payload = {"labels": [{"name": "wo:merged"}, {"name": "size:M"}]}
        self.assertEqual(cli.label_names(payload), ["wo:merged", "size:M"])

    def test_a_bare_label_listing_works_the_same_way(self):
        # gh label list answers with the array itself, unwrapped.
        self.assertEqual(cli.label_names([{"name": "bug"}]), ["bug"])

    def test_a_nameless_entry_is_dropped_never_coerced(self):
        # One deliberate strictness for every caller: an entry with no
        # usable name yields NO name — not None (the validator's old
        # lifecycle-comparison hazard) and not "" (gate_digest's old
        # coercion). A non-object entry is dropped too, not a traceback.
        payload = {"labels": [{"id": 4321}, {"name": None}, {"name": ""},
                              "junk", {"name": "wo:ready-for-agent"}]}
        self.assertEqual(cli.label_names(payload), ["wo:ready-for-agent"])

    def test_a_missing_or_malformed_labels_key_is_empty(self):
        for payload in ({}, {"labels": None}, {"labels": "wo:merged"}, None):
            with self.subTest(payload=payload):
                self.assertEqual(cli.label_names(payload), [])


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


class TestDecodeEvents(unittest.TestCase):
    """The one JSON-lines decode for every harness stream: undecodable
    and blank lines are skipped, decoded events come back in order."""

    def test_json_lines_decode_and_junk_is_skipped(self):
        lines = ["not json", "", '  {"type": "result"}  ', '{"n": 1}']
        self.assertEqual(list(cli.decode_events(lines)),
                         [{"type": "result"}, {"n": 1}])

    def test_an_empty_iterable_decodes_to_nothing(self):
        self.assertEqual(list(cli.decode_events([])), [])


FAKE_EMITTER = """#!/bin/sh
echo 'not json'
echo '{"type": "result", "result": "ok"}'
"""

FAKE_SLEEPER = """#!/bin/sh
# Spawn a grandchild that outlives us unless the caller kills our group.
sleep 300 &
echo $! > "$PID_FILE"
echo '{"n": 1}'
sleep 300
"""

FAKE_EXITING = """#!/bin/sh
# Leader exits immediately; the grandchild inherits the stdout pipe and
# keeps the process group alive after the leader is gone.
sleep 300 &
echo $! > "$PID_FILE"
exit 0
"""

FAKE_VANISHING = """#!/bin/sh
exit 0
"""

FAKE_ENV_PROBE = """#!/bin/sh
echo "{\\"guard\\": \\"${CLAUDECODE:-absent}\\"}"
"""


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


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


class TestHarnessRun(unittest.TestCase):
    """The streaming-spawn contract (ADR-0045): own process group,
    decoded events while the child runs, and an unconditional group
    SIGKILL on the way out — whether the leader is still running,
    already exited with survivors, or fully gone. Signalled, not
    reaped — killed grandchildren are collected by init, hence the
    grace loops."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="harness-run-"))
        self.pid_file = self.dir / "grandchild.pid"
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        if self.pid_file.is_file():
            pid = int(self.pid_file.read_text())
            if pid_alive(pid):
                os.kill(pid, 9)
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def script(self, body):
        path = self.dir / "fake-harness"
        path.write_text(body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
        return str(path)

    def env(self):
        return {**cli.child_env(), "PID_FILE": str(self.pid_file)}

    def assert_grandchild_reaped(self):
        deadline = time.time() + 2
        while time.time() < deadline and not self.pid_file.is_file():
            time.sleep(0.05)
        self.assertTrue(self.pid_file.is_file(),
                        "fake harness never started")
        pid = int(self.pid_file.read_text())
        deadline = time.time() + 2
        while time.time() < deadline and pid_alive(pid):
            time.sleep(0.05)
        self.assertFalse(pid_alive(pid), "grandchild survived harness_run")

    def test_events_stream_decoded_with_junk_lines_skipped(self):
        cmd = [self.script(FAKE_EMITTER)]
        with cli.harness_run(cmd, cwd=self.dir, timeout=10,
                             env=self.env()) as events:
            self.assertEqual(list(events),
                             [{"type": "result", "result": "ok"}])
        self.assertFalse(events.timed_out)

    def test_a_timeout_flips_timed_out_and_reaps_the_group(self):
        cmd = [self.script(FAKE_SLEEPER)]
        with cli.harness_run(cmd, cwd=self.dir, timeout=2,
                             env=self.env()) as events:
            self.assertEqual(list(events), [{"n": 1}])
        self.assertTrue(events.timed_out)
        self.assert_grandchild_reaped()

    def test_a_dead_leaders_grandchild_is_still_reaped(self):
        # Deterministic by control flow: the fake writes nothing and its
        # grandchild holds the stdout write end open, so the reader can
        # only leave its loop by observing the exit — the cleanup always
        # runs against a dead leader.
        cmd = [self.script(FAKE_EXITING)]
        with cli.harness_run(cmd, cwd=self.dir, timeout=2,
                             env=self.env()) as events:
            self.assertEqual(list(events), [])
        self.assertFalse(events.timed_out)
        self.assert_grandchild_reaped()

    def test_a_fully_exited_group_is_tolerated(self):
        # No grandchild: the reader's poll reaps the leader, leaving the
        # group empty, so the exit group-kill has nothing to signal and
        # must swallow the lookup failure rather than crash the run.
        cmd = [self.script(FAKE_VANISHING)]
        with cli.harness_run(cmd, cwd=self.dir, timeout=2,
                             env=self.env()) as events:
            self.assertEqual(list(events), [])

    def test_the_default_env_strips_the_nesting_guard(self):
        cmd = [self.script(FAKE_ENV_PROBE)]
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1"}):
            with cli.harness_run(cmd, cwd=self.dir, timeout=10) as events:
                self.assertEqual(list(events), [{"guard": "absent"}])

    def test_a_spawn_that_never_starts_raises_into_the_callers_catch(self):
        def no_spawn(*args, **kwargs):
            raise OSError("no harness binary")
        with self.assertRaises(OSError):
            with cli.harness_run(["nope"], cwd=self.dir, timeout=2,
                                 spawn=no_spawn):
                self.fail("the body must never run when spawn fails")

    def test_kill_falls_back_to_the_leader_when_the_group_is_gone(self):
        process = FakeProcess()

        def refuse_killpg(pgid, sig):
            # force the fallback so no real signal leaves the test
            raise ProcessLookupError
        with mock.patch.object(cli.os, "killpg", refuse_killpg):
            with cli.harness_run(["fake"], cwd=self.dir, timeout=2,
                                 spawn=lambda *a, **k: process):
                pass  # never read the mock pipe; the exit path is the test
        self.assertTrue(process.killed)
        self.assertTrue(process.waited)
        process.stdout.close.assert_called_once_with()


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
