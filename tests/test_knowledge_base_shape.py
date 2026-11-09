"""Pin the knowledge-base skill's text for the practices it adopted
from anthropics/knowledge-work-plugins (issue #1274, ADR-0125): the
outside-check fields, class pages, symptom-first gotcha summaries, the
optional wrong/right pair, the setup question, how ingest judges the
new candidate kinds, the credit, and harness neutrality.

Text assertions only, the tests/test_polish_shape.py pattern: they
check that a rule is stated where an agent reads it, not that an agent
follows it.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "knowledge-base"
SKILL = SKILL_DIR / "SKILL.md"
RUBRIC = SKILL_DIR / "references" / "page-rubric.md"
INGEST = SKILL_DIR / "references" / "ingest.md"
# Harness-specific paths the skill text must never name: the memory
# source is "the harness's auto-memory for this repo".
FORBIDDEN = ("~/.claude", ".claude/projects", "CLAUDE_CONFIG_DIR",
             "MEMORY.md", "/memory/")
VERBS = ("NOOP", "CONFLICT", "UPDATE", "DELETE", "ADD")


def read(path):
    return path.read_text(encoding="utf-8")


def section(text, heading):
    """From the heading line starting with `heading` to the next heading
    of the same or a higher level; empty when there is no such heading."""
    match = re.search(rf"^{re.escape(heading)}.*$", text, re.M)
    if not match:
        return ""
    level = len(heading) - len(heading.lstrip("#"))
    rest = text[match.end():]
    end = re.search(rf"^#{{1,{level}}} ", rest, re.M)
    return rest[:end.start()] if end else rest


def flat(text):
    """text with every whitespace run as one space, so a phrase matches
    across a line wrap."""
    return " ".join(text.split())


class TestRubric(unittest.TestCase):
    def setUp(self):
        self.text = read(RUBRIC)

    def test_frontmatter_names_three_optional_fields(self):
        part = flat(section(self.text, "## Frontmatter"))
        self.assertIn("these four fields, plus three optional ones", part)
        self.assertNotIn("exactly these fields", part)
        for field in ("`checked-against`", "`checked`", "`max-age`"):
            self.assertIn(field, part)
        self.assertIn("declare all three", part)

    def test_admit_proposes_a_class_page_at_three(self):
        part = flat(section(self.text, "## Admit"))
        self.assertIn("class page", part)
        self.assertIn("three or more pages or candidates", part)

    def test_gotcha_summary_leads_with_the_symptom_inside_the_cap(self):
        part = flat(section(self.text, "## Frontmatter"))
        self.assertIn("leads with the symptom", part)
        self.assertIn("200 bytes", part)

    def test_shape_allows_one_optional_wrong_right_pair(self):
        part = flat(section(self.text, "## Shape"))
        self.assertIn("`Wrong:`", part)
        self.assertIn("`Right:`", part)
        self.assertIn("optional", part)


class TestIngest(unittest.TestCase):
    def setUp(self):
        self.text = read(INGEST)
        self.harvest = flat(section(self.text, "## Harvest"))

    def test_new_kinds_go_through_the_verbs_and_a_human_promotes(self):
        for kind in ("human_turns", "memory", "setup answer"):
            self.assertIn(kind, self.harvest)
        for verb in VERBS:
            self.assertIn(verb, self.harvest)
        self.assertIn("a human promotes", self.harvest)

    def test_paired_and_unpaired_memory_verbs(self):
        self.assertIn("NOOP, CONFLICT or UPDATE", self.harvest)
        self.assertIn("ADD or NOOP", self.harvest)

    def test_a_lead_cites_the_repo_and_restates(self):
        self.assertIn("never a memory file or a transcript", self.harvest)
        self.assertIn("restated, never pasted", self.harvest)
        self.assertIn("always-loaded guardrail", self.harvest)
        self.assertIn("names its kind", self.harvest)

    def test_user_scoped_facts_are_never_proposed(self):
        self.assertIn("user-scoped or personal fact is never proposed",
                      self.harvest)

    def test_one_rule_over_many_instances(self):
        part = flat(section(self.text, "## The verbs"))
        self.assertIn("**One rule over many instances.**", part)
        self.assertIn("class page", part)


class TestSkill(unittest.TestCase):
    def setUp(self):
        self.text = read(SKILL)

    def test_setup_asks_the_newcomer_question(self):
        part = flat(section(self.text, "## 1. Setup"))
        for phrase in ("new to this repo", "one question per turn",
                       "at most three", "recommendation",
                       "five-page cap", "the user promotes",
                       "no human is present", "say that you skipped it"):
            self.assertIn(phrase, part)

    def test_the_flow_table_runs_the_question_alone(self):
        rows = [line for line in self.text.splitlines()
                if line.startswith("|") and "newcomers" in line]
        self.assertEqual(len(rows), 1)
        self.assertIn("step 1", rows[0])

    def test_harvest_names_the_new_kinds_without_a_path(self):
        part = flat(section(self.text, "## 2a."))
        self.assertIn("human_turns", part)
        self.assertIn("--memory", part)
        self.assertIn("the harness's auto-memory for this repo, where the"
                      " harness keeps one", part)

    def test_lint_step_handles_age_and_malformed_declarations(self):
        part = flat(section(self.text, "## 3."))
        for phrase in ("past its declared age", "re-run the page's check",
                       "`checked`", "missing field", "empty"
                       " 'checked-against'", "not a YYYY-MM-DD date",
                       "after today", "not a whole number of days"):
            self.assertIn(phrase, part)

    def test_over_budget_names_a_class_page(self):
        part = flat(section(self.text, "## 3."))
        line = next(ln for ln in part.split("- **") if
                    ln.startswith("over budget"))
        self.assertIn("class page", line)

    def test_the_tool_lists_the_memory_flag(self):
        self.assertIn("[--memory]", section(self.text, "## The tool"))

    def test_credits_knowledge_work_plugins(self):
        body = flat(self.text)
        for phrase in ("anthropics/knowledge-work-plugins", "Apache-2.0"):
            self.assertTrue(phrase in body, f"SKILL.md does not name"
                            f" {phrase!r}")


class TestNeutrality(unittest.TestCase):
    def test_no_harness_specific_path(self):
        for path in sorted(SKILL_DIR.rglob("*")):
            if path.is_file():
                text = read(path)
                for needle in FORBIDDEN:
                    with self.subTest(path=path.name, needle=needle):
                        self.assertNotIn(needle, text)


if __name__ == "__main__":
    unittest.main()
