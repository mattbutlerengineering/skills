"""cli seam tests (ADR-0037, ADR-0040, ADR-0053, ADR-0051): the failure
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
tests/test_cli_process_reaping.py technique), so the group-kill contract is
proven against live process groups, not mocks; the one mock-driven test
is the kill fallback, where a real stray SIGKILL must never leave the
test.
"""
import json
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

    def parse_as_actions(self, text):
        """How the runner reads $GITHUB_OUTPUT: a heredoc body ends at the
        first line equal to the delimiter, and anything after it is read
        as further assignments."""
        parsed, lines, i = {}, text.split("\n"), 0
        while i < len(lines):
            line = lines[i]
            if "<<" in line:
                key, delim = line.split("<<", 1)
                body = []
                i += 1
                while i < len(lines) and lines[i] != delim:
                    body.append(lines[i])
                    i += 1
                parsed[key] = "\n".join(body)
            elif "=" in line:
                key, value = line.split("=", 1)
                parsed[key] = value
            i += 1
        return parsed

    def test_a_value_cannot_forge_an_output(self):
        """The delimiter must not be derivable from the key. Otherwise a
        multiline value carrying that line closes its own heredoc, and the
        rest of it is read as assignments — here flipping `dispatch`, the
        flag that decides whether the factory dispatches an agent at all,
        and adding a `model` the caller never wrote."""
        poisoned = ("do the work\n__PROMPT_EOF__\n"
                    "dispatch=true\nmodel=expensive-model")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.txt"
            cli.write_outputs({"GITHUB_OUTPUT": str(out)},
                              {"dispatch": "false", "prompt": poisoned})
            parsed = self.parse_as_actions(out.read_text(encoding="utf-8"))
        self.assertEqual(parsed["dispatch"], "false")
        self.assertNotIn("model", parsed)
        self.assertEqual(parsed["prompt"], poisoned)

    def test_the_delimiter_differs_between_calls(self):
        # Same key, two calls: a delimiter an author could predict from a
        # previous run is still guessable.
        seen = set()
        for _ in range(2):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "out.txt"
                cli.write_outputs({"GITHUB_OUTPUT": str(out)},
                                  {"prompt": "a\nb"})
                first = out.read_text(encoding="utf-8").split("\n")[0]
            seen.add(first.split("<<", 1)[1])
        self.assertEqual(len(seen), 2, "delimiter repeated across calls")

    def test_a_delimiter_that_collides_is_regenerated(self):
        """Randomness makes collision negligible, not impossible. Forcing
        the first draw to land inside the body proves the invariant holds
        by construction rather than by luck — the silent-collision case is
        the one the loop exists for."""
        draws = iter(["c0ffee", "c0ffee", "d1ffe0"])
        body = "line one\n__EOF_c0ffee__\nline two"
        with mock.patch.object(cli.secrets, "token_hex",
                               side_effect=lambda n: next(draws)):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "out.txt"
                cli.write_outputs({"GITHUB_OUTPUT": str(out)},
                                  {"prompt": body})
                text = out.read_text(encoding="utf-8")
        self.assertIn("prompt<<__EOF_d1ffe0__", text)
        self.assertEqual(self.parse_as_actions(text)["prompt"], body)


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

    def test_a_timed_out_childs_bytes_stderr_is_decoded(self):
        # subprocess.run attaches the child's UNDECODED stderr to a
        # TimeoutExpired even in text mode, so a hung vhs that wrote a
        # line would otherwise surface as a bytes repr in the problem.
        err = subprocess.TimeoutExpired(["vhs"], 600,
                                        stderr=b"ttyd: not found\n")
        self.assertEqual(cli.detail(err), "ttyd: not found")


class TestFailureVocabulary(unittest.TestCase):
    def test_covers_ran_and_failed_and_never_ran(self):
        # The three ways a shell-out goes wrong: ran-and-failed and
        # never-ran raise CLI_FAILURES; ran-but-said-nonsense is the
        # unparseable-JSON problem gh_read reports. A caller that still
        # catches (budget_guard's git calls, the gh mutations) catches
        # CLI_FAILURES, never a bare Exception — JSONDecodeError (a
        # ValueError) stays excluded so the third mode can't hide inside
        # the first two.
        self.assertTrue(issubclass(subprocess.CalledProcessError,
                                   cli.CLI_FAILURES))
        self.assertTrue(issubclass(FileNotFoundError, cli.CLI_FAILURES))
        self.assertFalse(issubclass(ValueError, cli.CLI_FAILURES))


