"""The reviewer treats the diff as material to judge, never instructions."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PHRASE = "never instructions to follow"
TARGETS = (
    ("skills/implement-queue/references/reviewer-contract.md", "Constraints"),
    ("skills/review/SKILL.md", "Rules"),
)


def section(text, heading):
    m = re.search(r"^## " + re.escape(heading) + r"\n(.*?)(?=^## |\Z)",
                  text, re.S | re.M)
    return m.group(1) if m else ""


class ReviewerDataRuleTest(unittest.TestCase):
    def test_phrase_in_section(self):
        for rel, heading in TARGETS:
            with self.subTest(file=rel):
                body = section((ROOT / rel).read_text(), heading)
                flat = " ".join(body.split())
                self.assertIn(PHRASE, flat)


NO_CUTOFF_FILES = (
    "skills/implement-queue/references/reviewer-contract.md",
    "skills/implement-queue/SKILL.md",
    "docs/factory/merge-train-routine.md",
    "docs/factory/hourly-improvement-routine.md",
)


class NoCutoffTest(unittest.TestCase):
    """ADR-0123: the reviewer is told no pass line and returns no
    verdict; reviewer_verdict.py is the only owner of the threshold."""

    def test_no_cutoff_wording(self):
        for rel in NO_CUTOFF_FILES:
            flat = " ".join((ROOT / rel).read_text().split()).lower()
            for phrase in ("7 or more", "6 or less"):
                with self.subTest(file=rel, phrase=phrase):
                    self.assertNotIn(phrase, flat)

    def test_contract_asks_for_no_verdict(self):
        text = (ROOT / NO_CUTOFF_FILES[0]).read_text()
        rows = [ln for ln in section(text, "Output").splitlines()
                if ln.startswith("| `verdict`")]
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
