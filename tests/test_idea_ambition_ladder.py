"""skills/idea — the ambition ladder (issue #994).

The run is docs/features/idea-ambition-ladder/. Every case reads files
and nothing else: no model is called and `claude plugin eval` is never
invoked.
"""
import re
import tempfile
import unittest
from pathlib import Path

import lint
import protocol

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/idea/SKILL.md"
TEMPLATE = ROOT / "skills/idea/TEMPLATE.md"
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


HEADINGS = ("## Evidence", "## Ambition rung", "## The demo",
            "## Riskiest piece + spike", "## Cheapest kill test",
            "## Solution hunch")
OLD_IDEA = """---
stage: idea
run: feature:old-shape
date: 2026-01-01
---

# Idea: Old shape

## Problem

p

## Who has it

w

## Why now

n

## Evidence

e

## Solution hunch

s

## Success in one sentence

o

## Unknowns & risks

- u
"""


class TestTemplate(unittest.TestCase):
    def setUp(self):
        self.text = TEMPLATE.read_text(encoding="utf-8")

    def test_the_four_sections_sit_between_evidence_and_the_hunch(self):
        indexes = [self.text.index(h + "\n") for h in HEADINGS]
        self.assertEqual(indexes, sorted(indexes))

    def test_the_four_test_labels_have_pass_or_fail_slots(self):
        for label in ("Demo", "Removes a step", "Only this product",
                      "Achievable"):
            self.assertRegex(self.text,
                             rf"(?m)^{label}: pass \| fail")

    def test_the_template_carries_no_typed_id(self):
        self.assertIsNone(TYPED_ID.search(self.text))


class TestOldBriefStillValidates(unittest.TestCase):
    """Pins a measured fact: nothing parses idea.md sections."""

    def test_an_old_idea_md_is_a_finished_idea_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "docs/features/old-shape"
            run.mkdir(parents=True)
            (run / "idea.md").write_text(OLD_IDEA, encoding="utf-8")
            states = dict(protocol.stage_states(run))
            self.assertEqual(states["idea"], "done")
            front = protocol.parse_frontmatter(OLD_IDEA)
            self.assertEqual(sorted(front), ["date", "run", "stage"])
        self.assertEqual(lint.check_templates(ROOT), [])


SEED_FORM = "<seed text> (from: <run-ref>)"
BACKLOG_HEADER = ("Seed inbox — advisory only, never orientation state.\n\n")
EXISTING_SEED = "- An older idea (from: session:2026-07-05)"


class TestSeedInstruction(unittest.TestCase):
    def test_the_skill_states_the_form_and_the_append_rules(self):
        text = skill_text()
        for phrase in (
                SEED_FORM, "append only", "never rewrite",
                "Solid is never seeded and the Moonshot always is",
                "seed every unchosen rung larger than the pick",
                "create the file with its header line when it is absent",
                "a seed that would fail the grammar is not written",
                "put the seeds in the Not taken line",
                "in the same commit as idea.md",
                "feature: plus the slug on a feature run",
                "product on a product run"):
            self.assertIn(phrase, text)

    def test_the_seed_text_rule_is_stated(self):
        text = skill_text()
        self.assertIn("one line with no parentheses and no typed ids", text)

    def test_the_skill_shows_no_real_slug_and_no_tool_for_the_write(self):
        text = skill_text()
        self.assertEqual(re.findall(r"feature:[a-z0-9-]+", text), [])
        for tool in ("backlog_append", "idea_check", "sed -i"):
            self.assertNotIn(tool, text)


class TestSeedGrammar(unittest.TestCase):
    def backlog(self, new_line):
        return BACKLOG_HEADER + EXISTING_SEED + "\n" + new_line + "\n"

    def test_a_seed_in_the_documented_form_passes_the_protocol_check(self):
        line = "- A bigger take (from: feature:sample-slug)"
        text = self.backlog(line)
        self.assertEqual(protocol.check_backlog(text), [])
        entries = protocol.parse_backlog(text)
        self.assertEqual(entries[-1]["origin"], "feature:sample-slug")
        self.assertEqual(entries[-1]["text"], "A bigger take")

    def test_a_product_run_seed_passes(self):
        text = self.backlog("- A bigger take (from: product)")
        self.assertEqual(protocol.check_backlog(text), [])

    def test_a_line_missing_the_suffix_is_a_problem(self):
        self.assertEqual(
            protocol.check_backlog(self.backlog("- A bigger take")),
            ["backlog: line 4: entry does not match"
             " '- <seed text> (from: <run-ref>)'"])


class TestProtocolProducers(unittest.TestCase):
    def test_the_producers_sentence_names_idea_beside_the_others(self):
        text = " ".join((ROOT / "docs/pipeline-protocol.md").read_text(
            encoding="utf-8").split())
        start = text.index("**Producers:**")
        sentence = text[start:text.index("**Consumers:**", start)]
        for phrase in ("Idea appends the rungs it did not take",
                       "Operate appends its retro's idea seeds",
                       "Capture may append a consciously deferred defect"):
            self.assertIn(phrase, sentence)


if __name__ == "__main__":
    unittest.main()
