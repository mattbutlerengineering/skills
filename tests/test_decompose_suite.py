"""plugin-evals/decompose/ — static wiring of the Decompose harness suite.

The run is docs/features/decompose-eval-suite/ (ADR-0114). The suite is
authored and never run here: every case below reads files and nothing
else, so no model is called and `claude plugin eval` is never invoked.
"""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from tests.test_plugin_eval_tags import case_tags

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "plugin-evals/decompose"
CASE = SUITE / "csv-export-cut"
FIXTURE = ROOT / "evals/fixtures/decompose-feature/docs/features/csv-export"
# `claude plugin eval --help` (ADR-0114): the grader types, none of which
# runs code.
GRADER_TYPES = {"regex", "tool_order", "tool_used", "file_exists", "llm",
                "baseline"}
GRADERS = {
    "skill-fired": "tool_used", "breakdown-exists": "file_exists",
    "has-rows": "regex", "covers-every-component": "llm",
    "blocked-by-names-real-items": "llm", "accept-is-checkable": "llm",
    "items-are-one-sitting": "llm",
}
PROMPT_KEYS = ("description", "tags", "max_turns", "timeout_seconds",
               "allowed_tools")
# Everything the change must leave exactly as main has it.
UNTOUCHED = ("evals", "LEDGER.md", "plugin-evals/records",
             "plugin-evals/implement", "plugin-evals/knowledge-base",
             "plugin-evals/lean", "plugin-evals/next", ".claude-plugin")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True)


def main_exists():
    return shutil.which("git") is not None and \
        git("rev-parse", "--verify", "--quiet", "main").returncode == 0


def front(path):
    """The frontmatter text of a case file."""
    return path.read_text(encoding="utf-8").split("---", 2)[1]


def field(path, name):
    match = re.search(rf"^{name}:[ \t]*(.*)$", front(path), re.MULTILINE)
    return match.group(1).strip() if match else None


def heredoc(script, target):
    """The body of the `cat > <target> <<'DELIM'` heredoc in a script."""
    match = re.search(
        rf"cat > {re.escape(target)} <<'(\w+)'\n(.*?)\n\1\n", script, re.DOTALL)
    return match.group(2) + "\n" if match else None


class TestManifestAndLayout(unittest.TestCase):
    def test_the_manifest_points_evals_at_the_plugin_evals_directory(self):
        manifest = json.loads(
            (ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["experimental"]["evals"], "plugin-evals")

    def test_the_case_directory_holds_the_four_parts(self):
        for part in ("case.yaml", "prompt.md", "scaffold.sh", "graders"):
            self.assertTrue((CASE / part).exists(), part)

    def test_case_yaml_names_the_case_and_its_scaffold(self):
        text = (CASE / "case.yaml").read_text(encoding="utf-8")
        self.assertIn('schema_version: "1.1"', text)
        self.assertIn("name: csv-export-cut", text)
        self.assertIn("scaffold_script: scaffold.sh", text)

    def test_every_decompose_case_carries_the_decompose_tag(self):
        prompts = sorted(SUITE.glob("*/prompt.md"))
        self.assertTrue(prompts)
        for prompt in prompts:
            self.assertIn("decompose", case_tags(prompt) or [], str(prompt))

    def test_the_prompt_frontmatter_carries_the_harness_keys(self):
        for key in PROMPT_KEYS:
            self.assertIsNotNone(field(CASE / "prompt.md", key), key)
        self.assertEqual(field(CASE / "prompt.md", "tags"), "[decompose]")


class TestGraders(unittest.TestCase):
    def test_the_grader_files_are_exactly_the_seven(self):
        names = sorted(p.stem for p in (CASE / "graders").glob("*.md"))
        self.assertEqual(names, sorted(GRADERS))

    def test_each_grader_has_its_type_and_none_runs_code(self):
        for name, kind in GRADERS.items():
            path = CASE / "graders" / f"{name}.md"
            self.assertEqual(field(path, "type"), kind, name)
            self.assertIn(kind, GRADER_TYPES)

    def test_has_rows_is_a_multiline_regex_over_the_produced_file(self):
        path = CASE / "graders/has-rows.md"
        text = front(path)
        self.assertIn("source: file", text)
        self.assertIn("docs/features/csv-export/breakdown.md", text)
        self.assertEqual(field(path, "flags"), "m")

    def test_each_llm_grader_names_one_defect_class(self):
        keywords = {"covers-every-component": "component",
                    "blocked-by-names-real-items": "Blocked by",
                    "accept-is-checkable": "Accept",
                    "items-are-one-sitting": "one sitting"}
        for name, word in keywords.items():
            body = (CASE / "graders" / f"{name}.md").read_text(
                encoding="utf-8").split("---", 2)[2]
            self.assertIn("PASS if", body, name)
            self.assertIn("FAIL if", body, name)
            self.assertIn(word, body, name)

    def test_nothing_in_the_case_runs_the_offline_grader(self):
        for path in sorted(p for p in CASE.rglob("*") if p.is_file()):
            self.assertNotIn("decompose_grade",
                             path.read_text(encoding="utf-8"), str(path))


class TestScaffold(unittest.TestCase):
    def setUp(self):
        self.script = (CASE / "scaffold.sh").read_text(encoding="utf-8")

    def test_the_prd_heredoc_equals_the_fixture_file(self):
        self.assertEqual(
            heredoc(self.script, "docs/features/csv-export/prd.md"),
            (FIXTURE / "prd.md").read_text(encoding="utf-8"))

    def test_the_architecture_heredoc_equals_the_fixture_file(self):
        self.assertEqual(
            heredoc(self.script, "docs/features/csv-export/architecture.md"),
            (FIXTURE / "architecture.md").read_text(encoding="utf-8"))


@unittest.skipUnless(main_exists(), "no main ref to compare against")
class TestNothingElseMoved(unittest.TestCase):
    def test_the_protected_paths_match_main(self):
        changed = git("diff", "--name-only", "main", "--", *UNTOUCHED)
        self.assertEqual(changed.stdout.split(), [])

    def test_no_untracked_file_appears_under_the_protected_paths(self):
        new = git("ls-files", "--others", "--exclude-standard", "--",
                  *UNTOUCHED)
        self.assertEqual(new.stdout.split(), [])


if __name__ == "__main__":
    unittest.main()
