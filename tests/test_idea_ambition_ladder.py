"""skills/idea — the ambition ladder (issue #994).

The run is docs/features/idea-ambition-ladder/. Every case reads files
and nothing else: no model is called and `claude plugin eval` is never
invoked.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/idea/SKILL.md"
TYPED_ID = re.compile(r"\b(PRD|ADR|WO)-\d{4}\b")


def skill_text():
    return " ".join(SKILL.read_text(encoding="utf-8").split())


TESTS = ("A 30-second demo exists",
         "It removes a step instead of speeding one up",
         "It is built on something only this product has",
         "It is achievable")
PROMPTS = ("What would you show first in a demo?",
           "What does the user do today that they would never have to do"
           " again?",
           "What does the product already know that it is not using?")


class TestLadderPhrases(unittest.TestCase):
    def test_every_pinned_phrase_is_in_the_skill(self):
        text = skill_text()
        for phrase in (
                "**Ambition ladder.**", "**The ambition ladder.**",
                "Showstopper (recommended)",
                "anchored on the user's own words",
                "The pick is the user's, and it is recorded in idea.md",
                "The Moonshot is never chosen in this run and is always"
                " saved as a seed",
                *TESTS, "a spike of about two days", "re-scope it once",
                "record it as the Moonshot and make Solid the pick",
                *PROMPTS,
                "answered in writing, pass or fail with one clause of"
                " evidence",
                "For a feature run, ask the ladder as one question",
                "The ladder offers a bigger version anchored on their"
                " words; it never swaps their idea for yours."):
            self.assertIn(phrase, text)

    def test_the_rules_keep_the_existing_line(self):
        self.assertIn("don't replace their idea with yours", skill_text())

    def test_each_rung_name_appears_more_than_once(self):
        text = skill_text()
        for rung in ("Solid", "Showstopper", "Moonshot"):
            self.assertGreaterEqual(text.count(rung), 2, rung)

    def test_the_skill_shows_no_typed_id(self):
        self.assertIsNone(TYPED_ID.search(skill_text()))


class TestLadderOrder(unittest.TestCase):
    def test_the_bullet_sits_between_evidence_and_the_hunch(self):
        text = skill_text()
        self.assertLess(text.index("What evidence exists"),
                        text.index("**Ambition ladder.**"))
        self.assertLess(text.index("**Ambition ladder.**"),
                        text.index("What's the rough shape of a solution?"))

    def test_the_bullet_comes_before_the_block(self):
        text = skill_text()
        self.assertLess(text.index("**Ambition ladder.**"),
                        text.index("**The ambition ladder.**"))

    def test_the_four_tests_appear_in_order(self):
        text = skill_text()
        indexes = [text.index(t) for t in TESTS]
        self.assertEqual(indexes, sorted(indexes))

    def test_the_block_precedes_the_write_step(self):
        text = skill_text()
        self.assertLess(text.index("**The ambition ladder.**"),
                        text.index("**Write the artifact.**"))


if __name__ == "__main__":
    unittest.main()
