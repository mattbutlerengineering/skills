"""fast_path.py — ADR-0096's fast-path classifier (faster-sdlc #909).

Every case drives main() through the fake git port (tests/fake_git.py),
asserting the exact strings the queue profile's `fast-path` hook reads:
`fast-path: low-risk` (exit 0), `fast-path: review (<path>)` (exit 1),
and a `fast-path:` problem string with exit 2 when git itself fails,
which is ADR-0088's fail-closed case.
"""
import sys
import unittest
from pathlib import Path

import fast_path

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling helper import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from fake_git import FakeGit  # noqa: E402

DIFF = ("diff", "--name-only", "origin/main...HEAD")


def run(paths, **kwargs):
    """(exit code, stdout, the fake) for a diff naming `paths`."""
    git = FakeGit({DIFF: "".join(f"{p}\n" for p in paths)}, **kwargs)
    code, out = cli_contract.capture(fast_path.main,
                                     ["origin/main", "HEAD"], git=git)
    return code, out, git


class TestClassification(unittest.TestCase):
    def test_docs_only_outside_the_gate_paths_is_low_risk(self):
        code, out, git = run(["docs/kb/main-unprotected.md",
                              "docs/factory/merge-train-routine.md",
                              "docs/research/notes.md"])
        self.assertEqual((code, out), (0, "fast-path: low-risk\n"))
        self.assertEqual(git.calls, [list(DIFF)])

    def test_the_first_path_outside_docs_is_named(self):
        code, out, _ = run(["docs/kb/a.md", "run_tests.py", "lint.py"])
        self.assertEqual((code, out), (1, "fast-path: review (run_tests.py)\n"))

    def test_every_gate_path_under_docs_is_review(self):
        for path in ("docs/adr/x.md", "docs/adr/README.md",
                     "docs/design/home.md", "docs/features/a/prd.md",
                     "docs/features/a/architecture.md", "docs/prd.md",
                     "docs/architecture.md"):
            with self.subTest(path=path):
                code, out, _ = run(["docs/kb/a.md", path])
                self.assertEqual((code, out),
                                 (1, f"fast-path: review ({path})\n"))

    def test_the_gate_paths_this_repo_adds_are_review(self):
        for path in ("factory/templates/Makefile",
                     ".github/workflows/validator.yml",
                     ".claude-plugin/plugin.json"):
            with self.subTest(path=path):
                code, out, _ = run([path])
                self.assertEqual((code, out),
                                 (1, f"fast-path: review ({path})\n"))

    def test_a_docs_prefix_is_a_directory_not_a_substring(self):
        code, out, _ = run(["docs-site/index.md"])
        self.assertEqual((code, out),
                         (1, "fast-path: review (docs-site/index.md)\n"))

    def test_an_empty_diff_is_review(self):
        code, out, _ = run([])
        self.assertEqual((code, out), (1, "fast-path: review (empty diff)\n"))


class TestFailClosed(unittest.TestCase):
    def test_a_failed_git_exits_2_with_a_problem_string(self):
        code, out, _ = run(["docs/kb/a.md"], failing=["diff"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "fast-path: git diff --name-only"
                              " origin/main...HEAD failed: fatal: rejected\n")

    def test_a_ref_that_does_not_resolve_is_the_same_case(self):
        git = FakeGit(failing=["diff"], error=fast_path.subprocess
                      .CalledProcessError(
                          128, "git", stderr="fatal: bad revision"
                                             " 'origin/main...nope'\n"))
        code, out = cli_contract.capture(fast_path.main,
                                         ["origin/main", "nope"], git=git)
        self.assertEqual(code, 2)
        self.assertEqual(out, "fast-path: git diff --name-only"
                              " origin/main...nope failed: fatal: bad"
                              " revision 'origin/main...nope'\n")

    def test_a_missing_git_exits_2_with_a_problem_string(self):
        git = FakeGit(failing=["diff"], error=FileNotFoundError("git"))
        code, out = cli_contract.capture(fast_path.main,
                                         ["origin/main", "HEAD"], git=git)
        self.assertEqual(code, 2)
        self.assertTrue(out.startswith("fast-path: git diff --name-only"
                                       " origin/main...HEAD failed: "), out)


class TestMain(cli_contract.CliContract, unittest.TestCase):
    usage_fragment = "python3 fast_path.py <base> <head>"
    bad_argv = ("origin/main",)

    def run_cli(self, argv):
        return cli_contract.capture(fast_path.main, argv, git=FakeGit())

    def test_three_refs_is_usage_too(self):
        code, out = self.run_cli(["a", "b", "c"])
        self.assertEqual(code, 2)
        self.assertIn(self.usage_fragment, out)


if __name__ == "__main__":
    unittest.main()
