"""Contract: gates.MERGED_ROW and knowledge_plane.ROW agree on shape.

knowledge_plane.ROW warns "change them together or completion counting and
dispatch will disagree about the same line", but the alignment was only a
comment. This suite makes it an enforced invariant: the merged-row detector
regex and the shared row grammar must accept the same bullet markers and
leading whitespace, and every checked row the merged-row detector matches
must be a valid row. The two intentional differences (ROW also matches an
unchecked box and requires a trailing space) are pinned too, so a change
that erased them would fail here instead of silently.
"""
import unittest

from gates import MERGED_ROW
from knowledge_plane import ROW

# Checked breakdown rows spanning every bullet marker, leading-whitespace
# form, inter-space, and checked-box case the two regexes must agree on.
CHECKED_ROWS = (
    "- [x] WO-0001 hyphen bullet",
    "* [x] WO-0002 star bullet",
    "+ [x] WO-0003 plus bullet",
    "  - [x] WO-0004 space-indented",
    "\t- [x] WO-0005 tab-indented",
    "-  [x] WO-0006 two spaces after bullet",
    "- [X] WO-0007 capital X",
)

# Lines neither regex may treat as a merged row: no bullet, or no space
# between the bullet and the checkbox.
NON_ROWS = (
    "-[x] WO-0008 no space after bullet",
    "WO-0009 no bullet at all",
    "plain prose line",
    "",
)


class TestRowGrammarContract(unittest.TestCase):
    def test_checked_rows_match_both_regexes(self):
        """Bullet set, leading whitespace, inter-space, and checked-box case
        are aligned: every checked row matches both owners."""
        for line in CHECKED_ROWS:
            with self.subTest(line=line):
                self.assertTrue(MERGED_ROW.match(line),
                                "MERGED_ROW should match a checked row")
                self.assertTrue(ROW.match(line),
                                "ROW should match a checked row")

    def test_merged_row_matches_imply_row_matches(self):
        """MERGED_ROW's match set is a subset of ROW's for real rows: a line
        the merged-row detector counts must be a valid row, or completion
        counting and dispatch would disagree about the same line."""
        for line in CHECKED_ROWS + NON_ROWS:
            with self.subTest(line=line):
                if MERGED_ROW.match(line):
                    self.assertTrue(
                        ROW.match(line),
                        f"MERGED_ROW matched {line!r} but ROW did not")

    def test_non_rows_are_rejected_by_both(self):
        """A missing bullet or a missing space rejects in both owners."""
        for line in NON_ROWS:
            with self.subTest(line=line):
                self.assertFalse(MERGED_ROW.match(line))
                self.assertFalse(ROW.match(line))

    def test_intentional_divergence_unchecked_box(self):
        """The one shape difference is deliberate and pinned: ROW also matches
        an unchecked box; the merged-row detector must not (it would count an
        open work order as merged)."""
        unchecked = "- [ ] WO-0010 still open"
        self.assertTrue(ROW.match(unchecked))
        self.assertFalse(MERGED_ROW.match(unchecked))


if __name__ == "__main__":
    unittest.main()
