"""tests/fake_git.py — the shared fake at the conductor's git port.

Ten hand-written git ports across the conductor suites each restated
git's exit codes, and disagreed with real git and with each other
(#781): the one behind every RunCase launch answered `config
--get-regexp` with exit 0 where real git exits 1, so a mutant _pushurls
treating any non-zero exit as failure passed every launch.

These pin FakeGit's contract against git's own documented failures, and
the last class pins that it is the one fake at the conductor's git
port, the way tests/test_fake_gh.py pins FakeGh's.
"""
import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import cli

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_git import FakeGit, default_error  # noqa: E402

TESTS = Path(__file__).resolve().parent


def git_port_fakes(directory=TESTS):
    """Every private git-port fake in the conductor suites under
    `directory`: a function or `__call__` taking only `args` that builds
    a subprocess.CompletedProcess or raises a CalledProcessError itself.

    That is what deciding git's answer looks like in a fake — a port
    that shells out to a real git (subprocess.run) builds neither, and a
    FakeGit answer returns plain stdout. Derived from the syntax, so the
    roll-call cannot go stale by being retyped; the directory is a
    parameter so the rule can be run against a planted fake.
    """
    found = []
    for path in sorted(directory.glob("test_conductor*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            params = [a.arg for a in node.args.args]
            if params not in (["args"], ["self", "args"]):
                continue
            if any(_decides_gits_answer(inner) for inner in ast.walk(node)):
                found.append((path.name, node.name))
    return found


def _decides_gits_answer(node):
    if not isinstance(node, ast.Call):
        return False
    name = node.func.attr if isinstance(node.func, ast.Attribute) \
        else getattr(node.func, "id", None)
    return name in ("CompletedProcess", "CalledProcessError")


class TestAnAnswerIsWhatGitPrinted(unittest.TestCase):
    def test_it_returns_what_cli_runner_returns(self):
        git = FakeGit(answers={("log",): "one\n"})
        done = git(["log", "--format=%s", "a..b"])
        self.assertIsInstance(done, subprocess.CompletedProcess)
        self.assertEqual((done.returncode, done.stdout), (0, "one\n"))

    def test_the_longest_matching_prefix_wins(self):
        git = FakeGit(answers={("rev-parse",): "c0ffee\n",
                               ("rev-parse", "--git-common-dir"): "/r\n"})
        self.assertEqual(git(["rev-parse", "--git-common-dir"]).stdout,
                         "/r\n")
        self.assertEqual(git(["rev-parse", "b"]).stdout, "c0ffee\n")

    def test_a_callable_answer_sees_the_whole_argv(self):
        git = FakeGit(answers={("diff",): lambda args: args[-1] + "\n"})
        self.assertEqual(git(["diff", "--name-only", "x"]).stdout, "x\n")

    def test_an_unanswered_command_succeeds_printing_nothing(self):
        """The one unknown-argv policy: git ran and printed nothing —
        what push, commit, add, diff, log and ls-tree of an absent path
        do — never an AssertionError outside cli.CLI_FAILURES."""
        for args in (["push", "origin", "b"], ["diff", "--name-only"],
                     ["ls-tree", "--name-only", "origin/main", "--", "x"],
                     ["log", "--format=%s"], ["worktree", "add", "x"]):
            self.assertEqual(FakeGit()(args).stdout, "", args)


class TestNothingFoundFailsAsGitDoes(unittest.TestCase):
    """The reads whose "nothing" real git reports as a failure: each
    unanswered one raises what real git exits with."""

    def raised(self, args, git=None):
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            (git or FakeGit())(args)
        err = caught.exception
        return err.returncode, err.cmd, err.stderr

    def test_config_get_regexp_with_no_match_exits_1(self):
        self.assertEqual(self.raised(
            ["-C", "/wt", "config", "--get-regexp", "^remote"]),
            (1, "git", ""))

    def test_grep_with_no_match_exits_1(self):
        self.assertEqual(self.raised(
            ["grep", "-h", "-o", "-E", "PRD", "origin/main", "--", "docs"]),
            (1, "git", ""))

    def test_show_of_a_missing_path_exits_128(self):
        self.assertEqual(self.raised(["show", "origin/main:docs/x.jsonl"]), (
            128, "git", "fatal: path 'docs/x.jsonl' does not exist in"
            " 'origin/main'\n"))

    def test_rev_parse_of_an_unknown_revision_exits_128(self):
        code, cmd, stderr = self.raised(["rev-parse", "conductor/b1-12"])
        self.assertEqual((code, cmd), (128, "git"))
        self.assertTrue(stderr.startswith(
            "fatal: ambiguous argument 'conductor/b1-12': unknown"
            " revision"), stderr)

    def test_an_answer_of_nothing_is_nothing_found(self):
        """Git never prints nothing and exits 0 for these reads, so an
        empty answer cannot claim it did."""
        git = FakeGit(answers={("show",): ""})
        self.assertEqual(self.raised(["show", "r:p"], git)[0], 128)

    def test_a_found_read_answers(self):
        git = FakeGit(answers={("show", "r:p"): "text\n"})
        self.assertEqual(git(["show", "r:p"]).stdout, "text\n")


class TestAFailingPrefix(unittest.TestCase):
    def test_the_default_error_is_a_failed_git(self):
        err = default_error()
        self.assertIsInstance(err, subprocess.CalledProcessError)
        self.assertEqual((err.returncode, err.cmd, err.stderr),
                         (128, "git", "fatal: rejected\n"))

    def test_only_the_failing_prefix_raises_and_names_git(self):
        git = FakeGit(failing=["-C", "/wt", "push"])
        self.assertEqual(git(["-C", "/wt", "commit"]).stdout, "")
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            git(["-C", "/wt", "push", "-u", "origin", "b"])
        self.assertEqual(cli.detail(caught.exception), "fatal: rejected")

    def test_a_suite_states_another_error_explicitly(self):
        git = FakeGit(failing=["rev-parse"], error=OSError("no git"))
        with self.assertRaises(OSError):
            git(["rev-parse", "HEAD"])

    def test_every_failure_is_one_the_callers_catch(self):
        for git, args in ((FakeGit(), ["grep", "x"]),
                          (FakeGit(), ["show", "a:b"]),
                          (FakeGit(failing=["push"]), ["push"])):
            with self.assertRaises(cli.CLI_FAILURES):
                git(args)


class TestRecordThenComputeThenRaise(unittest.TestCase):
    def test_a_failing_call_is_recorded_and_computed_before_it_raises(self):
        computed = []

        def answer(args):
            computed.append(list(args))
            return ""

        git = FakeGit(answers={("push",): answer}, failing=["push"])
        with self.assertRaises(subprocess.CalledProcessError):
            git(["push", "origin"])
        self.assertEqual((git.calls, computed),
                         ([["push", "origin"]], [["push", "origin"]]))

    def test_a_nothing_found_read_is_recorded_before_it_raises(self):
        git = FakeGit()
        with self.assertRaises(subprocess.CalledProcessError):
            git(["show", "a:b"])
        self.assertEqual(git.calls, [["show", "a:b"]])

    def test_called_filters_the_record_by_prefix(self):
        git = FakeGit()
        git(["-C", "/wt", "push"])
        git(["log"])
        self.assertEqual(git.called("-C", "/wt"), [["-C", "/wt", "push"]])


class TestItIsTheOneFakeAtTheGitPort(unittest.TestCase):
    """The claim the module opens with, pinned instead of asserted."""

    def test_the_conductor_suites_have_no_private_git_fake(self):
        self.assertEqual(
            git_port_fakes(), [],
            "a conductor suite is answering git with its own fake. Declare"
            " what git PRINTS through FakeGit(answers=…) instead; if it"
            " needs behaviour FakeGit does not have, add it there with a"
            " test above, so git's exit codes stay stated once")

    def test_the_rule_can_see_a_private_fake(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "test_conductor_x.py").write_text(
                "import subprocess\n"
                "def git(args):\n"
                "    return subprocess.CompletedProcess(args, 0, '', '')\n"
                "def builder():\n"
                "    def run(args):\n"
                "        raise subprocess.CalledProcessError(1, args)\n"
                "    return run\n"
                "class Port:\n"
                "    def __call__(self, args):\n"
                "        return subprocess.CompletedProcess(args, 0)\n",
                encoding="utf-8")
            self.assertEqual(
                sorted(git_port_fakes(Path(tmp))),
                [("test_conductor_x.py", "__call__"),
                 ("test_conductor_x.py", "git"),
                 ("test_conductor_x.py", "run")])

    def test_the_rule_does_not_fire_on_a_real_git_or_an_answer(self):
        """A port shelling out to a real git, a FakeGit answer, and a
        tool port taking more than argv are not private git fakes."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "test_conductor_y.py").write_text(
                "import subprocess\n"
                "def git(args):\n"
                "    return subprocess.run(['git', *args], check=True)\n"
                "def answer(args):\n"
                "    return args[-1]\n"
                "def tool(args, cwd=None):\n"
                "    return subprocess.CompletedProcess(args, 0)\n",
                encoding="utf-8")
            self.assertEqual(git_port_fakes(Path(tmp)), [])


if __name__ == "__main__":
    unittest.main()
