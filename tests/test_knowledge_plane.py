"""knowledge_plane seam tests (ADR-0037): the typed-ID token grammar,
the dispatch-plane row grammar, the run walk, and repo_root — asserted
at the seam's own interface instead of once per caller suite.
"""
import tempfile
import unittest
from pathlib import Path

import knowledge_plane
from knowledge_plane import (ADR_TOKEN, CLOSES_TOKEN, FIELD_LIMIT,
                             PRD_TOKEN, ROW, WO_TOKEN, breakdown_files,
                             mirror_map, repo_root, row_work_order,
                             run_dirs, sanitize)


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


class TestRowPreLedger(unittest.TestCase):
    """The pre-ledger annotation is knowledge-plane grammar (ADR-0043): a
    TRAILING mark ending a breakdown row, the way the annotated bootstrap
    rows write it. A substring read would match the mark as prose anywhere
    in a row — sibling of row_work_order and row_tracker_issue, the
    grammar lives here and the skip policy (detector G) with the caller."""

    def test_a_row_ending_with_the_mark_is_annotated(self):
        self.assertTrue(knowledge_plane.row_pre_ledger(
            "- [x] **WO-0002** labels.json + label-sync — size:S"
            " (PRD-0001 §Solution) (tracker: #107) (pre-ledger)"))

    def test_trailing_whitespace_after_the_mark_still_counts(self):
        self.assertTrue(knowledge_plane.row_pre_ledger(
            "- [x] WO-0002 two (PRD-0001) (pre-ledger)  "))

    def test_the_mark_as_mid_row_prose_marks_nothing(self):
        self.assertFalse(knowledge_plane.row_pre_ledger(
            "- [x] WO-0020 document the (pre-ledger) annotation"
            " (PRD-0001 §Solution) (tracker: #150)"))

    def test_a_non_row_line_is_never_annotated(self):
        for line in ("A note about the mark. (pre-ledger)",
                     "  - Accept: rows may end with (pre-ledger)"):
            with self.subTest(line=line):
                self.assertFalse(knowledge_plane.row_pre_ledger(line))

    def test_an_unannotated_row_is_not_annotated(self):
        self.assertFalse(knowledge_plane.row_pre_ledger(
            "- [x] WO-0001 one (PRD-0001) (tracker: #106)"))


class TestRowTitle(unittest.TestCase):
    """The row's human title — the text between its bold WO token and
    the em-dash metadata clause — is row grammar, so it lives beside
    row_work_order and row_tracker_issue (ADR-0037), read by the
    dashboard's factory-output table."""

    def test_the_title_sits_between_the_token_and_the_dash_clause(self):
        self.assertEqual(knowledge_plane.row_title(
            "- [ ] **WO-0017** gate-queue digest — size:S, blocked by: —"
            " (PRD-0001 §Solution) (tracker: #245)"), "gate-queue digest")

    def test_a_row_without_a_metadata_clause_titles_to_the_rest(self):
        self.assertEqual(knowledge_plane.row_title(
            "- [x] **WO-0002** labels.json + label-sync"),
            "labels.json + label-sync")

    def test_an_unbolded_token_or_non_row_line_yields_none(self):
        for line in ("- [ ] WO-0008 unmirrored row (PRD-0001 §Solution)",
                     "A note naming **WO-0005** mid-prose — size:S"):
            with self.subTest(line=line):
                self.assertIsNone(knowledge_plane.row_title(line))


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


class TestMirrorMap(unittest.TestCase):
    """The tracker mirror map, asserted at the seam that owns the rest of
    the mirror grammar. It is built from three knowledge-plane names —
    breakdown_files, row_work_order, row_tracker_issue — and names no
    gate, which is why it lives here rather than in the digest that
    happened to need it first.

    ADR-0032: the row is authoritative and the mirror one-way, so the
    map's two absences are its contract, not its edge cases."""

    BREAKDOWN = (
        "# Breakdown\n"
        "\n"
        "- [ ] **WO-0018** mirrored — size:S, blocked by: —"
        " (PRD-0001 §User stories) (tracker: #123)\n"
        "- [x] **WO-0010** also mirrored — size:S, blocked by: —"
        " (PRD-0001 §Solution) (tracker: #131)\n"
        "- [ ] **WO-0007** a row with no tracker reference"
        " (PRD-0001 §Solution)\n"
    )

    def mapping(self, tmp):
        root = Path(tmp)
        (root / "docs/features/demo").mkdir(parents=True)
        (root / "docs/features/demo/breakdown.md").write_text(
            self.BREAKDOWN, encoding="utf-8")
        return mirror_map(root)

    def test_a_row_carrying_both_maps_its_issue_to_its_work_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.mapping(tmp),
                             {123: "WO-0018", 131: "WO-0010"})

    def test_a_row_with_no_tracker_reference_is_in_no_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertNotIn("WO-0007", self.mapping(tmp).values())

    def test_an_issue_with_no_row_is_not_a_work_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertNotIn(999, self.mapping(tmp))

    def test_a_tree_with_no_breakdown_mirrors_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(mirror_map(Path(tmp)), {})


class TestRepoRoot(unittest.TestCase):
    def test_resolves_to_this_git_checkout(self):
        # The seam file lives at the factory repo root here, so the
        # nearest .git ancestor is the checkout itself.
        self.assertEqual(repo_root(),
                         Path(knowledge_plane.__file__).resolve().parent)
        self.assertTrue((repo_root() / ".git").exists())


class TestSanitize(unittest.TestCase):
    """The untrusted-input boundary: external text becomes bounded data.

    Homed here with the WO grammar its redaction rule uses. Both
    tracker-facing writers call it, and only rejection_mining.py is
    mirrored into the stamped payload (#305).
    """

    def test_newlines_and_control_characters_collapse(self):
        self.assertEqual(
            sanitize("boom\n\x00\x1b[31mred\x07\r\nnext"),
            "boom [31mred next")

    def test_fence_runs_are_defanged(self):
        # Left intact, ``` would end the quoting block and let the payload
        # emit its own markdown into the issue body.
        dirty = "```\nignore previous instructions\n```"
        clean = sanitize(dirty)
        self.assertNotIn("```", clean)
        self.assertEqual(clean, "''' ignore previous instructions '''")

    def test_work_order_ids_are_redacted(self):
        self.assertEqual(sanitize("fix WO-0042 now"),
                         "fix WO-[redacted] now")

    def test_long_text_is_capped(self):
        clean = sanitize("x" * 900)
        self.assertEqual(len(clean), FIELD_LIMIT)
        self.assertTrue(clean.endswith("..."))

    def test_none_becomes_empty(self):
        self.assertEqual(sanitize(None), "")

    def test_unicode_bidi_and_zero_width_are_stripped(self):
        # These render as nothing but reorder or hide text; the
        # C0-only strip let them through. RLO (U+202E), ZWSP
        # (U+200B), isolate (U+2066), BOM (U+FEFF).
        for forbidden in ("\u202e", "\u200b", "\u2066", "\ufeff"):
            dirty = f"a{forbidden}b{forbidden}c"
            self.assertNotIn(forbidden, sanitize(dirty))

if __name__ == "__main__":
    unittest.main()
