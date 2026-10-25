"""Skill prose that two skills share has one owner file.

Each passage below was once copied into two skills and kept in step only
by memory (docs/fixes/one-owner-for-copied-skill-text). The owner holds
the text; every consumer cites the owner's path and keeps only what
differs for it. A copy pasted back passes any `assertIn` on either file,
so these tests COUNT occurrences across the owner and its consumers:
exactly one, and that one in the owner.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (passage, owner, {consumer: path it must cite}, distinctive sentences)
SHARED = [
    ("recon",
     "skills/audit/references/recon.md",
     {"skills/audit/SKILL.md": "references/recon.md",
      "skills/automate/SKILL.md": "../audit/references/recon.md"},
     ["dropping every entry that carries a `pull_request` key",
      "is a duplicate of work in flight",
      "gh issue list --state open --limit 50"]),
    ("routing ladder",
     "skills/audit/references/routing.md",
     {"skills/audit/SKILL.md": "references/routing.md",
      "skills/automate/SKILL.md": "../audit/references/routing.md"},
     ["the default for anything worth remembering and not worth a run "
      "today",
      "the dedupe happens before the write, not after"]),
    ("dark diagram palette",
     "skills/animated-diagram/references/design-system.md",
     {"skills/interactive-architecture-diagram/references/design-system.md":
      "../../animated-diagram/references/design-system.md"},
     ["| storage | cache / object / block store | `#39c5cf` | "
      "`rgba(57,197,207,0.10)` |",
      "| node surface (mask) | `#161b22` |",
      "the fill is a hint"]),
]

DARK_DESIGN_SYSTEMS = [
    "skills/animated-diagram/references/design-system.md",
    "skills/interactive-architecture-diagram/references/design-system.md",
]


def normalized(rel):
    """Lower-cased, whitespace-collapsed text, so a sentence hard-wrapped
    at a different column, or capitalised at a sentence start, still
    counts as the same sentence. A missing file reads as empty, so the
    test reports the missing owner as a count rather than erroring."""
    path = ROOT / rel
    if not path.is_file():
        return ""
    return " ".join(path.read_text(encoding="utf-8").split()).lower()


class SharedPassageHasOneOwner(unittest.TestCase):

    def test_each_sentence_occurs_once_and_in_its_owner(self):
        for passage, owner, consumers, sentences in SHARED:
            files = [owner, *consumers]
            for sentence in sentences:
                needle = " ".join(sentence.split()).lower()
                counts = {rel: normalized(rel).count(needle)
                          for rel in files}
                with self.subTest(passage=passage, sentence=sentence):
                    self.assertEqual(
                        (sum(counts.values()), counts[owner]), (1, 1),
                        f"{passage}: {sentence!r} counted {counts}")

    def test_each_consumer_cites_its_owner(self):
        for passage, _owner, consumers, _sentences in SHARED:
            for consumer, cited in consumers.items():
                with self.subTest(passage=passage, consumer=consumer):
                    self.assertTrue(cited.lower() in normalized(consumer),
                                    f"{consumer} never cites {cited}")

    def test_each_cited_owner_ships(self):
        """A citation to a file that is not there is the drift this
        replaces, moved one step along."""
        for passage, owner, _consumers, _sentences in SHARED:
            with self.subTest(passage=passage):
                self.assertTrue((ROOT / owner).is_file(), owner)

    def test_no_keep_in_step_instruction_survives(self):
        """With one owner there is no second copy to match."""
        for rel in DARK_DESIGN_SYSTEMS:
            with self.subTest(file=rel):
                self.assertFalse("match it in the other" in normalized(rel),
                                 f"{rel} still says to match the copy")


class WorkQueuePromptListIsNumberedInOrder(unittest.TestCase):

    def test_step_four_items_number_one_to_n(self):
        text = (ROOT / "skills/work-queue/SKILL.md").read_text(
            encoding="utf-8")
        section = text.split("### 4.", 1)[1].split("### 5.", 1)[0]
        numbers = [int(n) for n in
                   re.findall(r"^(\d+)\. ", section, flags=re.MULTILINE)]
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))


if __name__ == "__main__":
    unittest.main()
