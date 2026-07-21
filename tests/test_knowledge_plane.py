"""knowledge_plane seam tests (ADR-0037): the typed-ID token grammar,
the dispatch-plane row grammar, the run walk, and repo_root — asserted
at the seam's own interface instead of once per caller suite.
"""
import tempfile
import unittest
from pathlib import Path

import knowledge_plane
from knowledge_plane import (ADR_TOKEN, CLOSES_TOKEN, PRD_TOKEN, ROW,
                             WO_TOKEN, breakdown_files, repo_root,
                             row_work_order, run_dirs)


class TestTokens(unittest.TestCase):
    def test_typed_id_tokens_match_only_the_four_digit_form(self):
        for token, text in ((WO_TOKEN, "WO-0012"), (PRD_TOKEN, "PRD-0001"),
                            (ADR_TOKEN, "ADR-0034")):
            with self.subTest(text=text):
                self.assertTrue(token.search(f"see {text} here"))
                self.assertFalse(token.search(text[:-1]))  # three digits
                self.assertFalse(token.search(f"X{text}"))  # word boundary

    def test_closes_token_captures_the_issue_number(self):
        for text in ("Closes #12", "closes: #12", "Fixes   #12",
                     "resolved #12"):
            with self.subTest(text=text):
                match = CLOSES_TOKEN.search(text)
                self.assertEqual(match.group(1), "12")
        self.assertIsNone(CLOSES_TOKEN.search("enclosed #12"))


class TestRowGrammar(unittest.TestCase):
    """One rule for 'is this a breakdown row, and whose is it' — the
    grammar validator, assembler, and orientation_pack all dispatch on."""

    def test_first_token_is_the_work_order(self):
        line = "- [ ] **WO-0002** thing (PRD-0001 §2) after WO-0001"
        self.assertEqual(row_work_order(line), "WO-0002")

    def test_checked_and_star_and_plus_bullets_are_rows(self):
        for line in ("- [x] WO-0002 done", "* [ ] WO-0002 t",
                     "+ [X] WO-0002 t", "  - [ ] WO-0002 indented"):
            with self.subTest(line=line):
                self.assertEqual(row_work_order(line), "WO-0002")

    def test_prose_and_sub_bullets_are_not_rows(self):
        for line in ("WO-0002 in prose", "  - Accept: cites WO-0002",
                     "## WO-0002 heading", "- [ballot] WO-0002"):
            with self.subTest(line=line):
                self.assertIsNone(row_work_order(line))

    def test_a_row_without_a_token_is_nobodys(self):
        self.assertIsNone(row_work_order("- [ ] anonymous work"))

    def test_bullet_needs_whitespace_before_the_box(self):
        # -[x] is not a markdown checkbox; a tab is whitespace and is.
        self.assertIsNone(row_work_order("-[x] WO-0002 t"))
        self.assertEqual(row_work_order("-\t[x] WO-0002 t"), "WO-0002")

    def test_alignment_with_the_completion_and_merged_grammars(self):
        # protocol._CHECKBOX and gates.MERGED_ROW are separate owners
        # (protocol stays factory-agnostic; MERGED_ROW wants only checked
        # rows) but must agree with ROW about what a checkbox line IS —
        # else stage completion and dispatch disagree about the same line.
        import gates
        import protocol
        agree = ("- [x] WO-0002 t", "-\t[x] WO-0002 t", "+ [x] WO-0002 t")
        disagree = ("-[x] WO-0002 t",)
        for line in agree:
            with self.subTest(line=line, expect=True):
                self.assertTrue(ROW.match(line))
                self.assertTrue(protocol._CHECKBOX.search(line))
                self.assertTrue(gates.MERGED_ROW.match(line))
        for line in disagree:
            with self.subTest(line=line, expect=False):
                self.assertFalse(ROW.match(line))
                self.assertFalse(protocol._CHECKBOX.search(line))
                self.assertFalse(gates.MERGED_ROW.match(line))


class TestRunDirs(unittest.TestCase):
    def test_docs_root_plus_feature_and_fix_dirs_in_sorted_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ("docs", "docs/features/b", "docs/features/a",
                        "docs/fixes/z"):
                (root / rel).mkdir(parents=True)
            (root / "docs/features/not-a-dir.md").write_text(
                "x", encoding="utf-8")
            self.assertEqual(
                run_dirs(root),
                [root / "docs", root / "docs/features/a",
                 root / "docs/features/b", root / "docs/fixes/z"])

    def test_a_tree_without_docs_walks_to_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run_dirs(Path(tmp)), [])


class TestRowTrackerIssue(unittest.TestCase):
    """The WO<->issue mirror grammar, one home (ADR-0039): both mirror
    directions (assembler issue#->row, validator row->issue#) read the
    row's `(tracker: #N)` through this accessor."""

    def test_a_mirrored_row_yields_its_issue_number(self):
        row = ("- [ ] **WO-0004** validator.yml — size:M"
               " (PRD-0001 §Solution) (tracker: #109)")
        self.assertEqual(knowledge_plane.row_tracker_issue(row), 109)

    def test_an_unmirrored_row_yields_none(self):
        self.assertIsNone(knowledge_plane.row_tracker_issue(
            "- [ ] WO-0008 unmirrored row (PRD-0001 §Solution)"))

    def test_a_non_row_line_yields_none_even_with_a_marker(self):
        # a Notes bullet is prose, not a row — the mirror never reads it
        self.assertIsNone(knowledge_plane.row_tracker_issue(
            "2026-07-12: a note naming WO-0005 (tracker: #110)"))


class TestBreakdownFiles(unittest.TestCase):
    def test_yields_each_runs_breakdown_with_its_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/features/a").mkdir(parents=True)
            (root / "docs/features/b").mkdir(parents=True)
            (root / "docs/breakdown.md").write_text(
                "- [ ] WO-0001 root row\n", encoding="utf-8")
            (root / "docs/features/b/breakdown.md").write_text(
                "- [x] WO-0002 done\n- [ ] WO-0003 open\n",
                encoding="utf-8")
            # features/a has no breakdown.md — walked past, not yielded
            self.assertEqual(list(breakdown_files(root)), [
                (root / "docs/breakdown.md", ["- [ ] WO-0001 root row"]),
                (root / "docs/features/b/breakdown.md",
                 ["- [x] WO-0002 done", "- [ ] WO-0003 open"]),
            ])

    def test_a_tree_without_docs_walks_to_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(list(breakdown_files(Path(tmp))), [])


class TestRepoRoot(unittest.TestCase):
    def test_resolves_to_this_git_checkout(self):
        # The seam file lives at the factory repo root here, so the
        # nearest .git ancestor is the checkout itself.
        self.assertEqual(repo_root(),
                         Path(knowledge_plane.__file__).resolve().parent)
        self.assertTrue((repo_root() / ".git").exists())


if __name__ == "__main__":
    unittest.main()
