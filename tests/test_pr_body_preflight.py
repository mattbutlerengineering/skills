"""pr_body_preflight — the PreToolUse hook that applies detector B's body
rule to a `gh pr create` before the PR exists.

Every case replays a complete hook payload (the JSON Claude Code writes
on stdin) through the pure seam `preflight(payload_text)` and asserts the
exact `(exit_code, stderr_lines)`. Exit 2 only on a body the hook read and
judged failing; every other outcome is exit 0, silent or with one note.
"""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

import cli
import gates
import pr_body_preflight

REPO_ROOT = Path(__file__).resolve().parent.parent

NO_WO = "B: PR body cites no work-order id"
NO_CLOSES = "B: PR body has no Closes #N link"
POINTER = ("pr-body-preflight: the body contract is "
           "docs/kb/pr-body-contract.md")
NOT_SEEN = ('pr-body-preflight: not checked — saw "gh pr create" but found '
            "no such command")
PASSING = "WO-0003 per breakdown. Closes #108"


def note(reason):
    return f"pr-body-preflight: not checked — {reason}"


def payload(command, cwd=None):
    """A complete Bash PreToolUse payload as Claude Code sends it."""
    data = {"session_id": "s", "hook_event_name": "PreToolUse",
            "tool_name": "Bash", "tool_input": {"command": command}}
    if cwd is not None:
        data["cwd"] = str(cwd)
    return json.dumps(data)


def run(command, cwd=None):
    return pr_body_preflight.preflight(payload(command, cwd))


def refused(body):
    """The verdict a judged failing body gets: B's own strings for that
    body, then the pointer line."""
    return (2, gates.pr_body_problems(body) + [POINTER])


class TestLiteralBody(unittest.TestCase):
    def test_passing_literal_body_is_silent(self):
        self.assertEqual(
            run(f'gh pr create --title t --body "{PASSING}"'), (0, []))

    def test_missing_work_order_line_is_refused(self):
        body = "Closes #108"
        self.assertEqual(run(f'gh pr create --body "{body}"'),
                         (2, [NO_WO, POINTER]))
        self.assertEqual(run(f'gh pr create --body "{body}"'),
                         refused(body))

    def test_missing_closes_line_is_refused(self):
        body = "WO-0003 per breakdown"
        self.assertEqual(run(f'gh pr create --body "{body}"'),
                         (2, [NO_CLOSES, POINTER]))
        self.assertEqual(run(f'gh pr create --body "{body}"'),
                         refused(body))

    def test_both_missing_is_refused_with_both_strings(self):
        self.assertEqual(run('gh pr create --body "x"'),
                         (2, [NO_WO, NO_CLOSES, POINTER]))
        self.assertEqual(run('gh pr create --body "x"'), refused("x"))

    def test_every_body_spelling_is_judged_like_long_body(self):
        for command in ('gh pr create -b "x"', 'gh pr create --body="x"',
                        "gh pr create -bx", "gh pr create -b=x"):
            with self.subTest(command=command):
                self.assertEqual(run(command), refused("x"))

    def test_passing_body_in_every_spelling_is_silent(self):
        for command in (f'gh pr create -b "{PASSING}"',
                        f'gh pr create --body="{PASSING}"',
                        f'gh pr create "-b{PASSING}"',
                        f'gh pr create "-b={PASSING}"'):
            with self.subTest(command=command):
                self.assertEqual(run(command), (0, []))

    def test_compound_command_is_judged(self):
        self.assertEqual(run('cd x && gh pr create --body "x"'),
                         refused("x"))

    def test_newline_separates_two_commands(self):
        self.assertEqual(run('git push -u origin b\ngh pr create --body "x"'),
                         refused("x"))

    def test_hash_inside_a_word_is_kept(self):
        """commenters="": a `#` mid-word is body text, not a comment."""
        self.assertEqual(run("gh pr create -b WO-0003,Closes\\ #108"),
                         (0, []))

    def test_leading_assignments_and_a_gh_path_are_recognised(self):
        for command in ('GH_REPO=o/r gh pr create --body "x"',
                        '/usr/local/bin/gh pr create --body "x"'):
            with self.subTest(command=command):
                self.assertEqual(run(command), refused("x"))

    def test_prefixes_are_not_looked_through(self):
        for command in ('bash -c "gh pr create --body x"',
                        "env gh pr create --body x",
                        "xargs gh pr create --body x",
                        "command gh pr create --body x"):
            with self.subTest(command=command):
                self.assertEqual(run(command), (0, [NOT_SEEN]))

    def test_unclosed_quote_fails_open_with_a_note(self):
        self.assertEqual(run('gh pr create --body "x'),
                         (0, [note("cannot parse the command: "
                                   "No closing quotation")]))


