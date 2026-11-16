"""Audit defect: a repeated top-level frontmatter key must be a problem.

parse_frontmatter keeps the last duplicate, but a strict YAML loader
rejects the file (or keeps the first), so the skill the plain split read
is not the skill the loader reads."""
import tempfile
import unittest
from pathlib import Path

import protocol


def _problems(frontmatter):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = protocol.skill_path(root, "demo")
        path.parent.mkdir(parents=True)
        path.write_text(frontmatter, encoding="utf-8")
        return protocol.skill_frontmatter_problems(root, "demo")


class TestDuplicateKeys(unittest.TestCase):
    def test_repeated_description_is_a_problem(self):
        self.assertEqual(
            _problems("---\nname: demo\ndescription: a\n"
                      "description: b\n---\n"),
            ["skills/demo/SKILL.md frontmatter repeats the key "
             "'description'"])

    def test_repeated_name_is_a_problem(self):
        self.assertEqual(
            _problems("---\nname: demo\nname: demo\ndescription: a\n---\n"),
            ["skills/demo/SKILL.md frontmatter repeats the key 'name'"])

    def test_indented_and_block_lines_are_not_keys(self):
        self.assertEqual(
            _problems("---\nname: demo\ndescription: a\nmeta:\n  k: x\n"
                      "  k: y\n---\n"), [])

    def test_crlf_and_bom_repeat_still_found(self):
        self.assertEqual(
            _problems("﻿---\r\nname: demo\r\ndescription: a\r\n"
                      "description: b\r\n---\r\n"),
            ["skills/demo/SKILL.md frontmatter repeats the key "
             "'description'"])


if __name__ == "__main__":
    unittest.main()
