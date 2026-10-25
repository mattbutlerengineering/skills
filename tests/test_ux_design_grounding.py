"""skills/ux-design — code facts, scenario walkthroughs, independent review
(issue #1093).

The run is docs/fixes/a-sketch-drawn-from-memory/. Every case reads files
and nothing else: no model is called. The cases show the text is present,
not that a designer follows it.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/ux-design/SKILL.md"
TEMPLATE = ROOT / "skills/ux-design/TEMPLATE.md"


def flat(path):
    return " ".join(path.read_text(encoding="utf-8").split())


def headings(path):
    return [line for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ")]


class TestCodeFacts(unittest.TestCase):
    def test_the_skill_grounds_each_existing_surface_in_code(self):
        text = flat(SKILL)
        for phrase in ("**Code facts before sketches.**",
                       "read the code that implements it today",
                       "Never sketch an existing surface from memory."):
            self.assertIn(phrase, text)

    def test_code_facts_come_before_the_sketch(self):
        text = flat(SKILL)
        self.assertLess(text.index("**Code facts before sketches.**"),
                        text.index("**Sketch.**"))

    def test_the_template_has_the_section(self):
        self.assertIn("## Code facts", headings(TEMPLATE))

    def test_a_contradicting_fact_reopens_the_flow_or_reaches_architect(self):
        self.assertIn("re-open the affected flow with the user", flat(SKILL))
        self.assertIn("Dependencies surfaced for Architect", flat(SKILL))
        self.assertIn("## Dependencies surfaced for Architect",
                      headings(TEMPLATE))


class TestScenarioWalkthroughs(unittest.TestCase):
    def test_the_skill_writes_the_hardest_scenarios_as_walkthroughs(self):
        text = flat(SKILL)
        for phrase in ("**Scenario walkthroughs first.**",
                       "the hardest scenarios in `idea.md` and `prd.md`",
                       "using only controls this doc defines",
                       "A walkthrough that cannot finish is a gap",
                       "Confirm the list with the user"):
            self.assertIn(phrase, text)

    def test_walkthroughs_come_before_the_flow_interview(self):
        text = flat(SKILL)
        self.assertLess(text.index("**Scenario walkthroughs first.**"),
                        text.index("**Interview.**"))

    def test_the_template_has_the_section(self):
        self.assertIn("## Scenario walkthroughs", headings(TEMPLATE))


class TestIndependentReview(unittest.TestCase):
    def test_the_reviewer_gets_files_not_conclusions(self):
        text = flat(SKILL)
        for phrase in ("**Independent review before hand-off.**",
                       "Give the reviewer the files, not your conclusions",
                       "Critical and High findings only",
                       "Fix or record each finding before committing",
                       "`idea.md`, `prd.md`, `ux.md`",
                       "re-walk the walkthroughs after the fixes"):
            self.assertIn(phrase, text)

    def test_the_inline_fallback_is_labelled(self):
        self.assertIn("`review: inline, not independent`", flat(SKILL))

    def test_an_unattended_fallback_reaches_the_assumptions(self):
        self.assertIn("also log it under `assumptions:`", flat(SKILL))

    def test_the_review_comes_before_the_hand_off(self):
        text = flat(SKILL)
        self.assertLess(
            text.index("**Independent review before hand-off.**"),
            text.index("**Hand off.**"))

    def test_the_template_has_the_section(self):
        self.assertIn("## Review", headings(TEMPLATE))


class TestUxPatternsSuggestion(unittest.TestCase):
    def test_an_absent_patterns_file_draws_a_suggestion_not_a_gate(self):
        text = flat(SKILL)
        for phrase in ("If it is absent, suggest running the `ux-patterns`"
                       " skill first",
                       "a suggestion, not a gate"):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
