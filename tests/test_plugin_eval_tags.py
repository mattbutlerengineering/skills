"""Every plugin-eval case is tagged with its skill directory (ADR-0093).

`claude plugin eval . --tag <skill>` selects cases by tag, so a case whose
tags omit its directory name silently drops out of its own suite. Arm tags
such as `kb-on` / `kb-off` are allowed as extras.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "plugin-evals"
TAGS_LINE = re.compile(r"^tags:\s*\[(.*)\]\s*$", re.MULTILINE)


def case_tags(prompt):
    """The tags list from a case prompt's frontmatter, or None if absent."""
    text = prompt.read_text(encoding="utf-8")
    front = text.split("---", 2)[1] if text.startswith("---") else ""
    match = TAGS_LINE.search(front)
    if match is None:
        return None
    return [tag.strip() for tag in match.group(1).split(",") if tag.strip()]


class PluginEvalTagsTest(unittest.TestCase):
    def test_suite_has_cases(self):
        self.assertTrue(sorted(SUITE.glob("*/*/prompt.md")))

    def test_every_case_is_tagged_with_its_skill_directory(self):
        problems = []
        for prompt in sorted(SUITE.glob("*/*/prompt.md")):
            skill = prompt.parent.parent.name
            tags = case_tags(prompt)
            if tags is None or skill not in tags:
                rel = prompt.relative_to(ROOT).as_posix()
                problems.append(f"{rel}: tags {tags} omit {skill!r}")
        self.assertEqual([], problems)


if __name__ == "__main__":
    unittest.main()
