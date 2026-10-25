"""plugin-evals/house-voice/ — static wiring of the house-voice harness suite.

The run is docs/features/house-voice/ (ADR-0119). The suite is authored and
never run here: every case below reads files and nothing else, so no model
is called and `claude plugin eval` is never invoked. The regex graders are
pinned to voice_grade.SLOP_PATTERNS, and each clarity grader's facts to the
authored before and after replies.
"""
import re
import unittest
from pathlib import Path

import voice_grade
from tests.test_plugin_eval_tags import case_tags

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "plugin-evals/house-voice"
FIXTURES = SUITE / "fixtures"
CASES = ("undo-unpushed-commit", "read-a-traceback", "pick-a-date-library")
OPENER = "Short answer, no filler."
SKILL_FIRED = r'"skill"\s*:\s*"(?:[\w-]+:)?house-voice"'
PROMPT_KEYS = ("description", "tags", "max_turns", "allowed_tools")


def text(path):
    return path.read_text(encoding="utf-8")


def front(path):
    """The frontmatter text of a case file."""
    return text(path).split("---", 2)[1]


def body(path):
    """The text after a case file's frontmatter."""
    return text(path).split("---", 2)[2]


def field(path, name):
    """A frontmatter value, with a YAML single-quoted scalar unquoted."""
    match = re.search(rf"^{name}:[ \t]*(.*)$", front(path), re.MULTILINE)
    if match is None:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def squash(value):
    """value lowercased with each whitespace run made one space, so a fact
    that wraps across a line in a fixture still counts as present."""
    return " ".join(value.split()).lower()


def facts(case):
    """The must-carry fact bullets of a case's clarity grader."""
    grader = SUITE / case / "graders/carries-the-answer.md"
    return re.findall(r"^- (.+)$", body(grader), re.MULTILINE)


class TestLayout(unittest.TestCase):
    def test_the_suite_holds_exactly_the_three_cases(self):
        held = sorted(p.parent.name for p in SUITE.glob("*/prompt.md"))
        self.assertEqual(held, sorted(CASES))

    def test_no_case_yaml_anywhere_in_the_suite(self):
        self.assertEqual(sorted(SUITE.rglob("case.yaml")), [])

    def test_every_case_is_tagged_house_voice(self):
        for case in CASES:
            self.assertEqual(case_tags(SUITE / case / "prompt.md"),
                             ["house-voice"], case)


class TestPrompts(unittest.TestCase):
    def test_the_frontmatter_carries_the_harness_keys(self):
        for case in CASES:
            prompt = SUITE / case / "prompt.md"
            for key in PROMPT_KEYS:
                self.assertTrue(field(prompt, key), f"{case}: {key}")
            self.assertEqual(field(prompt, "allowed_tools"), "[Skill]", case)
            self.assertRegex(field(prompt, "max_turns"), r"^\d+$", case)

    def test_the_body_opens_with_the_brevity_clause_then_a_question(self):
        for case in CASES:
            lines = body(SUITE / case / "prompt.md").strip().splitlines()
            self.assertEqual(lines[0], OPENER, case)
            self.assertIn("?", "\n".join(lines[1:]), case)


class TestGraders(unittest.TestCase):
    NAMES = {name for name, _, _ in voice_grade.SLOP_PATTERNS}

    def graders(self, case):
        return sorted((SUITE / case / "graders").glob("*.md"))

    def test_the_grader_set_is_skill_fired_clarity_and_one_per_pattern(self):
        expected = ({"skill-fired", "carries-the-answer"}
                    | {f"no-{name}" for name in self.NAMES})
        for case in CASES:
            self.assertEqual({p.stem for p in self.graders(case)}, expected,
                             case)

    def test_skill_fired_matches_the_skill_tool_call(self):
        for case in CASES:
            path = SUITE / case / "graders/skill-fired.md"
            self.assertEqual(field(path, "type"), "tool_used", case)
            self.assertEqual(field(path, "tool"), "Skill", case)
            self.assertEqual(field(path, "input_match"), SKILL_FIRED, case)

    def test_each_slop_grader_is_a_pinned_copy_of_its_pattern(self):
        for case in CASES:
            for name, pattern, flags in voice_grade.SLOP_PATTERNS:
                path = SUITE / case / "graders" / f"no-{name}.md"
                label = f"{case}: no-{name}"
                self.assertEqual(field(path, "type"), "regex", label)
                self.assertEqual(field(path, "pattern"), pattern, label)
                self.assertEqual(field(path, "flags"), flags, label)
                self.assertEqual(field(path, "match"), "not_contains", label)
                self.assertIn(field(path, "target"),
                              (None, "last_message"), label)

    def test_the_clarity_grader_is_an_llm_rubric_with_facts(self):
        for case in CASES:
            path = SUITE / case / "graders/carries-the-answer.md"
            self.assertEqual(field(path, "type"), "llm", case)
            self.assertIn("PASS if", body(path), case)
            self.assertIn("FAIL if", body(path), case)
            self.assertTrue(facts(case), case)

    def test_every_fact_is_in_both_the_before_and_the_after_reply(self):
        for case in CASES:
            for reply in ("before.md", "after.md"):
                held = squash(text(FIXTURES / case / reply))
                for fact in facts(case):
                    self.assertIn(squash(fact), held,
                                  f"{case}/{reply}: {fact}")


if __name__ == "__main__":
    unittest.main()