class TestGhRead(unittest.TestCase):
    """The whole windowed gh read as one call: run gh, catch the binary's
    failure vocabulary, parse and shape-check the JSON, own the window
    (both the --limit it sends and the truncation it reports), and answer
    with already-prefixed problem strings. The five facts fourteen call
    sites each carried by hand, none of them in a signature."""

    @staticmethod
    def _recorder(out):
        """A fake gh port that records the argv it was handed."""
        seen = []

        def run(args):
            seen.append(list(args))
            return out
        return run, seen

    def test_a_failed_gh_is_a_problem_not_the_callers_catch(self):
        def failing(args):
            raise subprocess.CalledProcessError(
                1, ["gh", *args], stderr="GraphQL: rate limited\n")
        result = cli.gh_read(["issue", "list"], "gh issue list",
                            label="gd", run=failing)
        self.assertIsNone(result.value)
        self.assertEqual(result.problems,
                         ["gd: gh issue list failed: GraphQL: rate limited"])
        self.assertFalse(result.truncated)

    def test_ran_and_said_nonsense_is_a_prefixed_problem(self):
        result = cli.gh_read([], "gh pr list", label="asm",
                            run=lambda args: "gh: banner text")
        self.assertIsNone(result.value)
        self.assertEqual(result.problems,
                         ["asm: gh pr list returned unparseable JSON:"
                          " Expecting value: line 1 column 1 (char 0)"])
        self.assertFalse(result.truncated)

    def test_a_wrong_top_level_shape_is_a_prefixed_problem(self):
        result = cli.gh_read([], "gh issue list", label="wq",
                            run=lambda args: "{}", expect=list)
        self.assertIsNone(result.value)
        self.assertEqual(
            result.problems,
            ["wq: gh issue list returned dict where list was expected"])

    def test_a_dict_read_names_its_own_expected_shape(self):
        result = cli.gh_read([], "gh issue view 12", label="V",
                            run=lambda args: "[]", expect=dict)
        self.assertIsNone(result.value)
        self.assertEqual(
            result.problems,
            ["V: gh issue view 12 returned list where dict was expected"])

    def test_a_clean_read_is_the_value_and_no_problems(self):
        result = cli.gh_read([], "gh pr list", label="asm",
                            run=lambda args: '[{"number": 4}]')
        self.assertEqual(result.value, [{"number": 4}])
        self.assertEqual(result.problems, [])
        self.assertFalse(result.truncated)

    def test_a_full_window_is_truncated_with_the_shared_sentence(self):
        payload = json.dumps([{}] * 3)
        result = cli.gh_read([], "gh issue list", label="gd",
                            run=lambda args: payload, window=3)
        # The value stays usable — the caller decides what truncation
        # means here (seven report and continue, two refuse outright).
        self.assertEqual(result.value, [{}] * 3)
        self.assertTrue(result.truncated)
        self.assertEqual(result.problems,
                         ["gd: gh issue list returned a full 3-entry window"
                          " — older entries are invisible; raise the window"
                          " or narrow the query"])

    def test_a_partial_window_is_not_truncated(self):
        result = cli.gh_read([], "gh issue list", label="gd",
                            run=lambda args: '[{}]', window=1000)
        self.assertFalse(result.truncated)
        self.assertEqual(result.problems, [])

    def test_an_unwindowed_read_is_never_truncated(self):
        # The four timeline/issue-view reads pass no window; a long
        # listing must not invent a truncation report for them.
        result = cli.gh_read([], "gh api timeline for #12", label="rm",
                            run=lambda args: json.dumps([{}] * 5000))
        self.assertFalse(result.truncated)
        self.assertEqual(result.problems, [])

    def test_the_window_reaches_gh_as_a_trailing_limit(self):
        run, seen = self._recorder("[]")
        cli.gh_read(["issue", "list", "--json", "number"], "gh issue list",
                    label="wq", run=run, window=100)
        # The limit sent and the limit the truncation check tests are the
        # same number by construction — work_queue's duplicate literal has
        # nowhere left to live.
        self.assertEqual(seen,
                         [["issue", "list", "--json", "number",
                           "--limit", "100"]])

    def test_an_unwindowed_read_sends_no_limit(self):
        run, seen = self._recorder("{}")
        cli.gh_read(["issue", "view", "12", "--json", "labels"],
                    "gh issue view 12", label="V", run=run, expect=dict)
        self.assertEqual(seen, [["issue", "view", "12", "--json", "labels"]])

    def test_the_callers_args_are_not_mutated(self):
        args = ["issue", "list"]
        cli.gh_read(args, "gh issue list", run=lambda a: "[]", window=500)
        self.assertEqual(args, ["issue", "list"])

    def test_no_label_leaves_the_problems_unprefixed(self):
        # label_sync.live_labels' three callers each own a different
        # label (L:, sweeps:), so the reader must not pick one.
        err = FileNotFoundError(2, "No such file or directory: 'gh'")

        def failing(args):
            raise err
        result = cli.gh_read([], "gh label list", run=failing)
        self.assertEqual(result.problems,
                         [f"gh label list failed: {err}"])
        unparseable = cli.gh_read([], "gh label list",
                                  run=lambda args: "not json")
        self.assertEqual(unparseable.problems,
                         ["gh label list returned unparseable JSON:"
                          " Expecting value: line 1 column 1 (char 0)"])

    def test_full_note_replaces_the_shared_sentence(self):
        # sweeps.known_keys says what a full window costs THERE; the seam
        # states the fact, the meaning stays local.
        note = ("returned a full 500-issue window; intake keys older than"
                " it are invisible and would be re-filed as duplicates")
        result = cli.gh_read([], "gh issue list", label="sweeps",
                            run=lambda args: json.dumps([{}] * 500),
                            window=500, full_note=note)
        self.assertTrue(result.truncated)
        self.assertEqual(result.problems, [f"sweeps: gh issue list {note}"])


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

    def test_a_timeout_raises_into_the_vocabulary(self):
        run = cli.runner("bash", timeout=0.5)
        with self.assertRaises(subprocess.TimeoutExpired):
            run(["-c", "sleep 5"])
        try:
            run(["-c", "sleep 5"])
        except cli.CLI_FAILURES:
            pass
        else:
            self.fail("TimeoutExpired is not in CLI_FAILURES")

    def test_stdin_input_reaches_the_child(self):
        run = cli.runner("cat")
        self.assertEqual(run([], input="hello\n").stdout, "hello\n")


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

