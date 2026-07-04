"""Frontmatter seam: protocol.read_frontmatter is the one parser
(ADR-0021) behind lint, orientation, and the trigger-eval runner.

Pins the documented contract (None for no block, {} for an empty block,
key: value pairs) plus the two well-formed inputs the line-splitting
parser used to get wrong: `|` literal block scalars and CRLF line endings.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from protocol import read_frontmatter  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
