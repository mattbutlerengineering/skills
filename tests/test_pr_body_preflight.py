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
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

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
