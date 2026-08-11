"""Frontmatter seam: protocol.read_frontmatter is the one parser
(ADR-0021) behind lint, orientation, and the trigger-eval runner.

Pins the documented contract (None for no block, {} for an empty block,
key: value pairs) plus the two well-formed inputs the line-splitting
parser used to get wrong: `|` literal block scalars and CRLF line endings.
Also pins the skill-file contract (ADR-0052): skill_path is the one
place the skills/<slug>/SKILL.md shape lives, and
skill_frontmatter_problems is the single frontmatter error contract
behind lint's skill checker and the trigger-eval loader — exact strings,
since lint prints them verbatim.
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from protocol import (SKILL_DESCRIPTION_LIMIT, read_frontmatter,  # noqa: E402
                      skill_frontmatter_problems, skill_path)


def write(text):
    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8", newline="")
    handle.write(text)
    handle.close()
    return Path(handle.name)


class TestExistingContract(unittest.TestCase):
    def test_simple_key_values(self):
        path = write("---\nname: idea\ndescription: d\n---\n\nbody\n")
        self.assertEqual(read_frontmatter(path),
                         {"name": "idea", "description": "d"})

    def test_no_block_returns_none(self):
        self.assertIsNone(read_frontmatter(write("body only\n")))

    def test_fieldless_block_returns_empty_dict(self):
        self.assertEqual(read_frontmatter(write("---\n\n---\n\nbody\n")), {})


class TestBlockScalars(unittest.TestCase):
    def test_literal_block_scalar_joins_indented_lines(self):
        path = write("---\n"
                     "name: idea\n"
                     "description: |\n"
                     "  first line\n"
                     "  second line\n"
                     "---\n\nbody\n")
        self.assertEqual(read_frontmatter(path)["description"],
                         "first line\nsecond line")

    def test_key_after_block_scalar_still_parses(self):
        path = write("---\n"
                     "description: |\n"
                     "  multi\n"
                     "name: idea\n"
                     "---\n\nbody\n")
        self.assertEqual(read_frontmatter(path),
                         {"description": "multi", "name": "idea"})


class TestLineEndings(unittest.TestCase):
    def test_crlf_file_parses_like_lf(self):
        path = write("---\r\nname: idea\r\ndescription: d\r\n---\r\n\r\nbody\r\n")
        self.assertEqual(read_frontmatter(path),
                         {"name": "idea", "description": "d"})


class TestSkillPath(unittest.TestCase):
    """The one place the skills/<slug>/SKILL.md shape lives (ADR-0052)."""

    def test_shape_under_a_plugin_root(self):
        self.assertEqual(skill_path(Path("/repo"), "idea"),
                         Path("/repo/skills/idea/SKILL.md"))

    def test_accepts_a_string_root(self):
        self.assertEqual(skill_path("/repo", "next"),
                         Path("/repo/skills/next/SKILL.md"))


class TestSkillFrontmatterProblems(unittest.TestCase):
    """One frontmatter error contract for lint and the trigger-eval
    loader (ADR-0052). Before it, trigger-eval skipped the Pi
    description limit lint enforces — an overlong description passed
    eval but failed lint."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="skill-fm-"))
        self.addCleanup(shutil.rmtree, self.root)

    def seed(self, slug, text):
        skill_dir = self.root / "skills" / slug
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")

    def test_conformant_skill_yields_no_problems(self):
        self.seed("idea", "---\nname: idea\ndescription: d\n---\n\nbody\n")
        self.assertEqual(skill_frontmatter_problems(self.root, "idea"), [])

    def test_missing_file(self):
        self.assertEqual(skill_frontmatter_problems(self.root, "idea"),
                         ["missing skills/idea/SKILL.md"])

    def test_no_frontmatter_block(self):
        self.seed("idea", "body only\n")
        self.assertEqual(skill_frontmatter_problems(self.root, "idea"),
                         ["skills/idea/SKILL.md has no frontmatter block"])

    def test_name_mismatch_and_missing_description_both_surface(self):
        self.seed("idea", "---\nname: notidea\n---\n\nbody\n")
        self.assertEqual(
            skill_frontmatter_problems(self.root, "idea"),
            ["skills/idea/SKILL.md frontmatter name is 'notidea', "
             "expected 'idea'",
             "skills/idea/SKILL.md frontmatter has no description"])

    def test_description_over_the_pi_limit(self):
        self.assertEqual(SKILL_DESCRIPTION_LIMIT, 1024)
        overlong = "x" * (SKILL_DESCRIPTION_LIMIT + 1)
        self.seed("idea",
                  f"---\nname: idea\ndescription: {overlong}\n---\n\nbody\n")
        self.assertEqual(
            skill_frontmatter_problems(self.root, "idea"),
            ["skills/idea/SKILL.md description exceeds Pi's "
             "1024-char limit"])


if __name__ == "__main__":
    unittest.main()
