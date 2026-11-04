"""fast_path.py — ADR-0096's fast-path classifier (faster-sdlc #909).

Every case drives main() through the fake git port (tests/fake_git.py),
asserting the exact strings the queue profile's `fast-path` hook reads:
`fast-path: low-risk` (exit 0), `fast-path: review (<path>)` (exit 1),
and a `fast-path:` problem string with exit 2 when git itself fails,
which is ADR-0088's fail-closed case.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import cli
import fast_path

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling helper import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
import git_repo  # noqa: E402
from fake_git import FakeGit  # noqa: E402

DIFF = ("diff", "--name-only", "-z", "--no-renames", "origin/main...HEAD")


def run(paths, **kwargs):
    """(exit code, stdout, the fake) for a diff naming `paths`."""
    git = FakeGit({DIFF: "".join(f"{p}\0" for p in paths)}, **kwargs)
    code, out = cli_contract.capture(fast_path.main,
                                     ["origin/main", "HEAD"], git=git)
    return code, out, git


class TestClassification(unittest.TestCase):
    def test_docs_only_outside_the_gate_paths_is_low_risk(self):
        code, out, git = run(["docs/kb/main-unprotected.md",
                              "docs/setup.md",
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

    def test_the_instruction_docs_agents_obey_are_review(self):
        """Review finding: docs/ holds files agents are told to follow,
        so a docs-only PR changing them is not low-risk."""
        for path in ("docs/pipeline-protocol.md", "docs/standards.json",
                     "docs/factory/merge-train-routine.md",
                     "docs/factory/routine-markers.md",
                     "docs/factory/costs.jsonl"):
            with self.subTest(path=path):
                code, out, _ = run(["docs/kb/a.md", path])
                self.assertEqual((code, out),
                                 (1, f"fast-path: review ({path})\n"))

    def test_a_neighbour_of_an_instruction_doc_stays_low_risk(self):
        code, out, _ = run(["docs/pipeline-protocol-notes.md",
                            "docs/standards.json.md",
                            "docs/factory-notes.md"])
        self.assertEqual((code, out), (0, "fast-path: low-risk\n"))

    def test_an_autorun_brief_at_any_depth_is_review(self):
        """Issue #1146: a resume obeys the brief (release authorization,
        `operate:`, `stop-after:`), so editing one is not low-risk."""
        for path in ("docs/features/x/autorun-brief.md",
                     "docs/fixes/y/autorun-brief.md",
                     "autorun-brief.md"):
            with self.subTest(path=path):
                code, out, _ = run(["docs/kb/a.md", path])
                self.assertEqual((code, out),
                                 (1, f"fast-path: review ({path})\n"))

    def test_a_brief_alone_names_itself(self):
        for path in ("docs/features/x/autorun-brief.md",
                     "docs/fixes/y/autorun-brief.md"):
            with self.subTest(path=path):
                code, out, _ = run([path])
                self.assertEqual((code, out),
                                 (1, f"fast-path: review ({path})\n"))

    def test_a_neighbour_of_a_brief_stays_low_risk(self):
        code, out, _ = run(["docs/features/x/breakdown.md",
                            "docs/fixes/y/defect.md",
                            "docs/features/x/autorun-brief-notes.md",
                            "docs/features/x/my-autorun-brief.md"])
        self.assertEqual((code, out), (0, "fast-path: low-risk\n"))

    def test_a_docs_prefix_is_a_directory_not_a_substring(self):
        code, out, _ = run(["docs-site/index.md"])
        self.assertEqual((code, out),
                         (1, "fast-path: review (docs-site/index.md)\n"))

    def test_an_empty_diff_is_review(self):
        code, out, _ = run([])
        self.assertEqual((code, out), (1, "fast-path: review (empty diff)\n"))


class TestProfilePin(unittest.TestCase):
    def test_the_profile_gate_paths_equal_the_classifiers_list(self):
        """Two copies of one policy (review minor): the queue profile's
        `gate_paths` and the classifier's list may not drift."""
        profile = (Path(__file__).resolve().parent.parent
                   / ".claude" / "implement-queue.md")
        lines = profile.read_text(encoding="utf-8").splitlines()
        start = lines.index("gate_paths:") + 1
        globs = []
        for line in lines[start:]:
            if not line.startswith("  - "):
                break
            globs.append(line[4:].strip().strip('"'))
        self.assertTrue(globs)
        self.assertEqual(sorted(globs), sorted(fast_path.gate_globs()))

    def test_the_brief_glob_is_in_the_classifiers_list(self):
        self.assertIn("**/autorun-brief.md", fast_path.gate_globs())

    def test_the_skill_profile_and_routine_name_one_changed_files_source(self):
        """The skill says what the list must hold, the profile names the
        command, the routine defers to the profile's hook."""
        root = Path(__file__).resolve().parent.parent
        skill = (root / "skills" / "implement-queue" / "SKILL.md"
                 ).read_text(encoding="utf-8")
        profile = (root / ".claude" / "implement-queue.md"
                   ).read_text(encoding="utf-8")
        routine = (root / "docs" / "factory" / "merge-train-routine.md"
                   ).read_text(encoding="utf-8")
        self.assertIn("| `changed-files`", skill)
        self.assertIn("**both**", skill)
        self.assertIn("fail closed", skill)
        for text in (skill, profile):
            for token in ("pulls/<N>/files --paginate", "`filename`",
                          "`previous_filename`", "changed_files"):
                self.assertIn(token, text)
        self.assertIn("\n## changed-files\n\n"
                      "    python3 fast_path.py gate origin/main HEAD\n",
                      profile)
        self.assertIn("the profile's `changed-files`", routine)


