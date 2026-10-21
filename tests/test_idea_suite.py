"""plugin-evals/idea/ — static wiring of the Idea harness suite.

The run is docs/features/idea-ambition-ladder/. The suite is authored and
never run here: every case below reads files and nothing else, so no model
is called and `claude plugin eval` is never invoked.
"""
import json
import re
import unittest
from pathlib import Path

import protocol
from tests.test_idea_ambition_ladder import TEMPLATE, base, git
from tests.test_plugin_eval_tags import case_tags

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "plugin-evals/idea"
CASE = SUITE / "ladder-brief"
SLUG = "slot-finder"
IDEA = f"docs/features/{SLUG}/idea.md"
# `claude plugin eval --help`: the grader types, none of which runs code.
GRADER_TYPES = {"regex", "tool_order", "tool_used", "file_exists", "llm",
                "baseline"}
GRADERS = {
    "skill-fired": "tool_used", "idea-exists": "file_exists",
    "has-ambition-rung": "regex", "has-the-demo": "regex",
    "has-riskiest-piece": "regex", "has-kill-test": "regex",
    "keeps-users-words": "regex", "moonshot-seed-appended": "regex",
    "showstopper-passes-four-tests": "llm",
    "rung-anchored-on-framing": "llm", "moonshot-not-chosen": "llm",
}
HEADING_GRADERS = {
    "has-ambition-rung": "## Ambition rung",
    "has-the-demo": "## The demo",
    "has-riskiest-piece": "## Riskiest piece + spike",
    "has-kill-test": "## Cheapest kill test",
}
PROMPT_KEYS = ("description", "tags", "max_turns", "timeout_seconds",
               "allowed_tools")
# Everything the change must leave exactly as the base has it.
UNTOUCHED = ("evals", "LEDGER.md", "plugin-evals/records",
             "plugin-evals/decompose", "plugin-evals/implement",
             "plugin-evals/knowledge-base", "plugin-evals/lean",
             "plugin-evals/next", ".claude-plugin", "factory/templates",
             "skills/launch-demo", "skills/verify")


def front(path):
    """The frontmatter text of a case file."""
    return path.read_text(encoding="utf-8").split("---", 2)[1]


def field(path, name):
    match = re.search(rf"^{name}:[ \t]*(.*)$", front(path), re.MULTILINE)
    return match.group(1).strip() if match else None


def pattern(name):
    """A regex grader's pattern, unquoted from its single-quoted YAML."""
    raw = field(CASE / "graders" / f"{name}.md", "pattern")
    return raw[1:-1].replace("''", "'")


def flags(name):
    return re.M if field(CASE / "graders" / f"{name}.md", "flags") == "m" \
        else 0


def heredoc(script, target):
    """The body of the `cat > <target> <<'DELIM'` heredoc in a script."""
    match = re.search(
        rf"cat > {re.escape(target)} <<'(\w+)'\n(.*?)\n\1\n", script,
        re.DOTALL)
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
        self.assertIn("name: ladder-brief", text)
        self.assertIn("scaffold_script: scaffold.sh", text)

    def test_every_idea_case_carries_the_idea_tag(self):
        prompts = sorted(SUITE.glob("*/prompt.md"))
        self.assertTrue(prompts)
        for prompt in prompts:
            self.assertIn("idea", case_tags(prompt) or [], str(prompt))

    def test_the_prompt_frontmatter_carries_the_harness_keys(self):
        for key in PROMPT_KEYS:
            self.assertIsNotNone(field(CASE / "prompt.md", key), key)
        self.assertEqual(field(CASE / "prompt.md", "tags"), "[idea]")
        self.assertEqual(field(CASE / "prompt.md", "allowed_tools"),
                         "[Read, Glob, Grep, Skill, Write, Edit]")


