"""conductor_merge.py's ADR-number reservations at the merge turn: the
numbers an item reserved are confirmed against origin/main before the
gate runs, and a taken number renumbers the item's ADRs. A facet of
tests/test_conductor_merge.py (its TurnCase harness, scratch repo and
fake ports), split out so the merge-turn suites run as parallel modules
(#916).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_flow import AT  # noqa: E402
from test_conductor_merge import (BRANCH, SEED, TurnCase,  # noqa: E402
                                  feature_shipped, own, sh, train)


def adr_rows(blobs=None):
    """#12 holds ADRs 90-92; covered by its own answer, or a train."""
    reserve = {"at": AT, "kind": "reserve", "item": "#12", "what": "adr",
               "values": [90, 91, 92]}
    other = dict(reserve, item="#13", values=[93])
    cover = own("ask-2", "#12") if blobs is None else train("ask-2",
                                                            ["#12"])
    return [reserve, other] + feature_shipped(blobs or {}) + cover


class TestReservations(TurnCase):
    ITEM = {"docs/adr/0091-item.md": "# ADR-0091 item\n",
            "docs/adr/README.md": SEED["docs/adr/README.md"]
            + "- [ADR-0091](0091-item.md) item\n"}
    # Main's index row lands far enough from the item's to merge cleanly.
    MAIN = {"docs/adr/0091-main.md": "# ADR-0091 main\n",
            "docs/adr/README.md": SEED["docs/adr/README.md"].replace(
                "The index.\n", "The index.\n- [ADR-0091](0091-main.md)"
                " main\n")}

    def test_a_free_number_is_confirmed_untouched(self):
        self.item(self.ITEM)
        self.assertEqual(self.turn(adr_rows())[1], [])
        self.assertTrue((self.wt / "docs/adr/0091-item.md").is_file())
        self.assertFalse([r for r in self.rows if "renumbered_from" in r])

    def test_a_number_taken_on_main_is_renumbered_mechanically(self):
        self.item(self.ITEM)
        self.main_moves(self.MAIN)
        summary, problems = self.turn(adr_rows())
        self.assertEqual((problems, summary["stall"]), ([], None))
        self.assertEqual(sorted(p.name for p in (self.wt / "docs/adr")
                                .iterdir()),
                         ["0091-main.md", "0094-item.md", "README.md"])
        self.assertEqual((self.wt / "docs/adr/0094-item.md").read_text(),
                         "# ADR-0094 item\n")
        index = (self.wt / "docs/adr/README.md").read_text()
        self.assertIn("- [ADR-0091](0091-main.md) main\n", index)
        self.assertIn("- [ADR-0094](0094-item.md) item\n", index)
        self.assertIn({"at": "2026-10-10T12:30:00Z", "kind": "reserve",
                       "item": "#12", "what": "adr", "values": [94],
                       "renumbered_from": [91]}, self.rows)
        self.assertEqual(self.rows[-1]["to"], "merged")
        self.assertLess(self.first("git", "grep"), self.first("tool",
                                                               "check"))

    def test_a_number_that_cannot_be_renumbered_stalls(self):
        self.item(self.ITEM)
        self.main_moves(dict(self.MAIN,
                             **{"docs/adr/9999-last.md": "# last\n"}))
        summary, _ = self.turn(adr_rows())
        self.assertEqual(summary["stall"], "ADR-0091 is taken on origin/main"
                         " and cannot be renumbered: ADR-10000 would leave"
                         " the 4-digit grammar")
        self.assertFalse(self.calls("git", "push"))

    def test_a_renumbered_gate_file_no_longer_rides_a_train(self):
        self.item(self.ITEM)
        blobs = {path: sh(self.repo, "rev-parse", f"{BRANCH}:{path}").strip()
                 for path in self.ITEM}
        self.main_moves(self.MAIN)
        summary, _ = self.turn(adr_rows(blobs))
        self.assertTrue(summary["stall"].startswith(
            "merge refused: #12's gate file docs/adr/"), summary)
        self.assertFalse(self.calls("git", "push"))




if __name__ == "__main__":
    unittest.main()
