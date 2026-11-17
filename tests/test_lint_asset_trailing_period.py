"""Audit defect #1859: a skill asset path ending a sentence is not
reported missing for its trailing period."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import lint  # noqa: E402


class TestTrailingPeriod(unittest.TestCase):
    def test_asset_at_sentence_end_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "idea"
            (skill / "references").mkdir(parents=True)
            (skill / "references" / "playbook.md").write_text("x\n")
            (skill / "SKILL.md").write_text(
                "---\nname: idea\n---\nRead references/playbook.md.\n")
            self.assertEqual(lint.check_skill_assets(root), [])

    def test_sibling_asset_at_sentence_end_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills" / "lean" / "references").mkdir(parents=True)
            (root / "skills" / "lean" / "references" / "l.md").write_text("x")
            idea = root / "skills" / "idea"
            idea.mkdir(parents=True)
            (idea / "SKILL.md").write_text(
                "---\nname: idea\n---\nApply ../lean/references/l.md.\n")
            self.assertEqual(lint.check_skill_assets(root), [])


if __name__ == "__main__":
    unittest.main()