class TestGraders(unittest.TestCase):
    def test_the_grader_files_are_exactly_the_eleven(self):
        names = sorted(p.stem for p in (CASE / "graders").glob("*.md"))
        self.assertEqual(names, sorted(GRADERS))

    def test_each_grader_has_its_type_and_none_runs_code(self):
        for name, kind in GRADERS.items():
            path = CASE / "graders" / f"{name}.md"
            self.assertEqual(field(path, "type"), kind, name)
            self.assertIn(kind, GRADER_TYPES)

    def test_the_heading_regexes_match_the_template_headings(self):
        template = TEMPLATE.read_text(encoding="utf-8")
        for name, heading in HEADING_GRADERS.items():
            path = CASE / "graders" / f"{name}.md"
            self.assertIn(f"path: {IDEA}", front(path), name)
            found = re.search(pattern(name), template, flags(name))
            self.assertIsNotNone(found, name)
            self.assertEqual(found.group(0).strip(), heading)

    def test_the_heading_regexes_reject_other_headings(self):
        for name in HEADING_GRADERS:
            self.assertIsNone(
                re.search(pattern(name), "## Solution hunch\n", flags(name)))

    def test_the_moonshot_seed_regex_accepts_the_seed_form(self):
        rx, fl = pattern("moonshot-seed-appended"), flags(
            "moonshot-seed-appended")
        self.assertIn("path: docs/backlog.md",
                      front(CASE / "graders/moonshot-seed-appended.md"))
        good = f"- A bigger take (from: feature:{SLUG})\n"
        self.assertIsNotNone(re.search(rx, good, fl))
        self.assertIsNone(re.search(rx, "- A bigger take\n", fl))
        self.assertIsNone(
            re.search(rx, "- An older idea (from: session:2026-07-05)\n", fl))

    def test_keeps_users_words_greps_the_planted_phrase(self):
        script = (CASE / "scaffold.sh").read_text(encoding="utf-8")
        rx = pattern("keeps-users-words")
        self.assertIn(f"path: {IDEA}",
                      front(CASE / "graders/keeps-users-words.md"))
        self.assertIsNotNone(re.search(rx, script))
        # Not just any word of the pitch: the user's own distinctive phrase.
        self.assertIn("self-healing", rx)

    def test_each_llm_grader_names_one_check(self):
        keywords = {"showstopper-passes-four-tests": "four tests",
                    "rung-anchored-on-framing": "own words",
                    "moonshot-not-chosen": "Moonshot"}
        for name, word in keywords.items():
            body = (CASE / "graders" / f"{name}.md").read_text(
                encoding="utf-8").split("---", 2)[2]
            self.assertIn("PASS if", body, name)
            self.assertIn("FAIL if", body, name)
            self.assertIn(word, body, name)
        body = (CASE / "graders/moonshot-not-chosen.md").read_text(
            encoding="utf-8")
        self.assertIn("FAIL if the brief chooses the Moonshot", body)


class TestPromptAndScaffold(unittest.TestCase):
    def setUp(self):
        self.prompt = (CASE / "prompt.md").read_text(encoding="utf-8")
        self.script = (CASE / "scaffold.sh").read_text(encoding="utf-8")

    def test_the_prompt_fixes_the_slug_and_supplies_every_answer(self):
        self.assertIn(f"docs/features/{SLUG}/", self.prompt)
        for answer in ("Showstopper", "demo", "spike", "kill test",
                       "Do not design the\nsolution."):
            self.assertIn(answer, self.prompt)

    def test_the_scaffold_stays_in_its_directory_and_off_the_network(self):
        for token in ("cd ", "curl", "wget", "ssh", "push", "remote",
                      "http://", "https://", "rm ", "sudo", "~/", "> /",
                      "..", "$HOME"):
            self.assertNotIn(token, self.script, token)

    def test_the_scaffold_backlog_parses_under_the_protocol_grammar(self):
        backlog = heredoc(self.script, "docs/backlog.md")
        self.assertIsNotNone(backlog)
        self.assertEqual(protocol.check_backlog(backlog), [])
        self.assertEqual(len(protocol.parse_backlog(backlog)), 1)


class TestHonesty(unittest.TestCase):
    def files(self):
        return sorted(p for p in SUITE.rglob("*") if p.is_file())

    def test_the_case_never_names_the_paid_command(self):
        for path in self.files():
            self.assertNotIn("claude plugin eval",
                             path.read_text(encoding="utf-8"), str(path))

    def test_nothing_imports_a_network_or_subprocess_module(self):
        rx = r"\b(import|from)\s+(subprocess|socket|urllib|requests|http)\b"
        for path in self.files():
            self.assertIsNone(
                re.search(rx, path.read_text(encoding="utf-8")), str(path))

    def test_no_case_file_runs_a_checker(self):
        for path in self.files():
            text = path.read_text(encoding="utf-8")
            for checker in ("lint.py", "gates.py", "run_tests.py"):
                self.assertNotIn(checker, text, str(path))


@unittest.skipUnless(base(), "no main ref to compare against")
class TestNothingElseMoved(unittest.TestCase):
    def test_the_protected_paths_match_the_base(self):
        changed = git("diff", "--name-only", base(), "--", *UNTOUCHED)
        self.assertEqual(changed.stdout.split(), [])

    def test_no_untracked_file_appears_under_the_protected_paths(self):
        new = git("ls-files", "--others", "--exclude-standard", "--",
                  *UNTOUCHED)
        self.assertEqual(new.stdout.split(), [])


if __name__ == "__main__":
    unittest.main()
