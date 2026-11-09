"""pr_body_preflight — the PreToolUse hook that applies detector B's body
rule to a `gh pr create` before the PR exists.

Every case replays a complete hook payload (the JSON Claude Code writes
on stdin) through the pure seam `preflight(payload_text)` and asserts the
exact `(exit_code, stderr_lines)`. Exit 2 only on a body the hook read and
judged failing; every other outcome is exit 0, silent or with one note.
"""
import io
import json
import os
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
        """A cd the hook can place inside this repository keeps the
        command judged (amended at the review fix loop: a cd it cannot
        place now fails open, so the fixture gives it a real checkout)."""
        with tempfile.TemporaryDirectory() as tmp:
            top = Path(tmp)
            _git_repo(top, "git@github.com:me/this.git")
            (top / "x").mkdir()
            self.assertEqual(run('cd x && gh pr create --body "x"', top),
                             refused("x"))

    def test_newline_separates_two_commands(self):
        self.assertEqual(run('git push -u origin b\ngh pr create --body "x"'),
                         refused("x"))

    def test_hash_inside_a_word_is_kept(self):
        """commenters="": a `#` mid-word is body text, not a comment."""
        self.assertEqual(run("gh pr create -b WO-0003,Closes\\ #108"),
                         (0, []))

    def test_leading_assignments_and_a_gh_path_are_recognised(self):
        for command in ('FOO=o/r gh pr create --body "x"',
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
            (0, [note("an unquoted heredoc body holds $, a backtick "
                      "or a backslash")]))

    def test_unquoted_delimiter_with_a_backslash_fails_open(self):
        """The shell joins a backslash-newline in an unquoted heredoc, so
        `Closes \\<newline>#12` reaches gh as `Closes #12`, which B
        accepts; judging the raw text would be a false block."""
        command = ('gh pr create --body "$(cat <<EOF\nWO-0003 Closes \\\n'
                   '#12\nEOF\n)"')
        self.assertEqual(
            run(command),
            (0, [note("an unquoted heredoc body holds $, a backtick "
                      "or a backslash")]))

    def test_unquoted_delimiter_without_expansions_is_judged(self):
        command = 'gh pr create --body "$(cat <<EOF\nplain text\nEOF\n)"'
        self.assertEqual(run(command), refused("plain text"))