# The fakes publish the PID file by rename, never by writing it in
# place: `>` creates the file before echo fills it, so a group kill
# landing between the two leaves it present and empty, and reading it
# dies on int('') instead of reporting on the grandchild.
FAKE_SLEEPER = """#!/bin/sh
# Spawn a grandchild that outlives us unless the caller kills our group.
sleep 300 &
echo $! > "$PID_FILE.tmp" && mv "$PID_FILE.tmp" "$PID_FILE"
echo '{"n": 1}'
sleep 300
"""

FAKE_EXITING = """#!/bin/sh
# Leader exits immediately; the grandchild inherits the stdout pipe and
# keeps the process group alive after the leader is gone.
sleep 300 &
echo $! > "$PID_FILE.tmp" && mv "$PID_FILE.tmp" "$PID_FILE"
exit 0
"""

FAKE_VANISHING = """#!/bin/sh
exit 0
"""

FAKE_ENV_PROBE = """#!/bin/sh
echo "{\\"guard\\": \\"${CLAUDECODE:-absent}\\"}"
: > "$READY_FILE"
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
    loop in assert_grandchild_reaped polls this predicate to decide
    whether a killed grandchild is gone, so counting a zombie as alive
    reports a grandchild that is already dead as a survivor.
    """
    state = process_state(pid)
    return state is not None and not state.startswith("Z")


