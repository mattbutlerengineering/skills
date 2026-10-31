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


if __name__ == "__main__":
    unittest.main()