class TestSameCallHeredoc(unittest.TestCase):
    """A `gh pr create --body-file F` that is not the compound's first
    command, where a `cat > F <<D` earlier in the same call wrote F: the
    hook judges the heredoc text. Full payloads through `preflight()`."""

    @staticmethod
    def demo(body, delim="'EOF'", path="/tmp/b.md"):
        return (f"cat > {path} <<{delim}\n{body}\nEOF\n"
                f"gh pr create --title t --body-file {path}")

    def test_the_demo_payload_is_refused_before_the_pr_exists(self):
        body = "A summary with no work order and no link."
        self.assertEqual(run(self.demo(body)), refused(body + "\n"))

    def test_its_passing_twin_is_silent(self):
        body = "No work order: a demo.\n\nCloses #12"
        self.assertEqual(run(self.demo(body)), (0, []))


    def capture(self, command, pairs=()):
        unrun = pr_body_preflight._Unrun(command, pairs)
        return unrun.run(), unrun.heredocs

    def test_a_statement_heredoc_is_captured_with_its_text(self):
        out, heredocs = self.capture(
            "cat > F <<'EOF'\nline one\nline two\nEOF\n")
        self.assertEqual(
            heredocs,
            [pr_body_preflight.Heredoc("line one\nline two\n", True, True)])
        self.assertEqual(out, "cat > F <<__pr_body_preflight_heredoc_0__\n")

    def test_a_dash_heredoc_strips_leading_tabs_from_its_text(self):
        _, heredocs = self.capture("cat <<-EOF > F\n\ta\n\t\tb\n\tEOF\n")
        self.assertEqual(heredocs[0].text, "a\nb\n")
        self.assertTrue(heredocs[0].terminated)

    def test_a_delimiter_that_never_closes_is_unterminated(self):
        _, heredocs = self.capture("cat > F <<EOF\nplain\nnever closed")
        self.assertEqual(
            heredocs,
            [pr_body_preflight.Heredoc("plain\nnever closed\n", True, False)])

    def test_a_here_string_is_not_a_heredoc(self):
        out, heredocs = self.capture("cat > F <<< text\n")
        self.assertEqual((out, heredocs), ("cat > F <<< text\n", []))

    def test_literal_follows_the_quoting_and_the_body(self):
        for command, literal in (
                ("cat <<'D'\n$X\nD\n", True), ('cat <<"D"\n$X\nD\n', True),
                ("cat <<\\D\n$X\nD\n", True), ("cat <<D\nplain\nD\n", True),
                ("cat <<D\n$X\nD\n", False), ("cat <<D\n`x`\nD\n", False),
                ("cat <<D\na\\b\nD\n", False)):
            with self.subTest(command=command):
                self.assertEqual(self.capture(command)[1][0].literal, literal)

    def test_heredocs_are_numbered_in_queue_order(self):
        out, heredocs = self.capture("cat <<A; cat <<B\none\nA\ntwo\nB\n")
        self.assertEqual([h.text for h in heredocs], ["one\n", "two\n"])
        self.assertEqual(out, "cat <<__pr_body_preflight_heredoc_0__; "
                              "cat <<__pr_body_preflight_heredoc_1__\n")

    def test_literal_and_text_are_decided_on_the_unmasked_body(self):
        """A body that documents a `$(cat <<'B' ... B)` snippet: the masked
        placeholder is restored before `literal` is decided, and `text` is
        the original span (P3 gap 7)."""
        snippet = "$(cat <<'B'\ninner\nB\n)"
        masked, _, pairs = pr_body_preflight._mask_heredocs(
            f"cat > F <<'EOF'\nsee {snippet} here\nEOF\n")
        self.assertNotIn("inner", masked)
        _, heredocs = self.capture(masked, pairs)
        self.assertEqual(heredocs[0].text, f"see {snippet} here\n")
        _, unquoted = self.capture(
            masked.replace("<<'EOF'", "<<EOF"), pairs)
        self.assertEqual(unquoted[0].text, f"see {snippet} here\n")
        self.assertFalse(unquoted[0].literal)


    def split(self, command):
        tokens = pr_body_preflight._tokens(
            pr_body_preflight._Unrun(command).run())
        return pr_body_preflight._simple_commands(tokens)

    def test_a_redirect_only_command_is_a_record_with_its_joiner(self):
        Simple = pr_body_preflight.Simple
        self.assertEqual(
            self.split("a\n> /tmp/b.md\nb"),
            [Simple(["a"], [], ""),
             Simple([], [(">", "/tmp/b.md")], "\n"),
             Simple(["b"], [], "\n")])

    def test_a_heredoc_redirect_keeps_its_written_order(self):
        ph = "__pr_body_preflight_heredoc_0__"
        Simple = pr_body_preflight.Simple
        for command, redirects in (
                ("cat > F <<D\nx\nD\n", [(">", "F"), ("<<", ph)]),
                ("cat <<D > F\nx\nD\n", [("<<", ph), (">", "F")])):
            with self.subTest(command=command):
                self.assertEqual(self.split(command),
                                 [Simple(["cat"], redirects, "")])

    def test_a_word_less_record_does_not_make_a_body_file_not_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.md").write_text("x\n", encoding="utf-8")
            self.assertEqual(
                run("> log\ngh pr create -F x.md", cwd=tmp), refused("x\n"))

    def test_a_mixed_run_splits_before_its_redirection_operator(self):
        Simple = pr_body_preflight.Simple
        self.assertEqual(
            self.split("a;>f"),
            [Simple(["a"], [], ""), Simple([], [(">", "f")], ";")])

    def test_a_lone_ampersand_before_a_redirect_stays_in_the_operator(self):
        Simple = pr_body_preflight.Simple
        for op in ("&>", "&>>"):
            with self.subTest(op=op):
                self.assertEqual(self.split(f"cmd {op} f"),
                                 [Simple(["cmd"], [(op, "f")], "")])
                self.assertEqual(
                    self.split(f"a;&{op[1:]}f"),
                    [Simple(["a"], [], ""), Simple([], [(op, "f")], ";")])

    BAD = "A summary with no work order and no link."
    GOOD = "No work order: a demo.\n\nCloses #12"
    NOT_FIRST = note("a body file is read only from the first command")

    @staticmethod
    def write(body, path="/tmp/b.md", delim="'EOF'", order="redirect first"):
        """A `cat > F <<D` writer line with its body and closing line."""
        operators = (f"> {path} <<{delim}" if order == "redirect first"
                     else f"<<{delim} > {path}")
        return f"cat {operators}\n{body}\nEOF\n"

    READ = "gh pr create --title t --body-file /tmp/b.md"

    def test_the_writer_is_found_in_both_orders(self):
        for order in ("redirect first", "heredoc first"):
            with self.subTest(order=order):
                self.assertEqual(
                    run(self.write(self.BAD, order=order) + self.READ),
                    refused(self.BAD + "\n"))
                self.assertEqual(
                    run(self.write(self.GOOD, order=order) + self.READ),
                    (0, []))

    def test_a_later_writer_of_the_same_spelling_replaces_an_earlier_one(self):
        self.assertEqual(
            run(self.write(self.GOOD) + self.write(self.BAD) + self.READ),
            refused(self.BAD + "\n"))
        self.assertEqual(
            run(self.write(self.BAD) + self.write(self.GOOD) + self.READ),
            (0, []))

    def test_a_reader_naming_a_different_file_keeps_todays_note(self):
        self.assertEqual(
            run(self.write(self.BAD) + "gh pr create --body-file /tmp/o.md"),
            (0, [self.NOT_FIRST]))

    def test_an_unquoted_delimiter_with_an_expansion_is_a_note(self):
        reason = note("an unquoted heredoc body holds $, a backtick "
                      "or a backslash")
        for body in ("WO-0003 $X", "WO-0003 `x`", "WO-0003 a\\b"):
            with self.subTest(body=body):
                self.assertEqual(
                    run(self.write(body, delim="EOF") + self.READ),
                    (0, [reason]))

    def test_an_unquoted_delimiter_without_expansion_is_judged(self):
        self.assertEqual(
            run(self.write(self.BAD, delim="EOF") + self.READ),
            refused(self.BAD + "\n"))

    def test_an_unterminated_heredoc_is_a_note(self):
        command = ("cat > /tmp/b.md <<'EOF' && gh pr create --title t "
                   "--body-file /tmp/b.md\nbody\n")
        self.assertEqual(
            run(command),
            (0, [note("the heredoc that writes /tmp/b.md has no closing "
                      "delimiter")]))

    def test_append_and_tee_are_not_writers(self):
        for writer in ("cat >> /tmp/b.md <<'EOF'\nx\nEOF\n",
                       "tee /tmp/b.md <<'EOF'\nx\nEOF\n",
                       "cat /tmp/b.md > /tmp/b.md <<'EOF'\nx\nEOF\n"):
            with self.subTest(writer=writer):
                self.assertEqual(run(writer + self.READ), (0, [self.NOT_FIRST]))

    def test_any_command_between_writer_and_reader_is_a_note(self):
        reason = ("/tmp/b.md may be rewritten or removed by {} between "
                  "the heredoc and gh pr create")
        for between, what in (("rm /tmp/b.md\n", "rm"),
                              ("> /tmp/b.md\n", "> /tmp/b.md")):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.write(self.BAD) + between + self.READ),
                    (0, [note(reason.format(what))]))

    def test_body_file_stdin_is_checked_ahead_of_the_binding(self):
        stdin = note("--body-file - reads the body from stdin")
        for path in ("/tmp/b.md", "-"):
            with self.subTest(path=path):
                self.assertEqual(
                    run(self.write(self.BAD, path=path)
                        + "gh pr create --title t --body-file -"),
                    (0, [stdin]))

    def test_a_cat_substitution_after_a_writer_keeps_todays_note(self):
        self.assertEqual(
            run(self.write(self.BAD)
                + 'gh pr create --title t --body "$(cat /tmp/b.md)"'),
            (0, [self.NOT_FIRST]))


    PROCSUB = note("a process substitution in gh pr create hides the body file")

    def test_a_process_substitution_in_the_reader_is_a_note(self):
        """As the compound's first command and after a writer, with no
        disk read of `a`: its text would fail B if it were read."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a").write_text("x\n", encoding="utf-8")
            for command in (
                    "gh pr create --title t -F <(cat a c)",
                    "gh pr create --title t --body-file >(cat a c)",
                    self.write(self.BAD)
                    + "gh pr create --title t -F <(cat a c)"):
                with self.subTest(command=command):
                    self.assertEqual(run(command, cwd=tmp), (0, [self.PROCSUB]))

    def test_the_splitter_records_a_process_substitution_anywhere(self):
        for command, op in (("diff <(a) b", "<("), ("echo x >(tee f)", ">(")):
            with self.subTest(command=command):
                records = self.split(command)
                self.assertIn(("procsub", op), records[0].redirects)

    def test_a_here_string_is_never_a_writer(self):
        self.assertEqual(
            run('cat > /tmp/b.md <<< "x"\n' + self.READ), (0, [self.NOT_FIRST]))


    def test_a_writer_the_shell_can_skip_is_a_note(self):
        reason = note("the heredoc that writes /tmp/b.md is not certain to "
                      "run before gh pr create")
        body = f"{self.BAD}\nEOF\n"
        read = "gh pr create --title t --body-file /tmp/b.md"
        for name, command in (
                ("a", f"test -f /tmp/b.md || cat > /tmp/b.md <<'EOF'\n{body}{read}"),
                ("b", f"test -f /tmp/b.md || cat > /tmp/b.md <<'EOF' && {read}\n{body}"),
                ("c", f"cat > /tmp/b.md <<'EOF' || {read}\n{body}"),
                ("d", f"cat > /tmp/b.md <<'EOF' &\n{body}{read}"),
                ("e", f"cat > /tmp/b.md <<'EOF' | {read}\n{body}"),
                ("f", f"git push && cat > /tmp/b.md <<'EOF'\n{body}{read}")):
            with self.subTest(shape=name):
                self.assertEqual(run(command), (0, [reason]))

    def test_a_writer_that_surely_runs_is_still_judged(self):
        body = f"{self.BAD}\nEOF\n"
        read = "gh pr create --title t --body-file /tmp/b.md"
        for name, command in (
                ("start", f"cat > /tmp/b.md <<'EOF'\n{body}{read}"),
                ("semicolon", f"true; cat > /tmp/b.md <<'EOF'\n{body}{read}"),
                ("and", f"cat > /tmp/b.md <<'EOF' && {read}\n{body}"),
                ("and newline", f"cat > /tmp/b.md <<'EOF' &&\n{body}{read}"),
                ("reader after semicolon",
                 f"cat > /tmp/b.md <<'EOF' ; {read}\n{body}")):
            with self.subTest(shape=name):
                self.assertEqual(run(command), refused(self.BAD + "\n"))

    def test_a_heredoc_with_no_newline_after_it_has_no_closing_delimiter(self):
        self.assertEqual(
            run("cat > /tmp/b.md <<'EOF' && gh pr create --title t "
                "--body-file /tmp/b.md"),
            (0, [note("the heredoc that writes /tmp/b.md has no closing "
                      "delimiter")]))

    def test_a_restored_span_holding_the_outer_delimiter_is_unterminated(self):
        masked, _, pairs = pr_body_preflight._mask_heredocs(
            "cat > F <<'EOF'\nSee $(cat <<'B'\nEOF\nB\n)\nEOF\n")
        _, heredocs = self.capture(masked, pairs)
        self.assertFalse(heredocs[0].terminated)
        masked, _, pairs = pr_body_preflight._mask_heredocs(
            "cat > F <<-'EOF'\n\tSee $(cat <<'B'\n\tEOF\nB\n)\n\tEOF\n")
        _, heredocs = self.capture(masked, pairs)
        self.assertFalse(heredocs[0].terminated)


    # --- Milestone 2, chain rule: the writer's joiners ---------------------
    CHAIN_WRITER = "cat > /tmp/b.md <<'EOF'"
    CHAIN_BODY = "{}\nEOF\n".format(BAD)
    CHAIN_NOTE = note("the heredoc that writes /tmp/b.md is not certain to "
                      "run before gh pr create")

    def chain(self, before="", after="\n", reader=READ):
        """`before` the writer, then the reader joined to the writer by
        `after` (a newline puts the reader after the heredoc body, any
        other joiner puts it on the writer's own line)."""
        if after.endswith("\n") and after.strip() == "":
            return (f"{before}{self.CHAIN_WRITER}\n{self.CHAIN_BODY}"
                    f"{reader}")
        return (f"{before}{self.CHAIN_WRITER} {after} {reader}\n"
                f"{self.CHAIN_BODY}")

    def test_a_writer_that_surely_ran_is_judged(self):
        judged = refused(self.BAD + "\n")
        for name, command in (
                ("start", self.chain()),
                ("semicolon", self.chain("true; ")),
                ("semicolon newline", self.chain("true;\n")),
                ("newline", self.chain("true\n")),
                ("and chain, newline writer", self.chain("a && b\n")),
                ("hostile run before a ; writer", self.chain("a | b ; ")),
                ("hostile run before a newline writer",
                 self.chain("a | b\n")),
                ("and newline", self.chain("true &&\n", "&&")),
                ("and space newline", self.chain("true && \n", "&&")),
                ("and comment newline", self.chain("true && # c\n", "&&")),
                ("and continuation", self.chain("true && \\\n", "&&")),
                ("semicolon reader", self.chain(after=";")),
                ("and reader after semicolon writer",
                 self.chain("true; ", "&&"))):
            with self.subTest(shape=name):
                self.assertEqual(run(command), judged)

    def test_a_writer_the_shell_may_skip_is_a_note(self):
        for name, command in (
                ("or before", self.chain("test -f /tmp/b.md || ", "&&")),
                ("or newline before", self.chain("test -f x ||\n", "&&")),
                ("or space newline before", self.chain("a || \n", "&&")),
                ("and before, newline reader",
                 self.chain("test -d /x && ")),
                ("git push and, newline reader", self.chain("git push && ")),
                ("and newline before, newline reader",
                 self.chain("a &&\n")),
                ("and comment before, newline reader",
                 self.chain("a && # c\n")),
                ("or after", self.chain(after="||")),
                ("background writer", self.chain(after="&")),
                ("background newline", self.chain("a &\n", "&&")),
                ("pipeline", self.chain(after="|")),
                ("pipeline reader", self.chain(reader="x | " + self.READ)),
                ("subshell reader", self.chain(reader="( " + self.READ + " )")),
                ("subshell writer", self.chain("( ", "&&")),
                ("double semicolon before", self.chain("a;; ")),
                ("double semicolon after", self.chain(after=";;")),
                ("and semicolon before", self.chain("a && ; ", "&&")),
                ("and semicolon after", self.chain(after="&& ;")),
                ("semicolon and after", self.chain(after="; &&"))):
            with self.subTest(shape=name):
                self.assertEqual(run(command), (0, [self.CHAIN_NOTE]))

    def test_an_if_between_writer_and_reader_is_a_note(self):
        for reader in ("if true; then\n" + self.READ + "\nfi",
                       "if true\nthen\n" + self.READ + "\nfi",
                       "while true; do\n" + self.READ + "\ndone"):
            with self.subTest(reader=reader):
                self.assertEqual(run(self.chain(reader=reader)),
                                 (0, [self.CHAIN_NOTE]))

    def test_a_cd_before_the_writer_is_judged_only_when_it_surely_ran(self):
        with tempfile.TemporaryDirectory() as tmp:
            top = Path(tmp)
            _git_repo(top, "git@github.com:me/this.git")
            (top / "d").mkdir()
            for name, command, expected in (
                    ("and to the reader", self.chain("cd d && ", "&&"),
                     refused(self.BAD + "\n")),
                    ("three links", self.chain("cd d && true && ", "&&"),
                     refused(self.BAD + "\n")),
                    ("newline before the reader", self.chain("cd d && "),
                     (0, [self.CHAIN_NOTE])),
                    ("or to the reader", self.chain("cd d || ", "&&"),
                     (0, [self.CHAIN_NOTE]))):
                with self.subTest(shape=name):
                    self.assertEqual(run(command, top), expected)

    def test_a_reader_joined_by_or_to_a_surely_run_writer_is_a_note(self):
        self.assertEqual(
            run(self.chain("true; ", "||")), (0, [self.CHAIN_NOTE]))

    def test_a_reader_joiner_the_shell_rejects_is_a_note(self):
        """#1661: `;;`, `; &&`, `&& ;`, `&&;` and a newline before `&&` are
        no sequential joiner (bash calls them syntax errors, so gh never
        runs; the hook still never reads them as a surely-run writer)."""
        for name, command in (
                ("double semicolon", self.chain(after=";;")),
                ("semicolon and", self.chain(after="; &&")),
                ("and semicolon", self.chain(after="&& ;")),
                ("and semicolon touching", self.chain(after="&&;")),
                ("newline and", self.write(self.BAD) + "&& " + self.READ),
                ("blank line and",
                 self.write(self.BAD) + "\n&& " + self.READ)):
            with self.subTest(shape=name):
                self.assertEqual(run(command), (0, [self.CHAIN_NOTE]))


    # --- Milestone 2, spelling rule ---------------------------------------
    def spelled(self, spelling, body=None, before="", between=""):
        """A writer and a reader that both spell F as `spelling`."""
        return (before + self.write(body or self.BAD, path=spelling) + between
                + f"gh pr create --title t --body-file {spelling}")

    def test_the_same_spelling_binds(self):
        judged = refused(self.BAD + "\n")
        for name, command in (
                ("absolute", self.spelled("/tmp/b.md")),
                ("$NAME", self.spelled("$S/b.md", before="S=/tmp\n")),
                ("${NAME}", self.spelled("${S}/b.md", before="S=/tmp\n")),
                ("$NAME unset", self.spelled("$S/b.md")),
                ("quoted", self.spelled('"$S/b.md"', before="S=/tmp\n")),
                ("relative", self.spelled("b.md")),
                ("a name that merely starts like a shell one",
                 self.spelled("$BANANA/b.md"))):
            with self.subTest(shape=name):
                self.assertEqual(run(command), judged)

    def test_a_passing_body_through_a_variable_path_is_silent(self):
        self.assertEqual(
            run(self.spelled("$S/b.md", self.GOOD, before="S=/tmp\n")),
            (0, []))

    def test_a_different_spelling_does_not_bind(self):
        self.assertEqual(
            run(self.write(self.BAD, path="b.md")
                + "gh pr create --body-file ./b.md"), (0, [self.NOT_FIRST]))
        self.assertEqual(
            run("S=/tmp\n" + self.write(self.BAD, path="$S/b.md")
                + "gh pr create --body-file ${S}/b.md"), (0, [self.NOT_FIRST]))

    def test_a_spelling_the_hook_cannot_compare_is_a_note(self):
        for spelling in ("/tmp/$RANDOM.md", "$PWD/b.md", "${PWD}/b.md",
                         "/tmp/*.md", "/tmp/?.md", "/tmp/[a].md", "~/b.md",
                         "$PIPESTATUS/b.md", "${HISTCMD}/b.md",
                         "$SECONDS.md", "$BASH_VERSION/b.md", "$_/b.md",
                         "$$.md", "$1/b.md", "${S:-x}/b.md", "/tmp/{a,b}.md",
                         "$S$/b.md", "$DIRSTACK/b.md", "${status}/b.md",
                         "$pipestatus/b.md"):
            with self.subTest(spelling=spelling):
                self.assertEqual(
                    run(self.spelled(spelling)),
                    (0, [note(f"{spelling} names a file through an "
                              "expansion the hook cannot compare")]))

    def test_a_command_substitution_spelling_is_a_note(self):
        for spelling in ("$(mktemp)", "$(mktemp).md"):
            with self.subTest(spelling=spelling):
                self.assertEqual(
                    run(self.spelled(spelling)),
                    (0, [note("a command substitution names the body file, "
                              "which the hook cannot compare")]))

    def test_a_cd_between_unbinds_a_relative_spelling(self):
        with tempfile.TemporaryDirectory() as tmp:
            top = Path(tmp)
            _git_repo(top, "git@github.com:me/this.git")
            (top / "d").mkdir()
            for spelling, before in (("b.md", ""), ("$S/b.md", "S=/tmp\n")):
                for verb in ("cd d", "pushd d", "popd"):
                    with self.subTest(spelling=spelling, verb=verb):
                        self.assertEqual(
                            run(self.spelled(spelling, before=before,
                                             between=verb + "\n"), top),
                            (0, [note("a cd between the heredoc and gh pr "
                                      f"create may change what {spelling} "
                                      "names")]))

    def test_an_absolute_spelling_survives_a_cd(self):
        with tempfile.TemporaryDirectory() as tmp:
            top = Path(tmp)
            _git_repo(top, "git@github.com:me/this.git")
            (top / "d").mkdir()
            for verb in ("cd d", "pushd d"):
                with self.subTest(verb=verb):
                    self.assertEqual(
                        run(self.spelled("/tmp/b.md", between=verb + "\n"),
                            top), refused(self.BAD + "\n"))

    def test_a_cd_that_hides_a_command_is_still_a_note(self):
        for between in ("cd `rm /tmp/b.md`\n", "cd $(rm /tmp/b.md)\n",
                        "cd d > /tmp/b.md\n", "cd d; rm /tmp/b.md\n",
                        "cd d | rm /tmp/b.md\n"):
            with self.subTest(between=between):
                code, lines = run(self.spelled("/tmp/b.md", between=between))
                self.assertEqual(code, 0)
                self.assertEqual(len(lines), 1)
                self.assertNotIn("B:", lines[0])

    # --- Milestone 3, invalidation rules 1 to 3 ---------------------------
    def unbound(self, what, spelling="/tmp/b.md"):
        return (0, [note(f"{spelling} may be rewritten or removed by {what} "
                         "between the heredoc and gh pr create")])

    def assert_a_note(self, command, cwd=None):
        code, lines = run(command, cwd)
        self.assertEqual(code, 0, command)
        self.assertEqual(len(lines), 1, command)
        self.assertTrue(lines[0].startswith("pr-body-preflight: not checked"),
                        command)

    def test_a_write_redirect_between_is_a_note(self):
        for between, what in (
                ("> /tmp/b.md\n", "> /tmp/b.md"),
                (">| /tmp/b.md\n", ">| /tmp/b.md"),
                ("&> /tmp/b.md\n", "&> /tmp/b.md"),
                (">& /tmp/b.md\n", ">& /tmp/b.md"),
                ('>> "$BODY"\n', ">> $BODY"),
                ("> ./b.md\n", "> ./b.md"),
                ("<> /tmp/b.md\n", "<> /tmp/b.md"),
                (">&2 > /tmp/b.md\n", "> /tmp/b.md"),
                ("2> /tmp/b.md\n", "2> /tmp/b.md")):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between)),
                    self.unbound(what))

    def test_a_file_descriptor_or_null_redirect_between_is_judged(self):
        for between in ("> /dev/null\n", ">&2\n", ">&-\n", ">/dev/stderr\n",
                        "&> /dev/null\n", "< /tmp/x\n"):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between)),
                    refused(self.BAD + "\n"))

    def test_a_write_redirect_on_the_reader_is_a_note(self):
        for tail, what in ((" > /tmp/b.md", "> /tmp/b.md"),
                           (' >> "$BODY"', ">> $BODY"),
                           (" > ./b.md", "> ./b.md"),
                           (" &> /tmp/b.md", "&> /tmp/b.md"),
                           (" >& /tmp/b.md", ">& /tmp/b.md")):
            with self.subTest(tail=tail):
                self.assertEqual(run(self.spelled("/tmp/b.md") + tail),
                                 self.unbound(what))

    def test_a_descriptor_or_null_redirect_on_the_reader_is_judged(self):
        for tail in (" 2>&1", " > /dev/null", " >&2", " >&-",
                     " > /dev/null 2>&1"):
            with self.subTest(tail=tail):
                self.assertEqual(run(self.spelled("/tmp/b.md") + tail),
                                 refused(self.BAD + "\n"))

    def test_a_process_substitution_between_is_a_note(self):
        for between in ("cat <(echo hi)\n", "diff <(a) <(b)\n",
                        "tee >(cat)\n", ": <(rm /tmp/b.md)\n"):
            with self.subTest(between=between):
                self.assert_a_note(
                    self.spelled("/tmp/b.md", between=between))

    def test_a_hostile_joiner_or_keyword_between_is_a_note(self):
        for between in ("true | true\n", "true || true\n", "true &\n",
                        "( true )\n", "{ true; }\n", "if true; then\nfi\n",
                        "while false; do\ndone\n", "! true\n",
                        "case x in\nx) true;;\nesac\n"):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between)),
                    (0, [self.CHAIN_NOTE]))

    def test_an_export_or_unset_of_a_name_the_spelling_holds_is_a_note(self):
        for between, what in (("export S=/x\n", "export"),
                              ("export S\n", "export"), ("unset S\n", "unset"),
                              ("unset -v S\n", "unset")):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("$S/b.md", before="S=/tmp\n",
                                     between=between)),
                    self.unbound(what, "$S/b.md"))

    def test_an_exec_with_a_write_redirect_unbinds(self):
        for name, command in (
                ("between", self.spelled("/tmp/b.md",
                                         between="exec > /tmp/log\n")),
                ("descriptor before the writer",
                 self.spelled("/tmp/b.md", before="exec 3> /tmp/b.md\n",
                              between="echo hi >&3\n")),
                ("append before the writer",
                 self.spelled("/tmp/b.md", before="exec 3>> /tmp/b.md\n")),
                ("read-write before the writer",
                 self.spelled("/tmp/b.md", before="exec 3<> /tmp/b.md\n"))):
            with self.subTest(shape=name):
                self.assert_a_note(command)
        self.assertEqual(
            run(self.spelled("/tmp/b.md", before="exec 2>&1\n")),
            refused(self.BAD + "\n"))
        self.assertEqual(
            run(self.spelled("/tmp/b.md", before="exec > /dev/null\n")),
            refused(self.BAD + "\n"))

    def closed(self, opener, closer, tail=""):
        """A writer and reader inside a block, `closer` after the reader."""
        return (f"{opener}\n" + self.write(self.BAD) + self.READ
                + f"\n{closer}{tail}")

    def test_a_closer_after_the_reader_with_a_write_redirect_unbinds(self):
        for opener, closer in (("{", "}"), ("(true", ")"),
                               ("while true; do", "done"),
                               ("if true; then", "fi")):
            for tail, what in ((" > /tmp/b.md", "> /tmp/b.md"),
                               (" >> /tmp/log", ">> /tmp/log"),
                               (" &> /tmp/log", "&> /tmp/log"),
                               (" 2>&1 > /tmp/log", "> /tmp/log")):
                with self.subTest(closer=closer, tail=tail):
                    self.assertEqual(run(self.closed(opener, closer, tail)),
                                     self.unbound(what))
            with self.subTest(closer=closer, tail="/dev/null"):
                self.assertEqual(
                    run(self.closed(opener, closer, " > /dev/null")),
                    refused(self.BAD + "\n"))
            with self.subTest(closer=closer, tail="none"):
                self.assertEqual(run(self.closed(opener, closer)),
                                 refused(self.BAD + "\n"))
        for tail, expected in (
                (" > /tmp/b.md", self.unbound("> /tmp/b.md")),
                (" > /dev/null", refused(self.BAD + "\n"))):
            with self.subTest(closer="esac", tail=tail):
                self.assertEqual(
                    run("case x in\nx) true\n" + self.write(self.BAD)
                        + self.READ + "\n;;\nesac" + tail), expected)

    def test_a_writer_on_the_blocks_opening_line_is_a_note(self):
        self.assertEqual(
            run("{ " + self.write(self.BAD) + self.READ + "; } > /tmp/b.md"),
            (0, [self.NOT_FIRST]))

    # --- Milestone 3, rule 4: the inert shell builtins and read-only verbs --
    INERT = (
        "echo hi", "printf '%s\\n' hi", "true", ":", "sleep 0",
        "cat /tmp/x", "grep -q x /tmp/x", "egrep -q x /tmp/x",
        "fgrep -q x /tmp/x", "head -1 /tmp/x", "tail -1 /tmp/x",
        "wc -l /tmp/x", "ls /tmp", "test -f /tmp/x", "[ -f /tmp/x ]",
        "diff /tmp/x /tmp/y", "cmp /tmp/x /tmp/y", "stat /tmp/x", "T=1",
        "export T=1", "T=1 U=2", "export T=1 U=2",
        "echo hi 2>&1", "echo hi > /dev/null", "echo hi >&2",
        "cat < /tmp/x", "grep x < /tmp/x")

    def test_an_inert_command_between_writer_and_reader_is_judged(self):
        for between in self.INERT:
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    refused(self.BAD + "\n"))
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", self.GOOD,
                                     between=between + "\n")), (0, []))

    def test_a_directory_change_between_is_judged_for_an_absolute_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            top = Path(tmp)
            _git_repo(top, "git@github.com:me/this.git")
            (top / "d").mkdir()
            for between in ("cd d", "pushd d", "cd d && echo hi"):
                with self.subTest(between=between):
                    self.assertEqual(
                        run(self.spelled("/tmp/b.md",
                                         between=between + "\n"), top),
                        refused(self.BAD + "\n"))

    def test_a_verb_off_the_list_between_is_a_note(self):
        for between, what in (
                ("rm /tmp/b.md", "rm"), ("mv /tmp/x /tmp/b.md", "mv"),
                ("cp /tmp/x /tmp/b.md", "cp"), ("tee /tmp/b.md", "tee"),
                ("sed -i s/a/b/ /tmp/b.md", "sed"),
                ("truncate -s 0 /tmp/b.md", "truncate"),
                ("python3 x.py", "python3"), ("touch /tmp/b.md", "touch"),
                ("sort -o /tmp/b.md x", "sort"), ("dd of=/tmp/b.md", "dd"),
                ("install x /tmp/b.md", "install"), ("ln -sf x /tmp/b.md", "ln"),
                ("exec true", "exec"), ("eval true", "eval"),
                ("source x.sh", "source"), ("read x", "read"),
                ("FOO=1 cat x", "FOO="), ("unset T", "unset"),
                ("export T", "export"), ("export -n T=1", "export"),
                ("export T=1 rm", "export"), ("T+=x", "T+=x"),
                ("[[ -f x ]]", "[["), ("./b.sh", "./b.sh"), ("sh -c true", "sh"),
                ("git", "git"), ("gh", "gh")):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    self.unbound(what))

    def test_an_inert_verb_that_writes_through_a_redirect_is_a_note(self):
        for between, what in (
                ("echo hi > /tmp/b.md", "> /tmp/b.md"),
                ("echo hi >> /tmp/b.md", ">> /tmp/b.md"),
                ("printf hi > /tmp/b.md", "> /tmp/b.md"),
                ("cat > /tmp/b.md", "> /tmp/b.md"),
                ("cat x > ./b.md", "> ./b.md"),
                ("true 2> /tmp/b.md", "2> /tmp/b.md"),
                ("echo hi &> /tmp/b.md", "&> /tmp/b.md"),
                ("echo hi >| /tmp/b.md", ">| /tmp/b.md")):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    self.unbound(what))
        self.assert_a_note(
            self.spelled("/tmp/b.md", between="cat x | tee /tmp/b.md\n"))

    def test_an_inert_verb_that_runs_or_assigns_in_an_argument_is_a_note(self):
        for verb in ("echo", "printf", "cat", "grep x", "ls", "test -f", "[",
                     "wc", "head", "stat", "sleep"):
            for argument in ("`rm /tmp/b.md`", "$[1+1]", "${S:=x}", "${S=x}",
                             '"$(date)"', '"`date`"', "x${S:=y}z"):
                with self.subTest(verb=verb, argument=argument):
                    self.assertEqual(
                        run(self.spelled("/tmp/b.md",
                                         between=f"{verb} {argument}\n")),
                        self.unbound(verb.split()[0]))
            for argument in ("$(rm /tmp/b.md)", "$((1+1))", "$((S=1))"):
                with self.subTest(verb=verb, argument=argument):
                    self.assert_a_note(
                        self.spelled("/tmp/b.md",
                                     between=f"{verb} {argument}\n"))

    def test_a_bracket_expansion_in_an_inert_argument_unbinds(self):
        """P3 gap 2: `echo $[1+1]` unbinds like `$((1+1))`."""
        self.assertEqual(
            run(self.spelled("/tmp/b.md", between="echo $[1+1]\n")),
            self.unbound("echo"))
        self.assert_a_note(
            self.spelled("/tmp/b.md", between="echo $((1+1))\n"))

    def test_printf_with_v_assigns_and_is_a_note(self):
        for between in ("printf -vS x", "printf -v S x", "printf -v S",
                        "printf -v T '%s' x"):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    self.unbound("printf"))
        self.assertEqual(
            run(self.spelled("/tmp/b.md", between="printf '%s' -vx\n")),
            self.unbound("printf"))
        self.assertEqual(
            run(self.spelled("/tmp/b.md", between="printf '%s\\n' v\n")),
            refused(self.BAD + "\n"))

    def test_an_assignment_to_a_name_the_spelling_holds_is_a_note(self):
        for between, what in ((": ${S:=x}", ":"), ("echo ${S:=x}", "echo"),
                              ("S=1", "S="), ("export S=1", "export"),
                              ("T=1 S=2", "T="), ("printf -v S x", "printf")):
            for spelling in ("$S/b.md", "${S}/b.md"):
                with self.subTest(between=between, spelling=spelling):
                    self.assertEqual(
                        run(self.spelled(spelling, before="S=/tmp\n",
                                         between=between + "\n")),
                        self.unbound(what, spelling))
        self.assert_a_note(self.spelled("$S/b.md", before="S=/tmp\n",
                                        between="echo $((S=1))\n"))
        self.assertEqual(
            run(self.spelled("$S/b.md", before="S=/tmp\n",
                             between="T=1\nexport U=1\n")),
            refused(self.BAD + "\n"))

    def test_an_assignment_whose_value_runs_a_command_is_a_note(self):
        for between, what in (("T=`date`", "T="), ("T=$[1+1]", "T="),
                              ("export T=`date`", "export"),
                              ("T=${U:=x}", "T="), ('T="$(date)"', "T=")):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    self.unbound(what))
        for between in ("T=$(date)", "export T=$(date)", "T=$((1+1))"):
            with self.subTest(between=between):
                self.assert_a_note(
                    self.spelled("/tmp/b.md", between=between + "\n"))

    def test_an_exec_descriptor_opened_onto_the_file_unbinds_a_dup(self):
        self.assert_a_note(
            self.spelled("/tmp/b.md", before="exec 3> /tmp/b.md\n",
                         between="echo hi >&3\n"))
        self.assertEqual(
            run(self.spelled("/tmp/b.md", between="echo hi >&3\n")),
            refused(self.BAD + "\n"))


    # --- Milestone 3, rule 4: the inert git and gh verbs ------------------
    INERT_GIT_GH = (
        "git status", "git status --short", "git diff", "git diff HEAD~1",
        "git log", "git log --oneline -3", "git rev-parse HEAD",
        "git rev-parse --show-toplevel", "git branch --show-current",
        "git config --get user.name", "git config --get --global user.name",
        "gh pr view", "gh pr view 12 --json title", "gh pr list",
        "gh pr status", "gh pr checks 12", "gh pr diff 12",
        "gh issue view 12", "gh issue list", "gh api repos/o/r",
        "gh api repos/o/r --jq .name", 'gh api -H "Accept: x" repos/o/r',
        "gh api --paginate user", "gh api -i user", "gh api --cache 1h user", 'gh api ""',
        "git status 2>&1", "gh pr view 12 > /dev/null")

    def test_an_inert_git_or_gh_verb_between_writer_and_reader_is_judged(self):
        for between in self.INERT_GIT_GH:
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    refused(self.BAD + "\n"))
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", self.GOOD,
                                     between=between + "\n")), (0, []))

    def test_a_git_or_gh_verb_off_the_list_between_is_a_note(self):
        for between, what in (
                ("git commit -m x", "git commit"), ("git push", "git push"),
                ("git fetch", "git fetch"), ("git add .", "git add"),
                ("git checkout x", "git checkout"), ("git pull", "git pull"),
                ("git stash", "git stash"), ("git reset --hard", "git reset"),
                ("git branch", "git branch"), ("git branch -D x", "git branch"),
                ("git branch --show-current x", "git branch"),
                ("git config user.name x", "git config"),
                ("git config --get-all x", "git config"),
                ("git config --unset x", "git config"),
                ("git config --get x --unset", "git config"),
                ("git -C d status", "git -C"), ("git", "git"),
                ("gh pr checkout 1", "gh pr checkout"),
                ("gh pr edit 1", "gh pr edit"),
                ("gh pr merge 1 --delete-branch", "gh pr merge"),
                ("gh issue create", "gh issue create"),
                ("gh repo sync", "gh repo sync"),
                ("gh repo clone o/r", "gh repo clone"),
                ("gh gist clone x", "gh gist clone"),
                ("gh extension install x", "gh extension install"),
                ("gh alias set x y", "gh alias set"), ("gh foo", "gh foo"),
                ("gh -R o/r pr view", "gh -R"), ("gh", "gh")):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    self.unbound(what))

    def test_a_git_verb_with_an_option_that_writes_is_a_note(self):
        for between, what in (
                ("git diff --output=/tmp/b.md", "git diff"),
                ("git diff --output /tmp/b.md", "git diff"),
                ("git diff --outp=/tmp/x", "git diff"),
                ("git diff --output-indicator-new=+", "git diff"),
                ("git log --output=/tmp/x", "git log"),
                ("git status -f /tmp/x", "git status"),
                ("git status -f/tmp/x", "git status"),
                ("git diff --file /tmp/x", "git diff"),
                ("git rev-parse --fil=/tmp/x", "git rev-parse"),
                ("git config -f /tmp/x --get a", "git config"),
                ("git config --file /tmp/x --get a", "git config"),
                ("git config --file=/tmp/x --get a", "git config"),
                ("git config --get a --file /tmp/x", "git config"),
                ("git config --get a -f /tmp/x", "git config"),
                ("git diff /tmp/b.md", "git diff"),
                ("git log -- /tmp/b.md", "git log"),
                ("git rev-parse :/tmp/b.md", "git rev-parse")):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    self.unbound(what))
        for between in ("git diff --output=/tmp/x > /tmp/b.md",
                        "git log >> /tmp/b.md", "git status | tee /tmp/b.md",
                        "git diff $(git rev-parse HEAD)",
                        "git log `echo x`"):
            with self.subTest(between=between):
                self.assert_a_note(
                    self.spelled("/tmp/b.md", between=between + "\n"))

    def test_a_gh_api_with_a_write_option_is_a_note(self):
        for options in ("--input x", "--input=x", "-X POST", "-XPOST",
                        "--method POST", "--method=POST", "-X GET",
                        "-f a=b", "-fa=b", "-F a=b", "-Fa=b", "--field a=b",
                        "--field=a=b", "--raw-field a=b", "--raw-field=a=b",
                        "--output /tmp/b.md", "--output=/tmp/b.md",
                        "-iX POST", "--paginate -f a=b"):
            with self.subTest(options=options):
                self.assertEqual(
                    run(self.spelled(
                        "/tmp/b.md",
                        between=f"gh api {options} repos/o/r\n")),
                    self.unbound("gh api"))

    def test_a_git_verb_between_leaves_a_relative_file_to_the_cd_rule(self):
        self.assertEqual(
            run(self.spelled("b.md", between="git status\n")),
            refused(self.BAD + "\n"))
        self.assertEqual(
            run(self.spelled("$S/b.md", before="S=/tmp\n",
                             between="git diff HEAD\n")),
            refused(self.BAD + "\n"))
        self.assertEqual(
            run(self.spelled("b.md", between="git diff b.md\n")),
            self.unbound("git diff", "b.md"))


    # --- Milestone 3 review fixes -----------------------------------------
    def test_a_redirect_target_that_runs_a_command_is_a_note(self):
        for between in ('cat <<< "$(echo good > /tmp/b.md)"',
                        'grep x < "$(rm /tmp/b.md)"',
                        'cat < "`rm /tmp/b.md`"',
                        'git log < "$(rm -f /tmp/b.md)"',
                        'cat < "${S:=/x}"',
                        'cat < "$[1+1]"',
                        "cat <<X\n$(echo good > /tmp/b.md)\nX",
                        "cat <<X\n`rm /tmp/b.md`\nX",
                        "cat <<X\na\\nb\nX",
                        'cat < "$(cat <<\'B\'\nx\nB\n)"'):
            with self.subTest(between=between):
                code, lines = run(
                    self.spelled("/tmp/b.md", between=between + "\n"))
                self.assertEqual(code, 0)
                self.assertEqual(len(lines), 1)
                self.assertIn("may be rewritten or removed by", lines[0])
        code, lines = run(self.spelled(
            "/tmp/b.md", between='cat <<< "$(rm /tmp/b.md)"\n'))
        self.assertEqual(
            lines, [note("/tmp/b.md may be rewritten or removed by <<< "
                         "$(rm /tmp/b.md) between the heredoc and gh pr "
                         "create")])

    def test_a_literal_heredoc_or_here_string_between_is_judged(self):
        for between in ("cat <<'X'\nhello $S\nX", "cat <<'X'\nhello\nX",
                        "cat <<X\nplain\nX", "cat <<< plain"):
            with self.subTest(judged=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    refused(self.BAD + "\n"))

    def test_a_here_string_that_runs_a_command_is_a_note(self):
        """`cat <<< 'literal $(x)'` holds `$(` in its argument, which the
        rule reads whether or not the shell quoted it."""
        self.assertEqual(
            run(self.spelled("/tmp/b.md",
                             between="cat <<< 'literal $(x)'\n")),
            self.unbound("<<< literal $(x)"))

    def test_a_masked_substitution_in_an_argument_or_value_is_a_note(self):
        for between in ('echo "$(cat <<B\n$(rm -f /tmp/b.md)\nB\n)"',
                        'T="$(cat <<B\n`rm /tmp/b.md`\nB\n)"',
                        "printf %s \"$(cat <<'B'\nhello\nB\n)\"",
                        "export T=\"$(cat <<'B'\nhello\nB\n)\""):
            with self.subTest(between=between):
                code, lines = run(
                    self.spelled("/tmp/b.md", between=between + "\n"))
                self.assertEqual(code, 0)
                self.assertEqual(len(lines), 1)
                self.assertIn("may be rewritten or removed by", lines[0])
        with tempfile.TemporaryDirectory() as tmp:
            top = Path(tmp)
            _git_repo(top, "git@github.com:me/this.git")
            (top / "d").mkdir()
            code, lines = run(self.spelled(
                "/tmp/b.md", between="cd \"$(cat <<'B'\nd\nB\n)\"\n"), top)
            self.assertEqual(code, 0)
            self.assertIn("may be rewritten or removed by cd", lines[0])

    def test_an_ansi_c_string_hides_what_the_tokenizer_cannot_see(self):
        for between in ("echo $'\\''; rm /tmp/b.md; \\'\n",
                        "cat $'\\''; rm /tmp/b.md; \\'\n",
                        "echo $'a'\n"):
            with self.subTest(between=between):
                code, lines = run(
                    self.spelled("/tmp/b.md", between=between))
                self.assertEqual(code, 0)
                self.assertEqual(len(lines), 1)
                self.assertIn("may be rewritten or removed by", lines[0])
        self.assertEqual(run(self.spelled("/tmp/b.md")), refused(self.BAD + "\n"))

    def test_a_descriptor_prefix_is_told_from_a_command_word(self):
        """A digit word touching its redirect operator is a descriptor
        prefix: `2>&1` and the other duplications and closes are judged.
        A digit word a space away is a command, and every other prefixed
        redirect is a note."""
        for between in ("2>&1", "echo hi 2>&1", "1>&2", "2>&-", "10>&1",
                        "true 2>&1 >&2", "2>&1 2>&1"):
            with self.subTest(judged=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    refused(self.BAD + "\n"))
        for between, what in (
                ("2 >&1", "2"), ("5 < /tmp/x", "5"),
                ("2 > /tmp/b.md", "> /tmp/b.md"),
                ('"2">&1', "2"), ("\\2>&1", "2"), ("x2>&1", "x2"),
                ("$2>&1", "$2"), ("2 > /dev/null", "2"),
                ("2> /tmp/b.md", "2> /tmp/b.md"),
                ("2>/tmp/b.md", "2> /tmp/b.md"),
                ("2>> /tmp/b.md", "2>> /tmp/b.md"),
                ("2>| /tmp/b.md", "2>| /tmp/b.md"),
                ("1>&2 > /tmp/b.md", "> /tmp/b.md"),
                ("2>&1>/tmp/b.md", "> /tmp/b.md"),
                ("echo hi 2>&1>/tmp/b.md", "> /tmp/b.md"),
                ("&> /tmp/b.md", "&> /tmp/b.md"),
                ("2>&1 > /tmp/b.md", "> /tmp/b.md"),
                ("2>&1 2>/tmp/b.md", "2> /tmp/b.md"),
                ("2>&1x", "2>& 1x"),
                ("3<<'X'\nx\nX", "3<< __pr_body_preflight_heredoc_1__"),
                ("3<> /tmp/b.md", "3<> /tmp/b.md")):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    self.unbound(what))

    def test_a_prefixed_read_or_null_redirect_is_judged_wherever_it_sits(self):
        for between in ("git status 2>/dev/null", "ls x 2>/dev/null",
                        "echo hi 1>/dev/null", "cat 2<&0", "cat 0< /tmp/x",
                        "echo hi 2>> /dev/null", "echo hi 2>| /dev/null",
                        "echo hi 2>/dev/stderr", "5< /tmp/x"):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    refused(self.BAD + "\n"))
        for tail in (" 2>/dev/null", " 1>/dev/null", " 2<&0"):
            with self.subTest(reader=tail):
                self.assertEqual(run(self.spelled("/tmp/b.md") + tail),
                                 refused(self.BAD + "\n"))
        for tail, what in ((" 2>/tmp/b.md", "2> /tmp/b.md"),
                           (" 1>&2 > /tmp/b.md", "> /tmp/b.md"),
                           (" 3<> /tmp/b.md", "3<> /tmp/b.md")):
            with self.subTest(reader=tail):
                self.assertEqual(run(self.spelled("/tmp/b.md") + tail),
                                 self.unbound(what))
        for closer in ("}", "done", "fi"):
            opener = {"}": "{", "done": "while true; do",
                      "fi": "if true; then"}[closer]
            with self.subTest(closer=closer):
                self.assertEqual(
                    run(self.closed(opener, closer, " 2>/dev/null")),
                    refused(self.BAD + "\n"))
                self.assertEqual(
                    run(self.closed(opener, closer, " 2>/tmp/b.md")),
                    self.unbound("2> /tmp/b.md"))

    def test_a_descriptor_prefix_is_never_part_of_a_writer(self):
        for writer in ("cat 1> /tmp/b.md <<'EOF'\nx\nEOF\n",
                       "cat > /tmp/b.md 3<<'EOF'\nx\nEOF\n",
                       "cat 0<<'EOF' > /tmp/b.md\nx\nEOF\n"):
            with self.subTest(writer=writer):
                self.assertEqual(run(writer + self.READ),
                                 (0, [self.NOT_FIRST]))

    def test_the_splitter_reads_a_descriptor_prefix_off_the_source(self):
        Simple = pr_body_preflight.Simple
        for command, expected in (
                ("a 2>&1", [Simple(["a"], [("2>&", "1")], "")]),
                ("a 2 >&1", [Simple(["a", "2"], [(">&", "1")], "")]),
                ("a 2>f", [Simple(["a"], [("2>", "f")], "")]),
                ("a;2>&1", [Simple(["a"], [], ""),
                            Simple([], [("2>&", "1")], ";")]),
                ("a 12<f", [Simple(["a"], [("12<", "f")], "")]),
                ('a "2">&1', [Simple(["a", "2"], [(">&", "1")], "")]),
                ("a x2>&1", [Simple(["a", "x2"], [(">&", "1")], "")]),
                ("a 2<(b)", [Simple(["a", "b"], [("procsub", "<(")], "")])):
            with self.subTest(command=command):
                got = self.split(command)
                self.assertEqual(got[:len(expected)], expected)

    def test_an_ansi_c_string_sets_a_flag_only_when_it_is_one(self):
        for command, flagged in (
                ("echo $'a'", True), ("echo $'\\''; x; \\'", True),
                ("grep -n 'TODO$' x", False), ("echo 'costs $'", False),
                ("gh pr create -t 'costs $'", False),
                ('echo "$\'a\'"', False), ("cat <<'E'\n$'x'\nE\n", False),
                ("echo $'a' # c", True), ("echo # $'a'", False)):
            with self.subTest(command=command):
                unrun = pr_body_preflight._Unrun(command)
                unrun.run()
                self.assertEqual(unrun.ansi_c, flagged)

    def test_a_string_ending_in_a_dollar_between_is_not_an_ansi_c_string(self):
        """The `$'` in `'a $'b` is a closing quote after a dollar, not an
        ANSI-C string; a word ending in a bare `$` stays a note by the
        argument rule (the tokenizer splits `$(` after its `$`)."""
        for between in ("echo 'a $'b", 'echo "cost $\'x\'"'):
            with self.subTest(judged=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    refused(self.BAD + "\n"))
        for between, what in (("grep -n 'TODO$' /tmp/x", "grep"),
                              ("echo 'costs $'", "echo")):
            with self.subTest(note=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    self.unbound(what))

    def before(self, what, spelling="/tmp/b.md"):
        return (0, [note(f"{spelling} may be rewritten or removed by {what} "
                         "before the heredoc")])

    def test_an_exec_behind_a_keyword_group_or_time_before_the_writer(self):
        for before in ("{ exec > /tmp/b.md; }\n", "{ exec 3> /tmp/b.md; }\n",
                       "if true; then exec 3> /tmp/b.md; fi\n",
                       "if true; then\nexec 3> /tmp/b.md\nfi\n",
                       "time exec 3> /tmp/b.md\n", "! exec 3> /tmp/b.md\n",
                       "while true; do exec 3>> /tmp/b.md; done\n",
                       "echo exec > /tmp/log\n",
                       "X=1 exec 3> /tmp/b.md\n", "command exec 3> /tmp/b.md\n",
                       "builtin exec 3>> /tmp/b.md\n",
                       "X=1 Y=2 command exec 3<> /tmp/b.md\n",
                       "exec 5<<'X'\nx\nX\n"):
            with self.subTest(before=before):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", before=before,
                                     between="echo hi >&3\n")),
                    self.before("an open descriptor"))
        for before in ("{ exec 3>&1; }\n", "time exec 2>&1\n",
                       "if true; then exec > /dev/null; fi\n",
                       "{ echo exec; }\n", "{ true; }\n", "X=1 exec 3>&1\n",
                       "exec 2>/dev/null\n", "exec 1>/dev/null\n",
                       "exec 3<&0\n", "exec 4>&-\n"):
            with self.subTest(judged=before):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", before=before)),
                    refused(self.BAD + "\n"))

    def test_a_named_descriptor_opened_onto_a_file_before_the_writer_unbinds(
            self):
        for before in ("true {fd}> /tmp/b.md\n", "true {fd}>> /tmp/b.md\n",
                       "{ true; } {fd}> /tmp/b.md\n", "exec {fd}> /tmp/b.md\n"):
            with self.subTest(before=before):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", before=before,
                                     between="echo hi >&10\n")),
                    self.before("an open descriptor"))
        for before in ("true {fd}>&2\n", "true {fd}> /dev/null\n",
                       "echo {x}\n"):
            with self.subTest(judged=before):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", before=before)),
                    refused(self.BAD + "\n"))

    WRITER_STEERING = ("PATH=/x", "export PATH=/x", "LD_PRELOAD=x",
                       "DYLD_INSERT_LIBRARIES=x", "BASH_ENV=x", "ENV=x",
                       "if true; then PATH=/x; fi", "T=1 PATH=/x")
    COMMAND_STEERING = ("export GIT_EXTERNAL_DIFF=x", "export GIT_TRACE=1",
                        "HOME=/x", "export HOME=/x", "XDG_CONFIG_HOME=/x",
                        "BROWSER=x", "export PAGER=cat", "export GH_PAGER=cat",
                        "export GIT_EDITOR=true", "IFS=,", "GH_HOST=h",
                        "{ export HOME=/x; }")

    def test_a_name_that_changes_the_writer_unbinds_wherever_it_is_set(self):
        for before in self.WRITER_STEERING:
            what = ("export" if before.startswith("export")
                    else before.split("=")[0].split()[-1] + "=")
            for between in ("", "git status\n"):
                with self.subTest(before=before, between=between):
                    command = self.spelled("/tmp/b.md", before=before + "\n",
                                           between=between)
                    code, lines = run(command)
                    self.assertEqual(code, 0)
                    self.assertEqual(len(lines), 1)
                    self.assertIn("before the heredoc", lines[0])

    def test_another_steering_name_matters_only_with_a_command_between(self):
        for before in self.COMMAND_STEERING:
            with self.subTest(before=before, between="git status"):
                code, lines = run(self.spelled(
                    "/tmp/b.md", before=before + "\n", between="git status\n"))
                self.assertEqual(code, 0)
                self.assertEqual(len(lines), 1)
                self.assertIn("before the heredoc", lines[0])
            with self.subTest(before=before, between="none"):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", before=before + "\n")),
                    refused(self.BAD + "\n"))
        for before in ("export T=1\n", "T=1\n", "PATH=/x git status\n",
                       "echo PATH=/x\n", "echo $HOME\n", "export S=/tmp\n"):
            with self.subTest(judged=before):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", before=before,
                                     between="git status\n")),
                    refused(self.BAD + "\n"))

    def test_a_function_alias_or_trap_before_the_writer_unbinds(self):
        for before, what in (
                ("ls() { rm /tmp/b.md; }\n", "a function definition"),
                ("ls () { rm /tmp/b.md; }\n", "a function definition"),
                ("function ls { rm /tmp/b.md; }\n", "a function definition"),
                ("{ function ls { :; }; }\n", "a function definition"),
                ("ls()\n{\nrm /tmp/b.md\n}\n", "a function definition"),
                ("alias ls='rm /tmp/b.md'\n", "alias"),
                ("trap 'rm /tmp/b.md' DEBUG\n", "trap"),
                ("trap 'rm /tmp/b.md' ERR\n", "trap"),
                ("trap 'x' EXIT DEBUG\n", "trap"), ("trap -p\n", "trap"),
                ("{ alias ls=x; }\n", "alias"),
                ("command trap 'x' ERR\n", "trap")):
            with self.subTest(before=before):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", before=before,
                                     between="ls /tmp\n")),
                    self.before(what))
        for before in ("echo alias ls\n", "echo trap\n", "unalias ls\n",
                       "echo 'ls() { :; }'\n", "grep -n function src.js\n",
                       "echo function\n", "trap 'rm -f /tmp/b.md' EXIT\n",
                       "trap 'x' 0\n", "trap 'x' EXIT EXIT\n"):
            with self.subTest(judged=before):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", before=before,
                                     between="ls /tmp\n")),
                    refused(self.BAD + "\n"))

    def test_an_assignment_to_a_name_that_steers_a_command_is_a_note(self):
        for between, what in (
                ("PATH=/x", "PATH="), ("export PATH=/x", "export"),
                ("IFS=,", "IFS="), ("GIT_DIR=/x", "GIT_DIR="),
                ("GH_REPO=o/r", "GH_REPO="), ("BASH_ENV=x", "BASH_ENV="),
                ("ENV=x", "ENV="), ("LD_PRELOAD=x", "LD_PRELOAD="),
                ("DYLD_INSERT_LIBRARIES=x", "DYLD_INSERT_LIBRARIES="),
                ("PAGER=cat", "PAGER="), ("GIT_PAGER=cat", "GIT_PAGER="),
                ("export PAGER=cat", "export"), ("MYPAGER=x", "MYPAGER="),
                ("T=1 PATH=/x", "T=")):
            with self.subTest(between=between):
                self.assertEqual(
                    run(self.spelled("/tmp/b.md", between=between + "\n")),
                    self.unbound(what))

    # --- Milestone 4: the PRD's remaining shapes --------------------------
    def assert_pair(self, build, cwd=None):
        """`build(body)` is refused for BAD and silent for GOOD."""
        self.assertEqual(run(build(self.BAD), cwd), refused(self.BAD + "\n"))
        self.assertEqual(run(build(self.GOOD), cwd), (0, []))

    def test_a_quoted_delimiter_is_judged_verbatim(self):
        for delim in ("'EOF'", '"EOF"', "\\EOF"):
            with self.subTest(delim=delim):
                self.assert_pair(
                    lambda body: self.write(body, delim=delim) + self.READ)
        bad, good = self.BAD + " $HOME `x` \\n", self.GOOD + "\n$X `y`"
        self.assertEqual(run(self.write(bad) + self.READ),
                         refused(bad + "\n"))
        self.assertEqual(run(self.write(good) + self.READ), (0, []))

    def test_an_unquoted_delimiter_without_expansion_is_a_pair(self):
        self.assert_pair(
            lambda body: self.write(body, delim="EOF") + self.READ)

    def test_a_dash_heredoc_with_tab_indented_lines_is_a_pair(self):
        for opener in ("<<-EOF", "<<-'EOF'"):
            with self.subTest(opener=opener):
                self.assert_pair(
                    lambda body: (
                        f"cat > /tmp/b.md {opener}\n"
                        + "".join(f"\t{line}\n" for line in body.split("\n"))
                        + "\tEOF\n" + self.READ))

    def test_a_leading_cd_to_the_repository_is_a_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            top = Path(tmp)
            _git_repo(top, "git@github.com:me/this.git")
            (top / "d").mkdir()
            for name, build in (
                    ("newline", lambda body: "cd d\n" + self.write(body)
                     + self.READ),
                    ("semicolon", lambda body: "cd d; " + self.write(body)
                     + self.READ),
                    ("and on one line", lambda body: (
                        "cd d && cat > /tmp/b.md <<'EOF' && gh pr create "
                        f"--title t --body-file /tmp/b.md\n{body}\nEOF\n"))):
                with self.subTest(shape=name):
                    self.assert_pair(build, top)
            for command in ("cd d &&\n" + self.write(self.BAD) + self.READ,
                            "cd .. && " + self.write(self.BAD) + self.READ):
                with self.subTest(note=command):
                    self.assertEqual(run(command, top), (0, [self.CHAIN_NOTE]))
            self.assertEqual(
                run("cd ..\n" + self.write(self.BAD) + self.READ, top),
                (0, [note("a cd before gh pr create leaves this repository")]))

    def test_two_readers_are_each_bound_to_their_own_writer(self):
        def two(first, second, path="/tmp/b.md"):
            return (self.write(first, path=path)
                    + f"gh pr create --title t --body-file {path}\n"
                    + self.write(second, path=path)
                    + f"gh pr create --title u --body-file {path}")

        self.assertEqual(
            run(two(self.BAD, self.GOOD)), refused(self.BAD + "\n"))
        self.assertEqual(
            run(two(self.GOOD, self.BAD)), refused(self.BAD + "\n"))
        self.assertEqual(
            run(two(self.BAD, self.BAD)),
            (2, gates.pr_body_problems(self.BAD + "\n") * 2 + [POINTER]))
        self.assertEqual(run(two(self.GOOD, self.GOOD)), (0, []))
        self.assertEqual(run(two(self.BAD, self.GOOD, "/tmp/c.md")),
                         refused(self.BAD + "\n"))

    def test_a_second_reader_with_no_writer_of_its_own_is_a_note(self):
        """A reader between writer and the second reader is off the inert
        list, so the second reader's binding is a note."""
        for first in (self.BAD, self.GOOD):
            with self.subTest(first=first):
                code, lines = run(
                    self.write(first) + self.READ + "\n" + self.READ)
                self.assertEqual(code, 2 if first == self.BAD else 0)
                self.assertEqual(
                    lines[-1 if first == self.GOOD else -2],
                    note("/tmp/b.md may be rewritten or removed by gh pr "
                         "create between the heredoc and gh pr create"))

    def test_a_cleanup_after_the_reader_does_not_unbind(self):
        for cleanup in ("\nrm /tmp/b.md", " && rm -f /tmp/b.md",
                        "; rm /tmp/b.md", "\nrm /tmp/b.md\n> /tmp/b.md"):
            with self.subTest(cleanup=cleanup):
                self.assert_pair(
                    lambda body: self.write(body) + self.READ + cleanup)

    def test_a_heredoc_inside_a_substitution_never_pairs_with_a_reader(self):
        for first in ('echo "$(cat > /tmp/b.md <<\'A\'\n{}\nA\n)"\n',
                      "X=$(sed q > /tmp/b.md <<'A'\n{}\nA\n)\n",
                      'echo "$(sed q <<A\n{}\nA\n)" > /tmp/b.md\n'):
            with self.subTest(first=first):
                self.assertEqual(
                    run(first.format(self.BAD) + self.READ),
                    (0, [self.NOT_FIRST]))
        # a writer-shaped command inside `$(`: the chain rule refuses it
        # (its own joiner is `(`), a note either way and never a verdict
        self.assert_a_note("X=$(cat > /tmp/b.md <<'A'\n" + self.BAD
                           + "\nA\n)\n" + self.READ)

    def test_a_heredoc_inside_a_substitution_does_not_shift_the_pairing(self):
        """The substitution's heredoc is queued first; the real writer
        after it still pairs with its own text, not the earlier one."""
        first = 'echo "$(sed q <<A\n{}\nA\n)"\n'
        self.assertEqual(
            run(first.format(self.GOOD) + self.write(self.BAD) + self.READ),
            refused(self.BAD + "\n"))
        self.assertEqual(
            run(first.format(self.BAD) + self.write(self.GOOD) + self.READ),
            (0, []))
        # after `X=$(…)` the next line's joiner is `)` plus a newline, which
        # the chain rule does not read as a start: a note, never a verdict
        self.assert_a_note("X=$(sed q <<A\n" + self.GOOD + "\nA\n)\n"
                           + self.write(self.BAD) + self.READ)

    def test_a_body_holding_its_own_heredoc_snippet_is_judged_on_the_text(self):
        """The file text, not the placeholder the masking leaves behind:
        a snippet holding both required lines satisfies B on its own."""
        passing = "```\n$(cat <<'B'\nWO-0003\nCloses #9\nB\n)\n```"
        self.assertEqual(gates.pr_body_problems(passing + "\n"), [])
        self.assertEqual(run(self.write(passing) + self.READ), (0, []))
        failing = "```\n$(cat <<'B'\ninner\nB\n)\n```\n" + self.BAD
        self.assertEqual(run(self.write(failing) + self.READ),
                         refused(failing + "\n"))
        self.assert_a_note(self.write(passing, delim="EOF") + self.READ)

    def test_a_log_redirect_before_a_first_command_body_file_reads_from_disk(
            self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.md").write_text(self.GOOD, encoding="utf-8")
            self.assertEqual(
                run("> log\ngh pr create -F x.md", cwd=tmp), (0, []))
            (Path(tmp) / "x.md").write_text(self.BAD, encoding="utf-8")
            self.assertEqual(
                run("> log\ngh pr create -F x.md", cwd=tmp),
                refused(self.BAD))

    def test_a_malformed_payload_or_a_raising_binding_fails_open(self):
        for text in ("not json", "[1, 2]", json.dumps({"tool_input": {}}),
                     json.dumps({"tool_input": {"command": 5}})):
            with self.subTest(payload=text):
                self.assertEqual(
                    pr_body_preflight.preflight(text), (0, []))
        command = self.write(self.BAD) + self.READ
        with mock.patch("pr_body_preflight._bound_body",
                        side_effect=RuntimeError("boom")):
            code, lines = run(command)
        self.assertEqual(code, 0)
        self.assertEqual(
            lines, [note("RuntimeError: boom")])
        self.assertEqual(
            sum(line.startswith("pr-body-preflight: not checked")
                for line in lines), 1)



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


class TestTextTheShellNeverRuns(unittest.TestCase):
    """Review finding 1: a heredoc body and a comment tail are never run,
    so a `gh pr create` inside one is not a command and is never judged."""

    def test_review_reproductions_are_not_commands(self):
        for command in (
                "cat > notes.md <<'EOF'\nExample:\n"
                "  gh pr create --title x --body \"WIP\"\nEOF",
                "git commit -F - <<'EOF'\ndocs: x\n\n"
                "gh pr create --body \"fix stuff\" is refused now\nEOF",
                "cat <<'EOF' > x\nX=1 gh pr create --body 'nope'\nEOF",
                "true # later ; gh pr create --body 'bad'"):
            with self.subTest(command=command):
                self.assertEqual(run(command), (0, [NOT_SEEN]))

    def test_every_heredoc_operator_spelling_hides_its_body(self):
        body = "gh pr create --body bad\n"
        for opener, close in (("<<EOF", "EOF"), ("<< EOF", "EOF"),
                              ('<<"EOF"', "EOF"), ("<<\\EOF", "EOF"),
                              ("<<E'O'F", "EOF"), ("<<-EOF", "\tEOF"),
                              ("<<-'EOF'", "\t\tEOF"),
                              ("<<EOF <<TWO", "EOF\n" + body + "TWO")):
            with self.subTest(opener=opener):
                command = f"cat > f {opener}\n\t{body}{close}\nls"
                self.assertEqual(run(command), (0, [NOT_SEEN]))

    def test_a_heredoc_inside_a_substitution_hides_its_body(self):
        command = ("x=$(python3 - <<'EOF'\nprint('gh pr create --body bad')"
                   "\ngh pr create --body bad\nEOF\n)")
        self.assertEqual(run(command), (0, [NOT_SEEN]))

    def test_a_heredoc_with_no_delimiter_line_hides_the_rest(self):
        self.assertEqual(run("cat <<EOF\ngh pr create --body bad"),
                         (0, [NOT_SEEN]))

    def test_a_real_command_after_a_heredoc_is_still_judged(self):
        """An apostrophe in the body no longer breaks the parse."""
        command = ("cat > b.md <<'EOF'\nit's done\nEOF\n"
                   'gh pr create --body "x"')
        self.assertEqual(run(command), refused("x"))

    def test_lookalikes_of_a_heredoc_are_not_heredocs(self):
        for command in ('cat <<< "a"; gh pr create --body "x"',
                        'echo "a <<EOF"\ngh pr create --body "x"',
                        "echo 'a <<EOF'\ngh pr create --body \"x\"",
                        'echo $((1<<2)); gh pr create --body "x"'):
            with self.subTest(command=command):
                self.assertEqual(run(command), refused("x"))

    def test_a_comment_line_is_not_a_command(self):
        self.assertEqual(run("# a note; gh pr create --body bad\nls"),
                         (0, [NOT_SEEN]))

    def test_a_comment_after_a_real_command_does_not_hide_it(self):
        self.assertEqual(run('gh pr create --body "x" # note'),
                         refused("x"))

    def test_a_hash_that_starts_no_word_is_body_text(self):
        for value, body in (('"x # y"', "x # y"), ("x#1", "x#1"),
                            ("'a #b'", "a #b"), ("x\\ #1", "x #1")):
            with self.subTest(value=value):
                self.assertEqual(run(f"gh pr create --body {value}"),
                                 refused(body))

    def test_a_heredoc_inside_backticks_fails_open(self):
        """Re-review: a backtick span was kept whole, so its heredoc
        body reached the tokenizer as commands."""
        for opener in ("<<EOF", "<<'EOF'"):
            with self.subTest(opener=opener):
                self.assertEqual(
                    run(f"x=`cat {opener}\ngh pr create --body bad\nEOF\n`"),
                    (0, [note("cannot parse the command: "
                              "a heredoc inside backticks")]))

    def test_a_comment_after_a_line_continuation_is_a_comment(self):
        """Re-review: the shell removes a backslash-newline, so a `#`
        right after one starts a word when the text before it did."""
        self.assertEqual(
            run("echo a \\\n# ; gh pr create --body bad"), (0, [NOT_SEEN]))
        self.assertEqual(run('gh pr create --body x\\\n#1'), refused("x#1"))

    def test_a_line_continuation_joins_the_lines(self):
        """Re-review: the shell removes a backslash-newline outside
        single quotes, so a flag on the next line belongs to the same
        gh pr create and a quoted body is joined."""
        self.assertEqual(run("gh pr create --body bad \\\n  --web"),
                         (0, [note("--web leaves the body to gh")]))
        self.assertEqual(
            run('gh pr create --body "WO-0003 per breakdown. '
                'Closes \\\n#108"'), (0, []))
        self.assertEqual(run("gh pr create \\\n  --body bad"), refused("bad"))
        self.assertEqual(run("gh pr create --body 'a\\\nb'"),
                         refused("a\\\nb"))

    def test_an_arithmetic_command_shift_is_not_a_heredoc(self):
        """Re-review: `(( … << … ))` read as a heredoc cut real lines."""
        self.assertEqual(
            run("((y = 1<<2))\necho '\n2\ngh pr create --body bad\n' \"' #\""),
            (0, [NOT_SEEN]))
        self.assertEqual(run('(( n <<= 1 ))\ngh pr create --body "x"'),
                         refused("x"))

    def test_a_parameter_expansion_holding_a_comment_or_heredoc_fails_open(
            self):
        """Re-review: a `#` after a blank inside `${ }` is not a comment."""
        self.assertEqual(
            run("echo ${x:- #'\ngh pr create --body bad\n' \"' #\"}"),
            (0, [note("cannot parse the command: "
                      "a ${ } holding # or << the hook cannot read")]))
        self.assertEqual(run('echo ${#x}; gh pr create --body "x"'),
                         refused("x"))

    def test_a_shape_the_hook_cannot_classify_fails_open(self):
        for command, reason in (
                ("cat <<$X\ngh pr create --body bad\n$X",
                 "a heredoc delimiter the hook cannot read"),
                ("cat <<\ngh pr create --body bad",
                 "a heredoc with no delimiter"),
                ('gh pr create --body "x" $(ls',
                 "an unclosed command substitution")):
            with self.subTest(command=command):
                self.assertEqual(
                    run(command),
                    (0, [note(f"cannot parse the command: {reason}")]))


def _git_repo(root, url):
    """A directory that git would call a checkout with one remote."""
    (root / ".git").mkdir(parents=True)
    (root / ".git" / "config").write_text(
        f'[core]\n\tbare = false\n[remote "origin"]\n\turl = {url}\n'
        "\tfetch = +refs/heads/*:refs/remotes/origin/*\n", encoding="utf-8")


class TestOtherRepository(unittest.TestCase):
    """Review finding 3: B is this repository's rule, so a PR aimed at
    another repository is never judged by it."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.top = Path(tmp.name).resolve()
        self.cwd = self.top / "this"
        _git_repo(self.cwd, "git@github.com:me/this.git")
        (self.cwd / "sub").mkdir()
        _git_repo(self.top / "that", "https://github.com/me/that.git")
        (self.top / "plain").mkdir()

    def run_here(self, command, environ=None):
        return pr_body_preflight.preflight(payload(command, self.cwd),
                                           environ)

    def test_a_repo_flag_naming_another_repository_fails_open(self):
        for flag in ("-R other/repo", "--repo other/repo",
                     "--repo=other/repo", "-Rother/repo", "-R=other/repo",
                     "-R github.com/other/repo"):
            value = flag.split("=", 1)[-1].split()[-1].removeprefix("-R")
            with self.subTest(flag=flag):
                self.assertEqual(
                    self.run_here(f'gh pr create {flag} --body "x"'),
                    (0, [note(f"the PR targets {value}, "
                              "not this repository")]))

    def test_gh_repo_naming_another_repository_fails_open(self):
        reason = note("the PR targets other/repo, not this repository")
        for command in ('GH_REPO=other/repo gh pr create --body "x"',
                        'export GH_REPO=other/repo && '
                        'gh pr create --body "x"'):
            with self.subTest(command=command):
                self.assertEqual(self.run_here(command), (0, [reason]))
        self.assertEqual(
            self.run_here('gh pr create --body "x"',
                          {"GH_REPO": "other/repo"}),
            (0, [reason]))

    def test_main_reads_gh_repo_from_its_environment(self):
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"GH_REPO": "other/repo"}), \
                redirect_stderr(err):
            code = pr_body_preflight.main([], stdin=io.StringIO(
                payload('gh pr create --body "x"', self.cwd)))
        self.assertEqual(
            (code, err.getvalue().splitlines()),
            (0, [note("the PR targets other/repo, not this repository")]))

    def test_naming_this_repository_is_still_judged(self):
        for command in ('gh pr create -R me/this --body "x"',
                        'gh pr create --repo=Me/This --body "x"',
                        'gh pr create -R github.com/me/this --body "x"',
                        'GH_REPO=me/this gh pr create --body "x"',
                        'GH_REPO= gh pr create --body "x"'):
            with self.subTest(command=command):
                self.assertEqual(self.run_here(command), refused("x"))

    def test_a_named_repository_with_no_remote_to_compare_fails_open(self):
        reason = note("the PR targets me/this and this repository's "
                      "remote cannot be read")
        self.assertEqual(run('gh pr create -R me/this --body "x"'),
                         (0, [reason]))
        self.assertEqual(
            run('gh pr create -R me/this --body "x"', cwd=self.top / "plain"),
            (0, [reason]))

    def test_a_cd_inside_this_repository_is_still_judged(self):
        for command in ('cd sub && gh pr create --body "x"',
                        f'cd {self.cwd}/sub; gh pr create --body "x"',
                        'cd sub/.. && pushd sub && gh pr create --body "x"'):
            with self.subTest(command=command):
                self.assertEqual(self.run_here(command), refused("x"))

    def test_a_cd_out_of_this_repository_fails_open(self):
        reason = note("a cd before gh pr create leaves this repository")
        for command in ('cd ../that && gh pr create --body "x"',
                        'cd ../plain && gh pr create --body "x"',
                        f'cd {self.top}/that\ngh pr create --body "x"'):
            with self.subTest(command=command):
                self.assertEqual(self.run_here(command), (0, [reason]))

    def test_a_worktree_shares_its_clones_remotes_and_checkout(self):
        """A worktree's .git is a file naming its gitdir, whose commondir
        leads back to the clone's one config."""
        gitdir = self.cwd / ".git" / "worktrees" / "w"
        gitdir.mkdir(parents=True)
        (gitdir / "commondir").write_text("../..\n", encoding="utf-8")
        tree = self.top / "w"
        tree.mkdir()
        (tree / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
        here = payload('gh pr create -R me/this --body "x"', tree)
        self.assertEqual(pr_body_preflight.preflight(here), refused("x"))
        back = payload(f'cd {self.cwd} && gh pr create --body "x"', tree)
        self.assertEqual(pr_body_preflight.preflight(back), refused("x"))

    def test_a_cd_the_hook_cannot_place_fails_open(self):
        reason = note("a cd before gh pr create the hook cannot place")
        for command in ('cd "$HOME" && gh pr create --body "x"',
                        'cd && gh pr create --body "x"',
                        'cd - && gh pr create --body "x"',
                        'cd ~/x && gh pr create --body "x"',
                        'cd gone && gh pr create --body "x"'):
            with self.subTest(command=command):
                self.assertEqual(self.run_here(command), (0, [reason]))
        self.assertEqual(run('cd sub && gh pr create --body "x"'),
                         (0, [reason]))


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


class TestRegistration(unittest.TestCase):
    """The exact command registered in .claude/settings.json, run the way
    Claude Code runs it: through /bin/sh with CLAUDE_PROJECT_DIR set."""

    def registered_command(self):
        settings = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(
                encoding="utf-8"))
        entries = [entry for entry in
                   settings.get("hooks", {}).get("PreToolUse", [])
                   if entry.get("matcher") == "Bash"]
        self.assertEqual(len(entries), 1, "one PreToolUse Bash entry")
        hooks = entries[0]["hooks"]
        self.assertEqual(len(hooks), 1)
        self.assertEqual(hooks[0]["type"], "command")
        self.assertEqual(hooks[0]["timeout"], 10)
        return hooks[0]["command"]

    def shell(self, command, project_dir, text):
        env = {"PATH": os.environ.get("PATH", ""),
               "CLAUDE_PROJECT_DIR": str(project_dir)}
        return subprocess.run(["/bin/sh", "-c", command], input=text,
                              env=env, capture_output=True, text=True,
                              timeout=30)

    def test_a_failing_body_is_refused_through_the_registration(self):
        done = self.shell(self.registered_command(), REPO_ROOT,
                          payload('gh pr create --body "x"', REPO_ROOT))
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stderr.splitlines(),
                         [NO_WO, NO_CLOSES, POINTER])

    def test_a_non_gh_command_passes_through_the_registration(self):
        done = self.shell(self.registered_command(), REPO_ROOT,
                          payload("ls -la", REPO_ROOT))
        self.assertEqual((done.returncode, done.stderr), (0, ""))

    def test_a_checkout_without_the_script_passes(self):
        """The guard: python3 exits 2 on a missing script, which would
        block every Bash call; the registration turns that into 0."""
        with tempfile.TemporaryDirectory() as tmp:
            done = self.shell(self.registered_command(), tmp,
                              payload('gh pr create --body "x"', tmp))
        self.assertEqual(done.returncode, 0)


if __name__ == "__main__":
    unittest.main()