class ReadinessGatedClock:
    """Stands in for cli's `time` module so a harness timeout counts
    from the fake's readiness, not from its spawn.

    A timeout counted from spawn races the fake's own startup: under
    load a cold spawn can outlast it, and the reader abandons a fake
    that has not yet written anything. This clock holds still until
    `marker` exists (the fake's readiness handshake), then runs at real
    speed from where it stood, so the fake always gets its whole timeout
    after it is set up. A fake that never gets ready releases the clock
    after `ceiling` real seconds, so the test fails instead of hanging.
    The tests/test_cli_process_reaping.py copy is the same clock.
    """

    def __init__(self, marker, ceiling=60):
        self.marker = marker
        self.ceiling = ceiling
        self.start = time.time()
        self.held = None  # seconds spent holding still, once released

    def time(self):
        now = time.time()
        if self.held is None:
            waiting = now - self.start < self.ceiling
            if waiting and not self.marker.is_file():
                return self.start
            self.held = now - self.start
        return now - self.held


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
    """The streaming-spawn contract (ADR-0053): own process group,
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
            # pid_alive then kill is a race: a grandchild that exits between
            # the two raises ProcessLookupError, and a dead one needs no kill.
            if pid_alive(pid):
                try:
                    os.kill(pid, 9)
                except ProcessLookupError:
                    pass
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

    def gated_on_the_grandchild(self):
        """The harness timeout counts from the PID file, not the spawn:
        a spawn stall past a spawn-counted timeout kills the fake before
        its grandchild exists, or abandons a leader that has not yet
        exited, and either reads as a harness failure (beads wo-yjq)."""
        return mock.patch.object(cli, "time",
                                 ReadinessGatedClock(self.pid_file))

    def test_a_timeout_flips_timed_out_and_reaps_the_group(self):
        cmd = [self.script(FAKE_SLEEPER)]
        with self.gated_on_the_grandchild():
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
        with self.gated_on_the_grandchild():
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
        # The timeout clock starts once the probe has written its line,
        # not at the spawn: under load a cold spawn can outlast any
        # timeout counted from spawn, and the reader then abandons the
        # run before the line exists (issue #446, beads wo-hdl). The
        # happy path never reaches the timeout — it returns at EOF.
        ready = self.dir / "ready"
        cmd = [self.script(FAKE_ENV_PROBE)]
        env = {"CLAUDECODE": "1", "READY_FILE": str(ready)}
        with mock.patch.dict(os.environ, env), \
                mock.patch.object(cli, "time", ReadinessGatedClock(ready)):
            with cli.harness_run(cmd, cwd=self.dir, timeout=20) as events:
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

    def test_the_factory_override_wins_over_the_runner_path(self):
        """A step cannot overwrite GITHUB_EVENT_PATH through $GITHUB_ENV
        (GitHub protects GITHUB_* defaults), so validator.yml's dispatch
        shims hand their synthesized payload over as FACTORY_EVENT_PATH."""
        with tempfile.TemporaryDirectory() as tmp:
            runner = Path(tmp) / "dispatch.json"
            runner.write_text('{"inputs": {"pr": "7"}}', encoding="utf-8")
            synthesized = Path(tmp) / "pr-event.json"
            synthesized.write_text('{"pull_request": {"number": 7}}',
                                   encoding="utf-8")
            self.assertEqual(
                cli.read_event({"GITHUB_EVENT_PATH": str(runner),
                                "FACTORY_EVENT_PATH": str(synthesized)}),
                ({"pull_request": {"number": 7}}, None))

    def test_an_unreadable_override_names_the_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "nope.json")
            event, error = cli.read_event({"FACTORY_EVENT_PATH": missing})
            self.assertIsNone(event)
            self.assertTrue(error.startswith(
                f"cannot read FACTORY_EVENT_PATH {missing}:"), error)

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

    def test_bytes_that_are_not_utf8_are_an_error(self):
        """The docstring promises an *unreadable* payload comes back as
        an error string. A file whose bytes are not UTF-8 is unreadable
        as text — and under RFC 8259 §8.1 not valid JSON either — so it
        lands in the same error as the malformed case above."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_bytes('{"action": "caf\u00e9"}'.encode("latin-1"))
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


