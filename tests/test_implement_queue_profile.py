"""implement-queue's profile check (#1697).

Phase 0 tells a consumer which hooks its queue profile lacks, and what
each absence costs, from references/profile-migration.md. That file is a
second list of the skill's keys and hooks, so it can silently fall behind
the one place a hook is added (the skill's tables): a new hook with no
row would be exactly the stale-profile case the check exists to report.
These tests hold the two lists equal, by name and order, against the real
files.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "implement-queue" / "SKILL.md"
MIGRATION = (ROOT / "skills" / "implement-queue" / "references"
             / "profile-migration.md")

ROW = re.compile(r"^\|\s*`([a-z][a-z-_]*)`\s*\|", re.M)


def names(text, start, end):
    """Backticked first-column names of the table rows between two
    markers."""
    body = text.split(start, 1)[1].split(end, 1)[0]
    return ROW.findall(body)


class TestMigrationNamesEveryRow(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text(encoding="utf-8")
        self.migration = MIGRATION.read_text(encoding="utf-8")

    def test_every_frontmatter_key_has_a_row_in_the_skills_order(self):
        skill_keys = names(self.skill, "Frontmatter keys (all optional):",
                           "Hooks (each")
        self.assertTrue(skill_keys)
        self.assertEqual(
            names(self.migration, "## Frontmatter keys", "## Hooks"),
            skill_keys)

    def test_every_hook_has_a_row_in_the_skills_order(self):
        skill_hooks = names(self.skill, "Hooks (each", "**Cloud sessions.**")
        self.assertIn("verdict", skill_hooks)
        self.assertEqual(
            names(self.migration, "## Hooks", "## What the check reports"),
            skill_hooks)


if __name__ == "__main__":
    unittest.main()
