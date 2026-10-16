"""conductor_merge.py's renumberer over every ADR filename form (issue
#774): it reads knowledge_plane's ADR file grammar, so a colliding ADR
file is renamed whether it is `0091-slug.md`, a bare `0091.md`, or
`ADR-091-slug.md`. A collision is an ADR file on main, never a citation
(#821). Same scratch-repo ports as test_conductor_merge.

A renumbered file keeps the width its name is written at, and each
citation of it is rewritten at the width that citation is written at
(#860): a consumer's `ADR-027-redis.md` becomes `ADR-030-redis.md` and
its `ADR-027` heading `ADR-030`, never `ADR-0030`.
"""
import sys
import tempfile
import unittest
from pathlib import Path

import conductor_merge as merge

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_conductor_merge_reservations as reservation_tests  # noqa: E402
from fake_git import FakeGit  # noqa: E402
from test_conductor_flow import AT  # noqa: E402
from test_conductor_merge import TurnCase  # noqa: E402
from test_conductor_merge_reservations import adr_rows  # noqa: E402

# Imported by attribute: a TestCase bound here would be run twice.
MAIN = reservation_tests.TestReservations.MAIN


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

    def test_a_prefixed_adr_file_keeps_its_prefix_and_width(self):
        self.assertEqual(self.renumbered("ADR-091-item.md"),
                         ["0091-main.md", "ADR-094-item.md", "README.md"])
        self.assertEqual((self.wt / "docs/adr/ADR-094-item.md").read_text(),
                         "# ADR-0094 item\n")

    def test_a_number_main_only_cites_is_not_taken(self):
        # #821: main is read as plan reads it: an ADR is taken by an ADR
        # file, not by a doc's prose citing another repo's ADR-0091.
        self.item({"docs/adr/0091-item.md": "# ADR-0091 item\n"})
        self.main_moves({"docs/notes.md": "see the plugin's ADR-0091\n"})
        self.assertEqual(self.turn(adr_rows())[1], [])
        self.assertTrue((self.wt / "docs/adr/0091-item.md").is_file())
        self.assertFalse([r for r in self.rows if "renumbered_from" in r])


# A 3-digit consumer (#860): ADR-020..026 are its own, and ADR-027 landed
# on main from another batch while #12 held 27-29 and wrote ADR-027.
CONSUMER_MAIN = [f"ADR-0{n}-decision-{n}.md" for n in range(20, 28)]
CONSUMER_INDEX = "# ADRs\n- [ADR-027](ADR-027-decision-27.md) Cache\n"
ITEM_ADR = "docs/adr/ADR-027-redis.md"


class TestConsumerWidth(unittest.TestCase):
    """confirm_reservations at the git port: FakeGit plays origin/main,
    and the item's worktree is on disk."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.wt = Path(tmp.name)
        (self.wt / "docs/adr").mkdir(parents=True)
        (self.wt / ITEM_ADR).write_text(
            "# ADR-027: Use Redis\n\nGates read it as ADR-0027.\n")
        (self.wt / "docs/adr/README.md").write_text(
            CONSUMER_INDEX + "- [ADR-027](ADR-027-redis.md) Use Redis\n")
        self.git = FakeGit({
            ("ls-tree", "--name-only", "origin/main", "--", "docs/adr/"):
                "".join(f"docs/adr/{name}\n"
                        for name in CONSUMER_MAIN + ["README.md"]),
            ("diff", "--name-only"): f"{ITEM_ADR}\ndocs/adr/README.md\n",
            ("show", "origin/main:docs/adr/README.md"): CONSUMER_INDEX})
        rows = [{"at": AT, "kind": "reserve", "item": "#12",
                 "what": "adr", "values": [27, 28, 29]}]
        self.fields = merge.confirm_reservations(rows, "#12", self.git,
                                                 self.wt, "item-branch")

    def test_the_file_keeps_its_three_digit_width(self):
        self.assertEqual(self.git.called("-C", str(self.wt), "mv"),
                         [["-C", str(self.wt), "mv", ITEM_ADR,
                           "docs/adr/ADR-030-redis.md"]])
        self.assertEqual(self.fields, [{"what": "adr", "values": [30],
                                        "renumbered_from": [27]}])

    def test_the_commit_names_the_adr_at_its_written_width(self):
        # #890: the message is one more place the width is written.
        self.assertEqual(
            self.git.called("-C", str(self.wt), "commit"),
            [["-C", str(self.wt), "commit", "-m",
              "chore(conductor): renumber ADR-027 to ADR-030"]])

    def test_citations_are_rewritten_at_the_width_they_are_written(self):
        self.assertEqual(
            (self.wt / "docs/adr/ADR-030-redis.md").read_text(),
            "# ADR-030: Use Redis\n\nGates read it as ADR-0030.\n")
        self.assertEqual(
            (self.wt / "docs/adr/README.md").read_text(),
            CONSUMER_INDEX + "- [ADR-030](ADR-030-redis.md) Use Redis\n")


if __name__ == "__main__":
    unittest.main()