class TestReadFile(unittest.TestCase):
    """read_file — the guarded local-file read (ADR-0075), asserted as
    the exact (value, problem) pair for every kind against real temp
    files. The readers that adopt it keep testing their own half — the
    label they prefix and what absence means to them — without each
    re-proving the failure vocabulary."""

    SHOWN = "docs/thing.json"
    KINDS = (str, dict, list)
    NOT_UTF8 = ("'utf-8' codec can't decode byte 0xff in position 0:"
                " invalid start byte")
    NOT_JSON = ("Expecting property name enclosed in double quotes:"
                " line 1 column 2 (char 1)")
    EMPTY = "Expecting value: line 1 column 1 (char 0)"
    TOO_MANY_DIGITS = ("Exceeds the limit (4300 digits) for integer string"
                       " conversion: value has 5000 digits; use"
                       " sys.set_int_max_str_digits() to increase the limit")

    def read(self, data, kind):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "thing.json"
            path.write_bytes(data)
            return cli.read_file(path, self.SHOWN, kind)

    def assert_pairs(self, data, expected):
        """expected maps each kind to its exact pair; a value must also
        be the expected TYPE, because True == 1 would let a bool pass
        for a number."""
        self.assertEqual(set(expected), set(self.KINDS))
        for kind, pair in expected.items():
            with self.subTest(kind=kind.__name__):
                got = self.read(data, kind)
                self.assertEqual(got, pair)
                self.assertIs(type(got[0]), type(pair[0]))

    def test_an_unknown_kind_is_a_value_error_at_the_call(self):
        """A kind that is not str, dict or list is a slip in the caller,
        never a failure of the file: it raises whether the file is
        there or not, and before the path is touched at all — a wrong
        kind must not pass for a read that found nothing wrong."""
        class Touched:
            def __fspath__(self):
                raise AssertionError("the path was touched")

        must = "read_file kind must be str, dict or list, not "
        with tempfile.TemporaryDirectory() as tmp:
            present = Path(tmp) / "thing.json"
            present.write_text('{"a": 1}', encoding="utf-8")
            paths = (("present", present),
                     ("absent", Path(tmp) / "nope.json"),
                     ("raises if touched", Touched()))
            for kind, message in ((object, must + "<class 'object'>"),
                                  ("dict", must + "'dict'"),
                                  (int, must + "<class 'int'>")):
                for name, path in paths:
                    with self.subTest(kind=kind, path=name):
                        with self.assertRaises(ValueError) as caught:
                            cli.read_file(path, self.SHOWN, kind)
                        self.assertEqual(str(caught.exception), message)

    def test_an_absent_file_is_none_none_for_every_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            for kind in self.KINDS:
                with self.subTest(kind=kind.__name__):
                    self.assertEqual(
                        cli.read_file(Path(tmp) / "nope.json", self.SHOWN,
                                      kind),
                        (None, None))

    def test_a_directory_in_its_place_counts_as_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "thing.json").mkdir()
            for kind in self.KINDS:
                with self.subTest(kind=kind.__name__):
                    self.assertEqual(
                        cli.read_file(Path(tmp) / "thing.json", self.SHOWN,
                                      kind),
                        (None, None))

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-000 file")
    def test_an_unreadable_file_is_cannot_read_for_every_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "thing.json"
            path.write_text('{"a": 1}', encoding="utf-8")
            path.chmod(0)
            try:
                for kind in self.KINDS:
                    with self.subTest(kind=kind.__name__):
                        self.assertEqual(
                            cli.read_file(path, self.SHOWN, kind),
                            (None, f"cannot read {self.SHOWN}: [Errno 13]"
                                   f" Permission denied: '{path}'"))
            finally:
                path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def test_bytes_that_are_not_utf8(self):
        """The ADR-0075 wording rule: a text reader has no grammar to
        blame, so the bytes are a read failure; a JSON reader's document
        must be UTF-8 (RFC 8259 §8.1), so they are a defect in it."""
        not_json = (None, f"{self.SHOWN} is not valid JSON: {self.NOT_UTF8}")
        self.assert_pairs(b"\xff\xfe", {
            str: (None, f"cannot read {self.SHOWN}: {self.NOT_UTF8}"),
            dict: not_json, list: not_json})

    def test_text_that_is_not_json(self):
        not_json = (None, f"{self.SHOWN} is not valid JSON: {self.NOT_JSON}")
        self.assert_pairs(b"{nope", {
            str: ("{nope", None),
            dict: not_json, list: not_json})

    def test_an_empty_file(self):
        not_json = (None, f"{self.SHOWN} is not valid JSON: {self.EMPTY}")
        self.assert_pairs(b"", {
            str: ("", None),
            dict: not_json, list: not_json})

    def test_an_integer_literal_past_the_digit_limit(self):
        """json.loads raises a plain ValueError, not a JSONDecodeError,
        for an integer literal longer than the interpreter's digit
        limit. It is a parse failure like any other. The text embeds
        the default limit, so PYTHONINTMAXSTRDIGITS must be unset."""
        not_json = (None, f"{self.SHOWN} is not valid JSON:"
                          f" {self.TOO_MANY_DIGITS}")
        self.assert_pairs(b"1" * 5000, {
            str: ("1" * 5000, None),
            dict: not_json, list: not_json})

    def test_arrays_nested_past_the_recursion_limit(self):
        """json.loads raises RecursionError for nesting it cannot
        follow. Only the prefix is pinned: the rest is the interpreter's
        and differs by version (a recursion depth on 3.12, the C stack
        from 3.14 on, which is why the document is a million arrays
        deep). The last read pins that the interpreter is usable
        afterwards."""
        depth = 1_000_000
        data = b"[" * depth + b"]" * depth
        for kind in (dict, list):
            with self.subTest(kind=kind.__name__):
                value, problem = self.read(data, kind)
                self.assertIsNone(value)
                self.assertTrue(problem.startswith(
                    f"{self.SHOWN} is not valid JSON: "), problem)
        text, problem = self.read(data, str)
        self.assertIsNone(problem)
        self.assertEqual(text, data.decode("ascii"))
        self.assertEqual(self.read(b'{"a": 1}', dict), ({"a": 1}, None))

    def test_a_json_object(self):
        self.assert_pairs(b'{"a": 1}', {
            str: ('{"a": 1}', None),
            dict: ({"a": 1}, None),
            list: (None, f"{self.SHOWN} is not a JSON array")})

    def test_a_json_array(self):
        self.assert_pairs(b'["a"]', {
            str: ('["a"]', None),
            dict: (None, f"{self.SHOWN} is not a JSON object"),
            list: (["a"], None)})

    def test_a_json_string(self):
        self.assert_pairs(b'"a"', {
            str: ('"a"', None),
            dict: (None, f"{self.SHOWN} is not a JSON object"),
            list: (None, f"{self.SHOWN} is not a JSON array")})

    def test_a_json_null(self):
        self.assert_pairs(b"null", {
            str: ("null", None),
            dict: (None, f"{self.SHOWN} is not a JSON object"),
            list: (None, f"{self.SHOWN} is not a JSON array")})

    def test_a_json_number(self):
        self.assert_pairs(b"5", {
            str: ("5", None),
            dict: (None, f"{self.SHOWN} is not a JSON object"),
            list: (None, f"{self.SHOWN} is not a JSON array")})

    def test_json_true(self):
        self.assert_pairs(b"true", {
            str: ("true", None),
            dict: (None, f"{self.SHOWN} is not a JSON object"),
            list: (None, f"{self.SHOWN} is not a JSON array")})

    def test_json_false(self):
        self.assert_pairs(b"false", {
            str: ("false", None),
            dict: (None, f"{self.SHOWN} is not a JSON object"),
            list: (None, f"{self.SHOWN} is not a JSON array")})

    def test_every_non_object_top_level_is_one_problem_under_dict(self):
        """The object rule both config readers shared before it moved
        here (factory_config.object_problems' cells): every JSON top
        level that is not an object is the same one problem."""
        for value in (None, [], ["a"], "factory", 5, 0.5, True, False):
            with self.subTest(value=value):
                self.assertEqual(
                    self.read(json.dumps(value).encode("utf-8"), dict),
                    (None, f"{self.SHOWN} is not a JSON object"))

    def test_shown_is_echoed_verbatim(self):
        """The problem names the file as the caller's `shown`, never as
        the path it read — and a Path formats as its own text."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "thing.json"
            path.write_text("[]", encoding="utf-8")
            for shown in ("any name at all", Path("docs") / "thing.json"):
                with self.subTest(shown=shown):
                    self.assertEqual(
                        cli.read_file(path, shown, dict),
                        (None, f"{shown} is not a JSON object"))
            self.assertEqual(
                cli.read_file(str(path), Path("docs") / "thing.json", dict),
                (None, "docs/thing.json is not a JSON object"))

    @unittest.skipIf(os.geteuid() == 0, "root searches a mode-000 directory")
    def test_an_unsearchable_parent_never_raises(self):
        """Path.is_file raises PermissionError under an unsearchable
        parent before Python 3.14 and answers False from 3.14 on, so the
        outcome is a problem on one and absence on the other. Only the
        promise is pinned: nothing raises, and no value comes back."""
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "locked"
            parent.mkdir()
            (parent / "thing.json").write_text('{"a": 1}', encoding="utf-8")
            parent.chmod(0)
            try:
                for kind in self.KINDS:
                    with self.subTest(kind=kind.__name__):
                        value, _ = cli.read_file(
                            parent / "thing.json", self.SHOWN, kind)
                        self.assertIsNone(value)
            finally:
                parent.chmod(stat.S_IRWXU)


class TestReadExecution(unittest.TestCase):
    """read_execution — the claude-code-action execution file's (tokens,
    cost), issue #222's harness-side spend record. Every shape it cannot
    account for is (None, error): the caller refuses to write rather than
    inventing a ledger row."""

    RESULT = {"type": "result", "subtype": "success",
              "total_cost_usd": 1.25,
              "usage": {"input_tokens": 1000, "output_tokens": 200,
                        "cache_creation_input_tokens": 300,
                        "cache_read_input_tokens": 500}}

    def write(self, tmp, payload):
        path = Path(tmp) / "execution.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_the_last_result_entry_yields_tokens_and_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, [{"type": "assistant"}, self.RESULT])
            self.assertEqual(cli.read_execution(path), ((2000, 1.25), None))

    def test_absent_usage_fields_count_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, [dict(
                self.RESULT, usage={"input_tokens": 7})])
            self.assertEqual(cli.read_execution(path), ((7, 1.25), None))

    def test_an_unreadable_path_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "nope" / "execution.json")
            spend, error = cli.read_execution(missing)
            self.assertIsNone(spend)
            self.assertTrue(error.startswith(
                f"cannot read execution file {missing}:"), error)

    def test_malformed_json_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "execution.json"
            path.write_text("{not json", encoding="utf-8")
            spend, error = cli.read_execution(str(path))
            self.assertIsNone(spend)
            self.assertTrue(error.startswith(
                f"execution file {path} is not valid JSON:"), error)

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-000 file")
    def test_a_file_the_process_may_not_read_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, [self.RESULT])
            os.chmod(path, 0)
            try:
                self.assertEqual(cli.read_execution(path), (
                    None, f"cannot read execution file {path}: [Errno 13]"
                    f" Permission denied: '{path}'"))
            finally:
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)

    def test_a_directory_in_its_place_is_an_error(self):
        # not absence: the caller named a path, and what is there cannot
        # be read as a file — the OS's own message says so
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "execution.json")
            os.mkdir(path)
            self.assertEqual(cli.read_execution(path), (
                None, f"cannot read execution file {path}: [Errno 21] Is a"
                f" directory: '{path}'"))

    def test_an_empty_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "execution.json"
            path.write_text("", encoding="utf-8")
            self.assertEqual(cli.read_execution(str(path)), (
                None, f"execution file {path} is not valid JSON: Expecting"
                " value: line 1 column 1 (char 0)"))

    def test_bytes_that_are_not_utf8_are_an_error(self):
        """The execution file is one JSON document, and JSON must be
        UTF-8 (RFC 8259 §8.1): bytes that will not decode are the same
        refusal as text that will not parse. The decode used to escape
        the OSError guard, so record-run died instead of refusing."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "execution.json"
            path.write_bytes(b"\xff\xfe")
            self.assertEqual(cli.read_execution(str(path)), (
                None, f"execution file {path} is not valid JSON: 'utf-8'"
                " codec can't decode byte 0xff in position 0: invalid start"
                " byte"))

    def test_a_null_log_has_no_result_entry(self):
        """null parses, so it is a shape this cannot account for rather
        than a read failure: no entry, no spend, the same refusal as a
        log that simply lacks its result."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, None)
            self.assertEqual(
                cli.read_execution(path),
                (None, f"execution file {path} has no result entry"))

    def test_a_log_with_no_result_entry_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, [{"type": "assistant"}])
            self.assertEqual(
                cli.read_execution(path),
                (None, f"execution file {path} has no result entry"))

    def test_a_bad_cost_is_an_error_not_a_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, [dict(self.RESULT,
                                         total_cost_usd="free")])
            self.assertEqual(cli.read_execution(path), (
                None, f"execution file {path} result entry's"
                " total_cost_usd 'free' is not a non-negative number"))

    def test_a_bad_usage_count_is_an_error_not_a_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write(tmp, [dict(
                self.RESULT, usage={"input_tokens": -1})])
            self.assertEqual(cli.read_execution(path), (
                None, f"execution file {path} usage input_tokens -1 is"
                " not a non-negative integer"))


class TestPidAlivePredicate(unittest.TestCase):
    """pid_alive underpins assert_grandchild_reaped's grace loop, so a
    zombie counted as alive reports an already-dead grandchild as a
    survivor. This suite's copy is the third (test_cli_process_reaping
    and test_charter_replay carry the other two)."""

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



if __name__ == "__main__":
    unittest.main()
