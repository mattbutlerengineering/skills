"""npx_bundle.py (the generated `npx` branch, ADR-0120) — fixture tests.

The skills CLI copies each skill folder out alone, so the branch adds a
runtime skill holding the plugin root and points every skill at it.
Pure seams (rewrite, bundled) are tested on strings; build and check on
a temp fixture tree; and the real repo is built once, so a skill that
names a root path the bundle cannot resolve fails CI here.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import npx_bundle
import protocol

sys.path.insert(0, str(Path(__file__).resolve().parent))
import git_repo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = npx_bundle.RUNTIME
SLUGS = ("lean", "architecture-diagram")


class TestRewrite(unittest.TestCase):
    def test_a_plugin_root_path_moves_to_the_runtime(self):
        self.assertEqual(
            npx_bundle.rewrite("Read `../../docs/pipeline-protocol.md`.",
                               SLUGS),
            f"Read `../{RUNTIME}/docs/pipeline-protocol.md`.")

    def test_a_tool_path_after_the_skill_directory_moves_too(self):
        self.assertEqual(
            npx_bundle.rewrite(
                "python3 <this skill's directory>/../../kb.py index", SLUGS),
            f"python3 <this skill's directory>/../{RUNTIME}/kb.py index")

    def test_a_reference_file_naming_a_sibling_skill_is_kept(self):
        text = "from `../../architecture-diagram/references/design-system.md`"
        self.assertEqual(npx_bundle.rewrite(text, SLUGS), text)

    def test_a_plain_sibling_path_is_kept(self):
        text = "Apply `../lean/references/ladder.md`."
        self.assertEqual(npx_bundle.rewrite(text, SLUGS), text)

    def test_two_levels_above_names_the_runtime_folder(self):
        self.assertEqual(
            npx_bundle.rewrite(
                "from `.claude-plugin/plugin.json` two levels above this"
                " skill's base\n   directory, and name it", SLUGS),
            f"from `.claude-plugin/plugin.json` in `../{RUNTIME}/` beside"
            " this skill's base\n   directory, and name it")

    def test_text_without_a_root_path_is_unchanged(self):
        text = "Run `python3 manage.py check` in the repo."
        self.assertEqual(npx_bundle.rewrite(text, SLUGS), text)


class TestBundled(unittest.TestCase):
    def test_the_runtime_takes_the_root_tools_and_payload_only(self):
        tracked = ["board.py", "CONTEXT.md", "LICENSE", "NOTICE",
                   "dashboard.html", ".claude-plugin/plugin.json",
                   ".claude-plugin/marketplace.json",
                   "factory/templates/Makefile", "factory/agents/a.md",
                   "licenses/x.txt", "output-styles/house-voice.md",
                   "docs/pipeline-protocol.md", "docs/standards.json",
                   "docs/adr/0001-x.md", "skills/lean/SKILL.md",
                   "tests/test_lint.py", "evals/routing.json",
                   ".github/workflows/validator.yml", "README.md"]
        self.assertEqual(npx_bundle.bundled(tracked), [
            ".claude-plugin/plugin.json", "CONTEXT.md", "LICENSE", "NOTICE",
            "board.py", "dashboard.html", "docs/pipeline-protocol.md",
            "docs/standards.json", "factory/agents/a.md",
            "factory/templates/Makefile", "licenses/x.txt",
            "output-styles/house-voice.md"])


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def skill(slug, body):
    return f"---\nname: {slug}\ndescription: d\n---\n\n{body}\n"


class FixtureTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "repo"
        self.out = Path(temp.name) / "out"
        write(self.root / ".claude-plugin" / "plugin.json",
              json.dumps({"name": "idea-to-prod", "version": "9.9.9"}))
        write(self.root / "CONTEXT.md", "terms\n")
        write(self.root / "LICENSE", "license\n")
        write(self.root / "docs" / "pipeline-protocol.md", "spec\n")
        write(self.root / "kb.py", "print('kb')\n")
        write(self.root / "skills" / "idea" / "SKILL.md",
              skill("idea", "Read `../../docs/pipeline-protocol.md`."))
        write(self.root / "skills" / "lean" / "SKILL.md",
              skill("lean", "Argue for less."))
        write(self.root / "skills" / "lean" / "references" / "ladder.md",
              "Run `<this skill's directory>/../../kb.py`.\n")

    def tracked(self):
        return sorted(path.relative_to(self.root).as_posix()
                      for path in self.root.rglob("*") if path.is_file())

    def build(self):
        return npx_bundle.build(self.root, self.out, self.tracked())


class TestBuild(FixtureTest):
    def test_a_clean_fixture_builds_with_zero_problems(self):
        self.assertEqual(self.build(), [])

    def test_skill_paths_point_at_the_runtime(self):
        self.build()
        text = (self.out / "skills" / "idea" / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertIn(f"`../{RUNTIME}/docs/pipeline-protocol.md`", text)
        self.assertNotIn("../../", text)

    def test_reference_files_are_rewritten_too(self):
        self.build()
        text = (self.out / "skills" / "lean" / "references"
                / "ladder.md").read_text(encoding="utf-8")
        self.assertIn(f"/../{RUNTIME}/kb.py", text)

    def test_every_skill_gets_the_install_note_once(self):
        self.build()
        for slug in ("idea", "lean"):
            text = (self.out / "skills" / slug / "SKILL.md").read_text(
                encoding="utf-8")
            self.assertEqual(text.count(npx_bundle.NOTE_HEADING), 1, slug)

    def test_the_runtime_holds_the_root_files_at_their_root_paths(self):
        self.build()
        runtime = self.out / "skills" / RUNTIME
        for rel in ("kb.py", "CONTEXT.md", "docs/pipeline-protocol.md",
                    ".claude-plugin/plugin.json"):
            self.assertTrue((runtime / rel).is_file(), rel)

    def test_the_runtime_skill_frontmatter_passes_the_skill_contract(self):
        self.build()
        self.assertEqual(
            protocol.skill_frontmatter_problems(self.out, RUNTIME), [])

    def test_the_runtime_names_the_plugin_version(self):
        self.build()
        text = (self.out / "skills" / RUNTIME / "SKILL.md").read_text(
            encoding="utf-8")
        self.assertIn("idea-to-prod 9.9.9", text)

    def test_the_branch_root_carries_a_readme_and_the_license(self):
        self.build()
        self.assertTrue((self.out / "README.md").is_file())
        self.assertTrue((self.out / "LICENSE").is_file())

    def test_a_non_empty_output_directory_is_refused(self):
        write(self.out / "stale.txt", "x")
        self.assertEqual(self.build(), [
            f"npx-bundle: output directory {self.out} is not empty"])

    def test_a_skill_already_named_like_the_runtime_is_refused(self):
        write(self.root / "skills" / RUNTIME / "SKILL.md",
              skill(RUNTIME, "x"))
        self.assertEqual(self.build(), [
            f"npx-bundle: skills/{RUNTIME} already exists; the runtime"
            " skill needs that name"])


class TestCheck(FixtureTest):
    def test_a_runtime_path_that_does_not_resolve_is_reported(self):
        write(self.root / "skills" / "idea" / "SKILL.md",
              skill("idea", "Read `../../docs/missing.md`."))
        self.assertEqual(self.build(), [
            f"npx-bundle: skills/idea/SKILL.md names"
            f" '../{RUNTIME}/docs/missing.md', which the runtime does"
            " not hold"])

    def test_a_path_climbing_past_the_skills_folder_is_reported(self):
        write(self.root / "skills" / "lean" / "references" / "deep.md",
              "See `../../../CONTEXT.md`.\n")
        self.assertEqual(self.build(), [
            "npx-bundle: skills/lean/references/deep.md still names"
            " '../../../CONTEXT.md', outside the installed skill folders"])

    def test_a_file_the_cli_would_drop_is_reported(self):
        write(self.root / "factory" / "metadata.json", "{}")
        self.assertEqual(self.build(), [
            f"npx-bundle: skills/{RUNTIME}/factory/metadata.json is named"
            " metadata.json, which the skills CLI never copies"])


def tracked_files(root):
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                         check=True, capture_output=True, text=True).stdout
    return [path for path in out.split("\0") if path]


class TestRealRepo(unittest.TestCase):
    """The real tree, built once: every skill's rewritten root path must
    resolve inside the runtime, and the bundled tools must run from it."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.temp.name) / "out"
        cls.problems = npx_bundle.build(ROOT, cls.out, tracked_files(ROOT))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_the_real_repo_builds_clean(self):
        self.assertEqual(self.problems, [])

    def test_every_skill_ships_and_passes_the_skill_contract(self):
        installed = sorted(path.name for path in
                           (self.out / "skills").iterdir())
        slugs = sorted(protocol.ALL_SKILLS)
        self.assertEqual(installed, sorted(slugs + [RUNTIME]))
        for slug in installed:
            with self.subTest(slug=slug):
                self.assertEqual(
                    protocol.skill_frontmatter_problems(self.out, slug), [])

    def test_the_bundled_factory_init_stamps_a_repo(self):
        runtime = self.out / "skills" / RUNTIME
        with tempfile.TemporaryDirectory() as temp:
            target = git_repo.init(Path(temp) / "product")
            run = subprocess.run(
                [sys.executable, str(runtime / "factory_init.py"), "stamp",
                 str(target)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertTrue((target / "tools" / "factory" / "gates.py")
                            .is_file())

    def test_the_bundled_conductor_reports_its_version(self):
        runtime = self.out / "skills" / RUNTIME
        run = subprocess.run(
            [sys.executable, str(runtime / "conductor.py"), "--version"],
            capture_output=True, text=True, cwd=runtime)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


class TestMain(unittest.TestCase):
    def test_no_arguments_prints_usage_and_exits_2(self):
        self.assertEqual(npx_bundle.main([]), 2)


if __name__ == "__main__":
    unittest.main()