class TestNotACandidate(unittest.TestCase):
    def test_non_gh_command_is_silent(self):
        self.assertEqual(run("ls -la"), (0, []))

    def test_quoted_mention_is_not_a_command(self):
        for command in ('echo "gh pr create"',
                        'git commit -m "gh pr create"'):
            with self.subTest(command=command):
                self.assertEqual(run(command), (0, [NOT_SEEN]))

    def test_unusable_payloads_are_silent(self):
        for text in ("not json", "[1, 2]", json.dumps({"tool_input": 5}),
                     json.dumps({"tool_input": {"command": 5}}),
                     json.dumps({"tool_name": "Bash"})):
            with self.subTest(text=text):
                self.assertEqual(pr_body_preflight.preflight(text), (0, []))

    def test_a_non_candidate_never_imports_gates(self):
        """The pre-filter runs before gates' ~60 ms import."""
        script = (
            "import sys, json, pr_body_preflight\n"
            "p = json.dumps({'tool_input': {'command': 'ls -la'}})\n"
            "print(pr_body_preflight.preflight(p), 'gates' in sys.modules)\n")
        out = subprocess.run([sys.executable, "-c", script], cwd=REPO_ROOT,
                             capture_output=True, text=True, check=True)
        self.assertEqual(out.stdout.strip(), "(0, []) False")


class TestOneOwner(unittest.TestCase):
    def test_the_hook_judges_through_gates(self):
        """B's one owner, not a copy: a sentinel from the patched owner
        reaches stderr for a body that would otherwise pass."""
        sentinel = ["SENTINEL one", "SENTINEL two"]
        with mock.patch("gates.pr_body_problems", return_value=sentinel):
            code, lines = run(f'gh pr create --body "{PASSING}"')
        self.assertEqual(code, 2)
        self.assertEqual(lines[:2], sentinel)

    def test_a_raising_owner_fails_open(self):
        with mock.patch("gates.pr_body_problems",
                        side_effect=RuntimeError("boom")):
            self.assertEqual(run('gh pr create --body "x"'),
                             (0, [note("RuntimeError: boom")]))