class TestFailClosed(unittest.TestCase):
    def test_a_failed_git_exits_2_with_a_problem_string(self):
        code, out, _ = run(["docs/kb/a.md"], failing=["diff"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "fast-path: git diff --name-only -z --no-renames"
                              " origin/main...HEAD failed: fatal: rejected\n")

    def test_a_ref_that_does_not_resolve_is_the_same_case(self):
        git = FakeGit(failing=["diff"], error=fast_path.subprocess
                      .CalledProcessError(
                          128, "git", stderr="fatal: bad revision"
                                             " 'origin/main...nope'\n"))
        code, out = cli_contract.capture(fast_path.main,
                                         ["origin/main", "nope"], git=git)
        self.assertEqual(code, 2)
        self.assertEqual(out, "fast-path: git diff --name-only -z --no-renames"
                              " origin/main...nope failed: fatal: bad"
                              " revision 'origin/main...nope'\n")

    def test_a_missing_git_exits_2_with_a_problem_string(self):
        git = FakeGit(failing=["diff"], error=FileNotFoundError("git"))
        code, out = cli_contract.capture(fast_path.main,
                                         ["origin/main", "HEAD"], git=git)
        self.assertEqual(code, 2)
        self.assertTrue(out.startswith("fast-path: git diff --name-only"
                                       " -z --no-renames"
                                       " origin/main...HEAD failed: "), out)


class TestRealGit(unittest.TestCase):
    """A rename lists only its destination under git's default rename
    detection, so a gate path moved into docs/ read as docs-only. These
    build a real repo: the fake port cannot show what git itself lists."""

    def repo(self, files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        git_repo.init(root)
        self.git("-C", root, "config", "user.email", "t@example.com")
        self.git("-C", root, "config", "user.name", "t")
        for name, text in files.items():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_text(text)
        self.git("-C", root, "add", "-A")
        self.git("-C", root, "commit", "-q", "-m", "base")
        self.git("-C", root, "branch", "base")
        return root

    @staticmethod
    def git(*args):
        subprocess.run(["git", *map(str, args)], check=True,
                       capture_output=True)

    def move(self, root, src, dst):
        (root / dst).parent.mkdir(parents=True, exist_ok=True)
        self.git("-C", root, "mv", src, dst)
        self.git("-C", root, "commit", "-q", "-m", "move")

    def classify(self, root):
        run = cli.runner("git")
        return cli_contract.capture(
            fast_path.main, ["base", "HEAD"],
            git=lambda args: run(args, cwd=root))

    def test_a_gate_path_renamed_into_docs_is_review(self):
        root = self.repo({".github/workflows/validator.yml": "name: v\n" * 9,
                          "docs/kb/a.md": "a\n"})
        self.move(root, ".github/workflows/validator.yml",
                  "docs/validator.yml.txt")
        self.assertEqual(self.classify(root),
                         (1, "fast-path: review"
                             " (.github/workflows/validator.yml)\n"))

    def test_a_file_renamed_from_outside_docs_into_docs_is_review(self):
        root = self.repo({"lint.py": "print('x')\n" * 9})
        self.move(root, "lint.py", "docs/lint.txt")
        self.assertEqual(self.classify(root),
                         (1, "fast-path: review (lint.py)\n"))

    def test_a_rename_inside_docs_clear_of_gates_is_low_risk(self):
        root = self.repo({"docs/kb/a.md": "a\n" * 9})
        self.move(root, "docs/kb/a.md", "docs/kb/b.md")
        self.assertEqual(self.classify(root),
                         (0, "fast-path: low-risk\n"))

    def test_a_brief_renamed_out_of_its_run_directory_is_review(self):
        root = self.repo({"docs/features/x/autorun-brief.md": "b\n" * 9})
        self.move(root, "docs/features/x/autorun-brief.md",
                  "docs/kb/old-brief.md")
        self.assertEqual(self.classify(root),
                         (1, "fast-path: review"
                             " (docs/features/x/autorun-brief.md)\n"))

    def test_a_brief_renamed_into_a_run_directory_is_review(self):
        root = self.repo({"docs/kb/old-brief.md": "b\n" * 9})
        self.move(root, "docs/kb/old-brief.md",
                  "docs/fixes/y/autorun-brief.md")
        self.assertEqual(self.classify(root),
                         (1, "fast-path: review"
                             " (docs/fixes/y/autorun-brief.md)\n"))

    def test_a_brief_edit_in_real_git_is_review(self):
        root = self.repo({"docs/fixes/y/autorun-brief.md": "stop-after: x\n",
                          "docs/fixes/y/defect.md": "d\n"})
        (root / "docs/fixes/y/autorun-brief.md").write_text("release: yes\n")
        self.git("-C", root, "commit", "-q", "-am", "edit")
        self.assertEqual(self.classify(root),
                         (1, "fast-path: review"
                             " (docs/fixes/y/autorun-brief.md)\n"))


    def test_a_non_ascii_gate_path_is_review_with_the_real_path(self):
        """git quotes `caf\\303\\251` unless told not to; the quoted string
        matched no gate prefix, so the path read as clear."""
        root = self.repo({"docs/adr/0999-café.md": "a\n"})
        (root / "docs/adr/0999-café.md").write_text("b\n")
        self.git("-C", root, "commit", "-q", "-am", "edit")
        self.assertEqual(self.classify(root),
                         (1, "fast-path: review (docs/adr/0999-café.md)\n"))

    def test_a_quote_in_a_gate_path_is_review_with_the_real_path(self):
        root = self.repo({'docs/adr/0998-a"b.md': "a\n"})
        (root / 'docs/adr/0998-a"b.md').write_text("b\n")
        self.git("-C", root, "commit", "-q", "-am", "edit")
        self.assertEqual(self.classify(root),
                         (1, 'fast-path: review (docs/adr/0998-a"b.md)\n'))


class TestGateMode(unittest.TestCase):
    """`fast_path.py gate <base> <head>` is the merge train's `gate_paths`
    check: the same rename-safe list, any gate path refuses (exit 1),
    and a list that cannot be proven complete fails closed."""

    def gate(self, paths, **kwargs):
        git = FakeGit({DIFF: "".join(f"{p}\0" for p in paths)}, **kwargs)
        return cli_contract.capture(
            fast_path.main, ["gate", "origin/main", "HEAD"], git=git)

    def test_a_plain_edit_to_an_ungated_file_is_clear(self):
        self.assertEqual(self.gate(["lint.py", "tests/test_lint.py"]),
                         (0, "gate-paths: clear\n"))

    def test_a_gate_path_among_ungated_ones_is_human(self):
        self.assertEqual(self.gate(["lint.py", "docs/adr/0001-x.md"]),
                         (1, "gate-paths: human (docs/adr/0001-x.md)\n"))

    def test_the_same_diff_args_as_the_classifier_are_used(self):
        git = FakeGit({DIFF: "lint.py\0"})
        cli_contract.capture(fast_path.main,
                             ["gate", "origin/main", "HEAD"], git=git)
        self.assertEqual([tuple(c) for c in git.calls], [DIFF])

    def test_an_empty_list_fails_closed(self):
        self.assertEqual(self.gate([]),
                         (1, "gate-paths: human (empty diff)\n"))

    def test_a_failed_git_exits_2_with_a_problem_string(self):
        self.assertEqual(
            self.gate(["lint.py"], failing=["diff"]),
            (2, "fast-path: git diff --name-only -z --no-renames"
                " origin/main...HEAD failed: fatal: rejected\n"))

    def test_a_rename_out_of_a_gate_path_in_real_git_is_human(self):
        real = TestRealGit()
        real.addCleanup = lambda fn: self.addCleanup(fn)
        root = real.repo({".github/workflows/validator.yml": "name: v\n" * 9})
        real.move(root, ".github/workflows/validator.yml",
                  "docs/validator.yml")
        run = cli.runner("git")
        self.assertEqual(
            cli_contract.capture(fast_path.main, ["gate", "base", "HEAD"],
                                 git=lambda args: run(args, cwd=root)),
            (1, "gate-paths: human (.github/workflows/validator.yml)\n"))

    def test_an_edit_to_an_ungated_file_in_real_git_is_clear(self):
        real = TestRealGit()
        real.addCleanup = lambda fn: self.addCleanup(fn)
        root = real.repo({"lint.py": "print('x')\n"})
        (root / "lint.py").write_text("print('y')\n")
        real.git("-C", root, "commit", "-q", "-am", "edit")
        run = cli.runner("git")
        self.assertEqual(
            cli_contract.capture(fast_path.main, ["gate", "base", "HEAD"],
                                 git=lambda args: run(args, cwd=root)),
            (0, "gate-paths: clear\n"))

    def test_a_non_ascii_gate_path_in_real_git_is_human(self):
        real = TestRealGit()
        real.addCleanup = lambda fn: self.addCleanup(fn)
        root = real.repo({".github/workflows/é.yml": "name: v\n"})
        (root / ".github/workflows/é.yml").write_text("name: w\n")
        real.git("-C", root, "commit", "-q", "-am", "edit")
        run = cli.runner("git")
        self.assertEqual(
            cli_contract.capture(fast_path.main, ["gate", "base", "HEAD"],
                                 git=lambda args: run(args, cwd=root)),
            (1, "gate-paths: human (.github/workflows/é.yml)\n"))


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
