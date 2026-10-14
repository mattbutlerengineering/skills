"""The breakdown row and block a work order or issue owns (issue #857):
one block rule on knowledge_plane's row records, and one work_orders
index every lookup — the assembler's issue -> row, the validator's
WO -> issue, mirror_map's issue -> WO, the conductor's order leg —
derives from, with one duplicate policy.
"""
import sys
import tempfile
import unittest
from pathlib import Path

import assembler
import validator
from knowledge_plane import breakdown_rows, mirror_map, work_orders

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixture_tree import FixtureTree  # noqa: E402

ROW_1 = "- [ ] **WO-0001** first — size:S, blocked by: — (tracker: #5)"
ROW_2 = "- [ ] **WO-0002** second — size:S, blocked by: — (tracker: #6)"


def blocks(text):
    return {row["wo"]: row["block"] for row in breakdown_rows(
        text.splitlines())}


class TestRowBlock(unittest.TestCase):
    """A row's block is the row plus the lines it owns: its indented
    sub-bullets, across blank lines (a loose list), up to the next row
    or the first unindented line — prose or a heading."""

    def test_a_tight_list_block_carries_its_sub_bullets(self):
        text = f"{ROW_1}\n  - Accept: one.\n  - Notes: two.\n{ROW_2}\n"
        self.assertEqual(blocks(text), {
            "WO-0001": f"{ROW_1}\n  - Accept: one.\n  - Notes: two.",
            "WO-0002": ROW_2})

    def test_a_loose_list_keeps_the_sub_bullet_after_a_blank_line(self):
        text = f"{ROW_1}\n\n  - Accept: cites ADR-0032.\n\n{ROW_2}\n"
        self.assertEqual(blocks(text)["WO-0001"],
                         f"{ROW_1}\n\n  - Accept: cites ADR-0032.")

    def test_unindented_prose_ends_the_block(self):
        text = f"{ROW_1}\n  - Accept: one.\nSome prose ADR-0033.\n"
        self.assertEqual(blocks(text)["WO-0001"],
                         f"{ROW_1}\n  - Accept: one.")

    def test_a_heading_ends_the_block(self):
        text = f"{ROW_1}\n\n## Milestone B\n\n  - Accept: stray.\n"
        self.assertEqual(blocks(text)["WO-0001"], ROW_1)

    def test_an_indented_row_is_a_row_not_a_sub_bullet(self):
        text = f"{ROW_1}\n  {ROW_2}\n"
        self.assertEqual(blocks(text)["WO-0001"], ROW_1)


class Tree:
    """A two-run tree: an older run in docs/ and a newer feature run."""

    def __init__(self, tmp, older, newer):
        self.tree = FixtureTree(tmp)
        self.tree.write("docs/breakdown.md", older)
        self.tree.write("docs/features/new/breakdown.md", newer)
        self.root = self.tree.root


OLDER = f"# Breakdown\n\n{ROW_1}\n"
# Issue #857's reproduction: WO-0002 copy-pasted from WO-0001's row with
# its tracker kept, in a run that reuses WO-0001.
NEWER = ("# Breakdown\n\n"
         "- [ ] **WO-0001** reused — (tracker: #9)\n"
         "- [ ] **WO-0002** copy — (tracker: #9)\n")
DUP_WO = ("docs/features/new/breakdown.md:3 WO-0001 duplicates the row"
          " at docs/breakdown.md:3")
DUP_ISSUE = ("docs/features/new/breakdown.md:4 (tracker: #9) duplicates"
             " the row at docs/features/new/breakdown.md:3")


class TestWorkOrders(unittest.TestCase):
    def test_a_clean_plane_has_one_record_per_work_order_and_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Tree(tmp, OLDER, f"# Breakdown\n\n{ROW_2}\n  - Accept.\n")
            index, problems = work_orders(tree.root)
        self.assertEqual(problems, [])
        self.assertEqual(sorted(index["wo"]), ["WO-0001", "WO-0002"])
        self.assertEqual(index["issue"][6]["wo"], "WO-0002")
        self.assertEqual(index["wo"]["WO-0002"]["block"],
                         f"{ROW_2}\n  - Accept.")
        self.assertEqual(index["wo"]["WO-0002"]["clashes"], [])

    def test_duplicates_are_problems_on_every_row_they_touch(self):
        with tempfile.TemporaryDirectory() as tmp:
            index, problems = work_orders(Tree(tmp, OLDER, NEWER).root)
        self.assertEqual(problems, [DUP_WO, DUP_ISSUE])
        self.assertEqual(index["wo"]["WO-0001"]["issue"], 5)  # first wins
        self.assertEqual(index["wo"]["WO-0001"]["clashes"], [DUP_WO])
        self.assertEqual(index["issue"][9]["wo"], "WO-0001")
        self.assertEqual(index["issue"][9]["clashes"], [DUP_WO, DUP_ISSUE])
        self.assertEqual(index["wo"]["WO-0002"]["clashes"], [DUP_ISSUE])


class TestTheLookupsAgree(unittest.TestCase):
    """The reproduction from issue #857: before, the dispatcher sent #9
    as WO-0001, mirror_map said WO-0002, and the validator answered #5."""

    def test_mirror_map_takes_the_first_row_as_every_lookup_does(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(mirror_map(Tree(tmp, OLDER, NEWER).root)[9],
                             "WO-0001")

    def test_the_assembler_refuses_to_dispatch_an_ambiguous_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                assembler.resolve_row(Tree(tmp, OLDER, NEWER).root, 9),
                (None, None, [f"asm: {DUP_WO}", f"asm: {DUP_ISSUE}"]))

    def test_the_validator_refuses_an_ambiguous_work_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Tree(tmp, OLDER, NEWER).root
            self.assertEqual(validator.tracker_issue(root, "WO-0001"),
                             (None, [f"V: {DUP_WO}"]))
            self.assertEqual(validator.tracker_issue(root, "WO-0002"),
                             (None, [f"V: {DUP_ISSUE}"]))

    def test_the_prompt_row_carries_a_loose_lists_accept_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Tree(tmp, OLDER, f"# Breakdown\n\n{ROW_2}\n\n"
                                    "  - Accept: cites ADR-0032.\n")
            wo, row, problems = assembler.resolve_row(tree.root, 6)
        self.assertEqual((wo, problems), ("WO-0002", []))
        self.assertEqual(row, f"{ROW_2}\n\n  - Accept: cites ADR-0032.")


if __name__ == "__main__":
    unittest.main()