class _TempCwd(unittest.TestCase):
    """Body files live in a temp directory used as the payload cwd."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.cwd = Path(tmp.name)
        (self.cwd / "pass.md").write_text(PASSING + "\n", encoding="utf-8")
        (self.cwd / "fail.md").write_text("x\n", encoding="utf-8")

    def run_here(self, command):
        return run(command, cwd=self.cwd)


class TestBodyFile(_TempCwd):
    def test_body_file_flags_with_a_real_file_are_judged(self):
        for flag in ("--body-file ", "--body-file=", "-F ", "-F"):
            with self.subTest(flag=flag):
                self.assertEqual(
                    self.run_here(f"gh pr create {flag}pass.md"), (0, []))
                self.assertEqual(
                    self.run_here(f"gh pr create {flag}fail.md"),
                    refused("x\n"))

    def test_an_absolute_body_file_needs_no_cwd(self):
        self.assertEqual(
            run(f"gh pr create -F {self.cwd / 'fail.md'}"), refused("x\n"))

    def test_a_missing_body_file_fails_open(self):
        self.assertEqual(self.run_here("gh pr create --body-file gone.md"),
                         (0, [note("no body file at gone.md")]))

    def test_a_non_utf8_body_file_fails_open_with_the_read_problem(self):
        (self.cwd / "bad.md").write_bytes(b"\xff\xfe")
        _, problem = cli.read_file(self.cwd / "bad.md", "bad.md", str)
        self.assertEqual(self.run_here("gh pr create -F bad.md"),
                         (0, [note(problem)]))

    def test_a_relative_body_file_with_no_cwd_fails_open(self):
        self.assertEqual(
            run("gh pr create --body-file fail.md"),
            (0, [note("a relative body file with no cwd in the payload")]))

    def test_cat_substitutions_are_read_as_that_file(self):
        for value in ('"$(cat fail.md)"', '"$(< fail.md)"'):
            with self.subTest(value=value):
                self.assertEqual(
                    self.run_here(f"gh pr create --body {value}"),
                    refused("x\n"))
                self.assertEqual(
                    self.run_here(
                        f"gh pr create --body {value.replace('fail', 'pass')}"),
                    (0, []))

    def test_a_body_file_after_another_command_fails_open(self):
        reason = note("a body file is read only from the first command")
        for command in ("cd x && gh pr create --body-file fail.md",
                        'cd x && gh pr create --body "$(cat fail.md)"'):
            with self.subTest(command=command):
                self.assertEqual(self.run_here(command), (0, [reason]))

    def test_body_file_stdin_fails_open(self):
        self.assertEqual(
            self.run_here("gh pr create --body-file -"),
            (0, [note("--body-file - reads the body from stdin")]))


class TestHeredoc(unittest.TestCase):
    def test_quoted_delimiter_body_is_judged_verbatim(self):
        """Inner quotes survive: a body ending `#12"` still meets B's
        word boundary, so it passes rather than being falsely blocked."""
        for delim in ("'EOF'", '"EOF"'):
            with self.subTest(delim=delim):
                command = ('gh pr create --title t --body "$(cat <<' + delim
                           + "\nWO-0003 it's \"q\"\n\nCloses #12\"\nEOF\n)\"")
                self.assertEqual(run(command), (0, []))

    def test_quoted_delimiter_failing_body_is_refused_verbatim(self):
        body = "it's \"q\" and `ticks` and $NOT_EXPANDED"
        command = ("gh pr create --body \"$(cat <<'EOF'\n" + body
                   + "\nEOF\n)\"")
        self.assertEqual(run(command), refused(body))

    def test_dash_heredoc_strips_leading_tabs(self):
        command = ("gh pr create --body \"$(cat <<-'EOF'\n\tWO-0003\n"
                   "\tCloses #12\n\tEOF\n)\"")
        self.assertEqual(run(command), (0, []))

    def test_unquoted_delimiter_with_a_dollar_fails_open(self):
        command = 'gh pr create --body "$(cat <<EOF\nWO-0003 $X\nEOF\n)"'
        self.assertEqual(
            run(command),
            (0, [note("an unquoted heredoc body holds $ or a backtick")]))

    def test_unquoted_delimiter_without_expansions_is_judged(self):
        command = 'gh pr create --body "$(cat <<EOF\nplain text\nEOF\n)"'
        self.assertEqual(run(command), refused("plain text"))


class TestUnreadableShapes(unittest.TestCase):
    def test_a_body_with_a_dollar_or_backtick_fails_open(self):
        reason = note("the body holds $ or a backtick the hook cannot expand")
        for value in ('"$VAR"', '"see `x`"', '"$(git log -1)"'):
            with self.subTest(value=value):
                self.assertEqual(run(f"gh pr create --body {value}"),
                                 (0, [reason]))

    def test_flags_that_leave_the_body_to_gh_fail_open(self):
        for flag in ("--fill", "--fill-first", "--fill-verbose", "--web",
                     "-w", "--editor", "-e", "-f", "--template t",
                     "-T t", "--recover r"):
            with self.subTest(flag=flag):
                self.assertEqual(
                    run(f"gh pr create {flag}"),
                    (0, [note(f"{flag.split()[0]} leaves the body to gh")]))

    def test_no_body_source_fails_open(self):
        self.assertEqual(run("gh pr create --title t"),
                         (0, [note("no --body or --body-file")]))

    def test_two_body_sources_fail_open(self):
        self.assertEqual(run('gh pr create -b "x" -F f.md'),
                         (0, [note("more than one body source")]))

    def test_a_cluster_hiding_a_body_flag_fails_open(self):
        self.assertEqual(
            run('gh pr create -db "x"'),
            (0, [note("-db hides a body flag in a cluster")]))


class _BrokenStdin:
    def read(self):
        raise OSError("gone")


class TestMain(unittest.TestCase):
    def test_main_writes_preflight_lines_and_returns_its_code(self):
        text = payload('gh pr create --body "x"')
        err = io.StringIO()
        with redirect_stderr(err):
            code = pr_body_preflight.main([], stdin=io.StringIO(text))
        self.assertEqual((code, err.getvalue().splitlines()),
                         pr_body_preflight.preflight(text))
        self.assertEqual(code, 2)

    def test_an_argument_prints_usage_and_exits_0(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = pr_body_preflight.main(["x"])
        self.assertEqual(code, 0)
        self.assertEqual(err.getvalue().strip(),
                         pr_body_preflight.__doc__.strip())

    def test_a_stdin_read_failure_fails_open(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = pr_body_preflight.main([], stdin=_BrokenStdin())
        self.assertEqual(code, 0)
        self.assertEqual(err.getvalue().splitlines(),
                         [note("OSError: gone")])


if __name__ == "__main__":
    unittest.main()
