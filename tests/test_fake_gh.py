"""tests/fake_gh.py — the shared fake at cli.gh_runner's seam.

Seven suites inject it, and until this module its three declared
behaviours were asserted nowhere: a change to any of them failed
somewhere downstream, in a test whose name is about work orders or gate
digests, or it failed nowhere at all.

The last class here pins the claim the file opens with — that it is THE
one fake at the seam — mechanically, so the roll-call cannot go stale
again by being retyped.
"""
import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_gh import FakeGh, default_error  # noqa: E402

TESTS = Path(__file__).resolve().parent


def runner_modules(directory=TESTS):
    """Every module under `directory` that defines a gh-runner fake.

    The seam's port is `gh_runner(args)`, so a class with
    `__call__(self, args)` is one — derived from the syntax rather than
    from a list somebody keeps up to date, which is the whole point.

    The directory is a parameter so the rule can be exercised against a
    tree that has a private fake in it. A second copy of this walk,
    written inline in that test, would be one more of exactly the thing
    this module is about.
    """
    found = []
    for path in sorted(directory.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if (isinstance(item, ast.FunctionDef)
                        and item.name == "__call__"
                        and [a.arg for a in item.args.args] == ["self",
                                                                "args"]):
                    found.append((path.name, node.name))
    return found


class TestRecordThenComputeThenRaise(unittest.TestCase):
    """The first declared behaviour, and the one a private fake in
    test_work_queue diverged from: a failed call is visible with exactly
    the shape a successful one would have."""

    def test_a_failing_call_is_recorded_before_it_raises(self):
        gh = FakeGh(answers={("issue",): "[]"}, failing=["issue"])
        with self.assertRaises(subprocess.CalledProcessError):
            gh(["issue", "list", "--state", "open"])
        self.assertEqual(gh.calls, [["issue", "list", "--state", "open"]])

    def test_a_failing_call_computes_its_answer_before_raising(self):
        computed = []

        def answer(args):
            computed.append(list(args))
            return "[]"

        gh = FakeGh(answers={("issue",): answer}, failing=["issue"])
        with self.assertRaises(subprocess.CalledProcessError):
            gh(["issue", "list"])
        self.assertEqual(computed, [["issue", "list"]])

    def test_only_the_failing_prefix_raises(self):
        gh = FakeGh(answers={("api",): "{}"}, failing=["issue"])
        self.assertEqual(gh(["api", "user"]), "{}")
        with self.assertRaises(subprocess.CalledProcessError):
            gh(["issue", "view", "7"])


class TestOneDefaultError(unittest.TestCase):
    """The second declared behaviour: the shape a real failed gh has,
    exercising cli.detail's stderr path."""

    def test_the_default_is_a_called_process_error_carrying_stderr(self):
        err = default_error()
        self.assertIsInstance(err, subprocess.CalledProcessError)
        self.assertEqual(err.returncode, 1)
        self.assertEqual(err.cmd, "gh")
        self.assertEqual(err.stderr, "boom\n")

    def test_a_suite_that_needs_another_cli_detail_path_states_it(self):
        gh = FakeGh(failing=["api"], error=FileNotFoundError("no gh"))
        with self.assertRaises(FileNotFoundError):
            gh(["api", "user"])


class TestBodyFileIsResolvedToItsContent(unittest.TestCase):
    """The third declared behaviour: the real gh reads the temp file
    before the caller deletes it, so assertions see the body."""

    def test_the_recorded_call_carries_the_body_not_the_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = Path(tmp) / "body.md"
            body.write_text("the findings\n", encoding="utf-8")
            gh = FakeGh()
            gh(["pr", "comment", "7", "--body-file", str(body)])
            self.assertEqual(
                gh.calls,
                [["pr", "comment", "7", "--body-file", "the findings\n"]])

    def test_a_call_without_a_body_file_is_recorded_verbatim(self):
        gh = FakeGh()
        gh(["issue", "edit", "7", "--add-label", "wo:merged"])
        self.assertEqual(
            gh.calls, [["issue", "edit", "7", "--add-label", "wo:merged"]])


class TestAnswersByArgvPrefix(unittest.TestCase):
    """What a suite declares: canned stdout keyed by argv prefix."""

    def test_the_longest_matching_prefix_wins(self):
        gh = FakeGh(answers={("issue",): "short",
                             ("issue", "view"): "long"})
        self.assertEqual(gh(["issue", "view", "7"]), "long")
        self.assertEqual(gh(["issue", "list"]), "short")

    def test_an_unmatched_argv_answers_the_empty_string(self):
        self.assertEqual(FakeGh(answers={("api",): "{}"})(["issue"]), "")

    def test_a_callable_answer_sees_the_whole_argv(self):
        gh = FakeGh(answers={("api",): lambda args: json.dumps(args[-1])})
        self.assertEqual(gh(["api", "repos/o/r/issues/12"]),
                         '"repos/o/r/issues/12"')

    def test_called_filters_the_record_by_prefix(self):
        gh = FakeGh()
        gh(["issue", "edit", "7"])
        gh(["api", "user"])
        gh(["issue", "edit", "8"])
        self.assertEqual(gh.called("issue", "edit"),
                         [["issue", "edit", "7"], ["issue", "edit", "8"]])
        self.assertEqual(gh.called("pr"), [])


class TestItIsTheOneFakeAtTheSeam(unittest.TestCase):
    """The claim the module opens with, pinned instead of asserted.

    It went stale twice over: the docstring named four suites while
    seven imported it, and test_work_queue.py kept two private runners
    at the same seam — one of which recorded and raised without
    computing, diverging from the first behaviour above. A retyped
    roll-call is what went stale, so nothing here is retyped."""

    def test_the_seam_has_exactly_one_fake_and_it_is_fake_gh(self):
        self.assertEqual(
            runner_modules(), [("fake_gh.py", "FakeGh")],
            "a suite is reaching cli.gh_runner's seam with its own fake."
            " Declare what gh SAYS through FakeGh(answers=…) instead; if"
            " it genuinely needs behaviour FakeGh does not have, add it"
            " there with a test above, so every suite gets the same"
            " answer to how a fake behaves")

    def test_the_rule_can_see_a_private_fake(self):
        """The detector, run against a class shaped like the ones this
        run folded — otherwise "exactly one" says nothing about whether
        the rule works. Same function, a different directory: a second
        copy of the walk written inline here would be one more of the
        thing this module is about."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "test_private.py").write_text(
                "class Private:\n"
                "    def __call__(self, args):\n"
                "        return ''\n", encoding="utf-8")
            self.assertEqual(runner_modules(Path(tmp)),
                             [("test_private.py", "Private")])

    def test_the_rule_does_not_fire_on_a_callable_that_is_not_the_port(self):
        """`__call__(self, cmd)` is some other callable — a harness
        spawn double, a formatter. The seam's port is named `args`, and
        a rule that matched every `__call__` would report those as
        private gh fakes and teach the next reader to ignore it."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "test_other.py").write_text(
                "class Elsewhere:\n"
                "    def __call__(self, cmd):\n"
                "        return ''\n"
                "class NoArgs:\n"
                "    def __call__(self):\n"
                "        return ''\n", encoding="utf-8")
            self.assertEqual(runner_modules(Path(tmp)), [])


if __name__ == "__main__":
    unittest.main()
