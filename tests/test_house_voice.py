"""skills/house-voice/SKILL.md — the house-voice utility skill.

The run is docs/features/house-voice/ (ADR-0119). These tests read the
skill file only: its frontmatter, the rules block between its two markers,
the conflict table against the research note's, the exemptions and the
opt-in. Offline, exact strings, no model.
"""
import re
import unittest
from pathlib import Path

import protocol
import voice_grade

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills/house-voice"
SKILL = SKILL_DIR / "SKILL.md"
RESEARCH = "docs/research/house-voice-sources-2026-10-25.md"
START = "<!-- house-voice:rules:start -->"
END = "<!-- house-voice:rules:end -->"
# architecture.md's Data model, in its order.
RULES = (
    "answer-first", "no-ceremony", "short-sentences", "plain-words",
    "no-tells", "exact-meaning", "payload-verbatim", "real-counts",
    "closing-disclosure", "full-length-when",
)
EXEMPTIONS = ("persisted-artifacts", "interviews", "interface-strings",
              "prescribed-forms", "user-instructions")
TABLE_ROW = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|(.*)\|\s*$")
LINK = re.compile(r"\]\(([^)\s]+)\)")
WORD_LIMIT = 1500


def skill_text():
    return SKILL.read_text(encoding="utf-8")


def section(text, heading):
    """The body under `## <heading>` up to the next `## ` heading."""
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)",
                      text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def table_rows(text):
    """{name: [cells after the name]} for every `| `name` | ... |` row."""
    rows = {}
    for line in text.splitlines():
        match = TABLE_ROW.match(line)
        if match:
            rows[match.group(1)] = [c.strip()
                                    for c in match.group(2).split("|")]
    return rows


def rules_block(text):
    """The text strictly between the two markers."""
    return text.split(START, 1)[1].split(END, 1)[0]


class TestFrontmatter(unittest.TestCase):
    def setUp(self):
        self.fields = protocol.read_frontmatter(SKILL)

    def test_the_name_is_the_slug(self):
        self.assertEqual(self.fields["name"], "house-voice")

    def test_the_description_triggers_on_the_agents_own_replies(self):
        description = self.fields["description"]
        for word in ("replies", "long", "hedged", "padded", "voice"):
            self.assertIn(word, description, word)

    def test_the_description_excludes_interface_strings_and_code(self):
        description = self.fields["description"]
        self.assertRegex(description,
                         r"does not cover interface strings")
        self.assertRegex(description, r"does not shorten code")


class TestRulesBlock(unittest.TestCase):
    def setUp(self):
        self.text = skill_text()

    def test_one_start_marker_and_one_end_marker_in_order(self):
        self.assertEqual(self.text.count(START), 1)
        self.assertEqual(self.text.count(END), 1)
        self.assertLess(self.text.index(START), self.text.index(END))

    def test_a_bold_named_rule_for_each_of_the_ten_names_in_order(self):
        block = rules_block(self.text)
        found = re.findall(r"^- \*\*([a-z-]+)\*\*", block, re.MULTILINE)
        self.assertEqual(tuple(found), RULES)

    def test_full_length_when_lists_its_six_cases(self):
        block = rules_block(self.text)
        tail = block.split("**full-length-when**", 1)[1]
        self.assertEqual(len(re.findall(r"^  - \S", tail, re.MULTILINE)), 6)


class TestConflicts(unittest.TestCase):
    def test_the_names_equal_the_research_notes_and_each_has_a_winner(self):
        note = (ROOT / RESEARCH).read_text(encoding="utf-8")
        expected = set(table_rows(section(note, "Conflicts and the"
                                          " precedence the skill uses")))
        self.assertEqual(len(expected), 7)
        rows = table_rows(section(skill_text(), "Conflicts"))
        self.assertEqual(set(rows), expected)
        for name, cells in rows.items():
            self.assertTrue(cells and cells[0], name)


class TestExemptions(unittest.TestCase):
    def setUp(self):
        self.body = section(skill_text(), "Exemptions")

    def test_each_exemption_is_named(self):
        for name in EXEMPTIONS:
            self.assertIn(f"`{name}`", self.body, name)

    def test_the_general_precedence_ladder_is_stated(self):
        self.assertIn("highest first", self.body)


class TestMakeItStick(unittest.TestCase):
    def setUp(self):
        self.body = section(skill_text(), "Make it stick")

    def test_the_one_time_opt_in_and_its_source(self):
        for needle in ("/output-style house-voice", "outputStyle",
                       "ADR-0119"):
            self.assertIn(needle, self.body, needle)

    def test_it_says_what_holds_without_the_opt_in(self):
        self.assertIn("Without", self.body)


class TestTheFile(unittest.TestCase):
    def setUp(self):
        self.text = skill_text()

    def test_under_the_word_limit(self):
        self.assertLess(len(self.text.split()), WORD_LIMIT)

    def test_cites_the_research_note_in_plain_text(self):
        self.assertIn(RESEARCH, self.text)
        self.assertNotIn(f"]({RESEARCH}", self.text)

    def test_no_link_leaves_the_skill_directory(self):
        for target in LINK.findall(self.text):
            resolved = (SKILL_DIR / target).resolve()
            self.assertTrue(resolved.is_relative_to(SKILL_DIR.resolve()),
                            target)

    def test_the_skill_follows_the_voice_it_defines(self):
        self.assertEqual(voice_grade.slop(self.text), [])


if __name__ == "__main__":
    unittest.main()
