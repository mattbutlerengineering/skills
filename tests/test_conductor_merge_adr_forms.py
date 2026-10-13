"""conductor_merge.py's renumberer over every ADR filename form (issue
#774): it reads knowledge_plane.ADR_FILE, so a colliding ADR file is
renamed whether it is `0091-slug.md`, a bare `0091.md`, or
`ADR-091-slug.md`. Same scratch-repo ports as test_conductor_merge.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_conductor_merge as merge_tests  # noqa: E402
from test_conductor_merge import TurnCase, adr_rows  # noqa: E402

# Imported by attribute: a TestCase bound here would be run twice.
MAIN = merge_tests.TestReservations.MAIN


class TestRenumberForms(TurnCase):
    def renumbered(self, name):
        self.item({f"docs/adr/{name}": "# ADR-0091 item\n"})
        self.main_moves(MAIN)
        summary, problems = self.turn(adr_rows())
        self.assertEqual((problems, summary["stall"]), ([], None))
        return sorted(p.name for p in (self.wt / "docs/adr").iterdir())

    def test_a_bare_numbered_adr_file_is_renumbered(self):
        self.assertEqual(self.renumbered("0091.md"),
                         ["0091-main.md", "0094.md", "README.md"])
        self.assertEqual((self.wt / "docs/adr/0094.md").read_text(),
                         "# ADR-0094 item\n")

    def test_a_prefixed_adr_file_keeps_its_prefix(self):
        self.assertEqual(self.renumbered("ADR-091-item.md"),
                         ["0091-main.md", "ADR-0094-item.md", "README.md"])


if __name__ == "__main__":
    unittest.main()
