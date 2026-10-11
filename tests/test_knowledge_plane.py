"""knowledge_plane seam tests (ADR-0037): the typed-ID token grammar,
the dispatch-plane row grammar, the run walk, and repo_root — asserted
at the seam's own interface instead of once per caller suite.
"""
import ast
import re
import tempfile
import unittest
from pathlib import Path

import knowledge_plane
from gates import (_clean_repo_fixture, _evidence_honesty_defect_fixture,
                   _link_integrity_defect_fixture, _wo_citation_defect_fixture)
from knowledge_plane import (ADR_TOKEN, CLOSES_TOKEN, FIELD_LIMIT,
                             PRD_TOKEN, ROW, WO_TOKEN, breakdown_files,
                             fence_closes, fence_open, mirror_map, parse_run, repo_root, row_done,
                             row_blockers, row_unreadable_blockers,
                             row_work_order, run_dirs, sanitize, unfenced)


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

    def test_alignment_with_the_completion_grammar(self):
        # protocol._CHECKBOX is a separate owner by design — it captures
        # the box contents and protocol.py stays factory-agnostic — but
        # must agree with ROW about what a checkbox line IS, else stage
        # completion and dispatch disagree about the same line. It is the
        # only other owner left; ADR-0058 retired the third.
        import protocol
        agree = ("- [x] WO-0002 t", "-\t[x] WO-0002 t", "+ [x] WO-0002 t")
        disagree = ("-[x] WO-0002 t",)
        for line in agree:
            with self.subTest(line=line, expect=True):
                self.assertTrue(ROW.match(line))
                self.assertTrue(protocol._CHECKBOX.search(line))
        for line in disagree:
            with self.subTest(line=line, expect=False):
                self.assertFalse(ROW.match(line))
                self.assertFalse(protocol._CHECKBOX.search(line))


class TestRowUnreadableBlockers(unittest.TestCase):
    """row_blockers reads only WO tokens, so a blocked-by clause that
    names a title or a mistyped id used to read as "no blockers", and the
    planner could dispatch the row before its dependency (beads wo-o3l).
    The seam now names what it could not read, so a caller can refuse to
    guess."""

    def line(self, clause):
        return (f"- [ ] **WO-0002** thing — size:S, blocked by: {clause}"
                " (PRD-0001 §2) (tracker: #7)")

    def test_work_order_lists_and_nothing_read_cleanly(self):
        for clause in ("WO-0001", "WO-0001, WO-0003", "WO-0001 and WO-0003",
                       "WO-0001; WO-0003", "—", "-", ""):
            with self.subTest(clause=clause):
                self.assertIsNone(row_unreadable_blockers(self.line(clause)))

    def test_a_title_is_unreadable(self):
        line = self.line("Export API")
        self.assertEqual(row_unreadable_blockers(line), "Export API")
        self.assertEqual(row_blockers(line), [])

    def test_a_mistyped_id_is_unreadable(self):
        self.assertEqual(row_unreadable_blockers(self.line("WO-001")),
                         "WO-001")

    def test_the_readable_half_of_a_mixed_clause_still_counts(self):
        line = self.line("WO-0001, Export API")
        self.assertEqual(row_unreadable_blockers(line), "Export API")
        self.assertEqual(row_blockers(line), ["WO-0001"])

    def test_no_clause_and_non_rows_are_not_its_business(self):
        self.assertIsNone(row_unreadable_blockers(
            "- [ ] **WO-0002** thing (PRD-0001 §2)"))
        self.assertIsNone(row_unreadable_blockers(
            "  - Accept: blocked by: Export API"))


class TestRowDone(unittest.TestCase):
    """The checked-row grammar at its own interface (ADR-0058). Five call
    sites ask this question — detector G, the reconcile sweep, the work
    queue, and the dashboard twice — and they must get one answer."""

    def test_checked_boxes_across_every_bullet_and_indent(self):
        for line in ("- [x] WO-0002 done", "- [X] WO-0002 done",
                     "-\t[x] WO-0002 done", "+ [x] WO-0002 done",
                     "* [x] WO-0002 done", "  - [x] WO-0002 indented"):
            with self.subTest(line=line):
                self.assertTrue(row_done(line))

    def test_unchecked_prose_and_malformed_bullets_are_not_done(self):
        for line in ("- [ ] WO-0002 open", "-[x] WO-0002 t",
                     "text - [x] WO-0002 t", "## WO-0002 heading", ""):
            with self.subTest(line=line):
                self.assertFalse(row_done(line))

    def test_a_box_with_no_space_after_it_is_not_a_row_at_all(self):
        # The whole point of the accessor family: ROW requires whitespace
        # after the closing bracket, so a line without it is not a row —
        # and row_done must say so too, or one module answers "is this a
        # row" twice and differently.
        for line in ("- [x]a WO-0002 no space after the box",
                     "- [x]**WO-0003** bold straight after the box"):
            with self.subTest(line=line):
                self.assertIsNone(row_work_order(line))
                self.assertFalse(row_done(line))

    def test_row_done_never_disagrees_with_the_row_grammar(self):
        # The property, not the cases: nothing row_done calls a checked
        # row may fail ROW.match. Shapes drawn from this class's own
        # checked/malformed fixtures plus the two above.
        for line in ("- [x] WO-0002 done", "- [X] WO-0002 done",
                     "-\t[x] WO-0002 done", "+ [x] WO-0002 done",
                     "* [x] WO-0002 done", "  - [x] WO-0002 indented",
                     "- [ ] WO-0002 open", "-[x] WO-0002 t",
                     "text - [x] WO-0002 t", "## WO-0002 heading", "",
                     "- [x]a WO-0002 no space", "- [x]**WO-0003** bold"):
            with self.subTest(line=line):
                if row_done(line):
                    self.assertIsNotNone(ROW.match(line))

    def test_the_checked_row_grammar_has_one_owner(self):
        # ADR-0058 amends ADR-0039's roster from three owners to two.
        # gates.MERGED_ROW was a fourth, added nineteen days after that
        # roster was fixed and identical to this one in pattern AND
        # flags. A re-added copy is the drift this pins.
        import gates
        self.assertFalse(
            hasattr(gates, "MERGED_ROW"),
            "gates.MERGED_ROW is back: the checked-row grammar has one"
            " owner, knowledge_plane.row_done (ADR-0058)")

    def test_the_documented_call_sites_are_the_real_ones(self):
        """row_done's docstring names its call sites, and a hand-typed
        enumeration goes stale silently: the list said five and named
        the reconcile sweep and the dashboard twice, months after
        ADR-0060 folded both into plane_drift.reconcile_drift, which
        asks once. Nothing failed. So the list is derived here from the
        source and compared to the prose, in both directions."""
        root = Path(__file__).resolve().parents[1]
        actual = set()
        for path in sorted(root.glob("*.py")):
            if path.name == "knowledge_plane.py":
                continue
            for node in ast.walk(ast.parse(
                    path.read_text(encoding="utf-8"))):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = (func.id if isinstance(func, ast.Name)
                        else func.attr if isinstance(func, ast.Attribute)
                        else None)
                if name == "row_done":
                    actual.add(path.name)
        # normalised first: the docstring rewraps whenever the prose
        # around it changes, and a listing that only matches at one line
        # width is a test that fails for the wrong reason
        flat = " ".join(knowledge_plane.row_done.__doc__.split())
        listing = re.search(r"Call sites\s*\(.*?\):(.*?)—", flat)
        self.assertIsNotNone(
            listing,
            "row_done's docstring no longer carries a delimited"
            " `Call sites (...): <modules> —` listing for this test to"
            " check")
        documented = set(re.findall(r"[a-z_]+\.py", listing.group(1)))
        self.assertEqual(documented, actual)
        self.assertTrue(actual, "no call sites found — the derivation"
                                " itself is broken")


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


class TestParseRun(unittest.TestCase):
    """parse_run (ADR-0039's amendment, issue #441 — expand phase only:
    no detector reads this yet). Built through the SAME planted-defect
    fixtures gates.py's own detector tests and selftest() share
    (issue #440's consolidation), not a fresh hand-typed tree — the
    exact duplication #440 closed."""

    def run_entry(self, root, parsed, rel):
        """The one run dict in parsed["runs"] at repo-relative `rel`."""
        matches = [r for r in parsed["runs"]
                  if r["path"].relative_to(root) == Path(rel)]
        self.assertEqual(len(matches), 1, parsed["runs"])
        return matches[0]

    def test_breakdown_matches_breakdown_files_exactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _wo_citation_defect_fixture(root)
            parsed = parse_run(root)
            expected = dict(breakdown_files(root))
            path = root / "docs/features/demo/breakdown.md"
            entry = self.run_entry(root, parsed, "docs/features/demo")
            self.assertEqual(entry["breakdown"], expected[path])
            self.assertIsNone(entry["prd_id"])
            self.assertIsNone(entry["architecture"])
            self.assertIsNone(entry["verification"])
            self.assertIsNone(entry["verification_error"])

    def test_prd_id_and_adr_files_from_link_integrity_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _link_integrity_defect_fixture(root)
            parsed = parse_run(root)
            self.assertEqual(
                self.run_entry(root, parsed, "docs/features/demo")["prd_id"],
                "PRD-0001")
            adr_names = {path.name for path, _ in parsed["adr_files"]}
            self.assertEqual(adr_names, {"0001-real.md"})
            _, lines = parsed["adr_files"][0]
            self.assertEqual(lines, ["# Real"])

    def test_verification_text_captured_per_run_and_unreadable_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _evidence_honesty_defect_fixture(root)
            # Corrupt one of the fixture's four verification.md files —
            # the case check_evidence_honesty turns into its own
            # "H: ... cannot be read" problem string.
            (root / "docs/features/gamed/verification.md").write_bytes(
                b"\xff\xfe not valid utf-8")
            parsed = parse_run(root)

            demo = self.run_entry(root, parsed, "docs/features/demo")
            self.assertIn("Suite is green", demo["verification"])
            self.assertIsNone(demo["verification_error"])

            gamed = self.run_entry(root, parsed, "docs/features/gamed")
            self.assertIsNone(gamed["verification"])
            self.assertIsNotNone(gamed["verification_error"])

    def test_architecture_lines_captured_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "docs" / "features" / "demo"
            run.mkdir(parents=True)
            (run / "architecture.md").write_text(
                "# Architecture\n\nno `Makefile` here.\n", encoding="utf-8")
            parsed = parse_run(root)
            entry = self.run_entry(root, parsed, "docs/features/demo")
            self.assertEqual(
                entry["architecture"],
                ["# Architecture", "", "no `Makefile` here."])
            self.assertIsNone(entry["breakdown"])
            self.assertIsNone(entry["prd_id"])

    def test_run_with_none_of_the_four_files_is_still_represented(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "features" / "empty").mkdir(parents=True)
            parsed = parse_run(root)
            entry = self.run_entry(root, parsed, "docs/features/empty")
            self.assertEqual(entry, {
                "path": root / "docs/features/empty",
                "breakdown": None, "prd_id": None, "prd": None,
                "prd_date": None, "architecture": None,
                "verification": None, "verification_error": None})

    def test_prd_lines_and_date_captured_when_present(self):
        """Detectors N and O read the PRD's body and its frontmatter
        date (ADR-0071, ADR-0072) — read here once, like architecture."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = root / "docs" / "features" / "demo"
            run.mkdir(parents=True)
            (run / "prd.md").write_text(
                "---\nid: PRD-0001\ndate: 2026-09-21\n---\n## Solution\n",
                encoding="utf-8")
            entry = self.run_entry(root, parse_run(root), "docs/features/demo")
            self.assertEqual(entry["prd"], ["---", "id: PRD-0001",
                                            "date: 2026-09-21", "---",
                                            "## Solution"])
            self.assertEqual(entry["prd_id"], "PRD-0001")
            self.assertEqual(entry["prd_date"], "2026-09-21")

    def test_adr_readme_lines_and_absence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(parse_run(root)["adr_readme"])
            (root / "docs" / "adr").mkdir(parents=True)
            (root / "docs" / "adr" / "README.md").write_text(
                "| ADR | Decision | Status |\n", encoding="utf-8")
            self.assertEqual(
                parse_run(root)["adr_readme"],
                ["| ADR | Decision | Status |"])

    def test_a_tree_without_docs_parses_to_an_empty_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(parse_run(Path(tmp)),
                             {"runs": [], "adr_files": [], "adr_readme": None,
                              "scannable": []})

    def test_scannable_defaults_to_empty_and_pays_no_i_o(self):
        # No `scannable` argument: callers that never touch it (detectors
        # A, G, H) do not pay for a walk they will not use.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _wo_citation_defect_fixture(root)
            self.assertEqual(parse_run(root)["scannable"], [])

    def test_scannable_reads_each_given_path_once_in_order(self):
        # `scannable` is an already-selected path list (gates.py's own
        # _scannable_files policy) — parse_run only reads it, in the
        # order given, same shape as adr_files.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "CONTEXT.md"
            first.write_text("first\ncontext\n", encoding="utf-8")
            second = root / "README.md"
            second.write_text("second\n", encoding="utf-8")
            parsed = parse_run(root, scannable=[first, second])
            self.assertEqual(parsed["scannable"], [
                (first, ["first", "context"]), (second, ["second"])])

    def test_the_clean_repo_fixture_parses_without_error(self):
        # The integration smoke fixture every detector's happy path
        # shares (selftest's "clean tree" case) — parse_run must read it
        # without raising and must see every artifact it plants.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _clean_repo_fixture(root)
            parsed = parse_run(root)
            demo = self.run_entry(root, parsed, "docs/features/demo")
            self.assertIsNotNone(demo["breakdown"])
            self.assertEqual(demo["prd_id"], "PRD-0001")
            evidenced = self.run_entry(root, parsed, "docs/features/evidenced")
            self.assertIsNotNone(evidenced["verification"])
            adr_names = {path.name for path, _ in parsed["adr_files"]}
            self.assertEqual(adr_names, {"0001-spine.md"})
            self.assertIsNotNone(parsed["adr_readme"])


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


class TestFences(unittest.TestCase):
    """The one fence rule: CommonMark closing (same character, at least as
    long as the opener, no info string) plus the backtick-info rule. Every
    caller that asks "is this line quoted?" reads it from here."""

    def kept(self, text):
        return [line for _, line in unfenced(text.split("\n"))]

    def test_tilde_inside_backtick_fence_is_content(self):
        self.assertEqual(
            self.kept("a\n```\n~~~\nquoted\n```\nb"), ["a", "b"])

    def test_three_backticks_inside_four_is_content(self):
        self.assertEqual(
            self.kept("a\n````\n```\nquoted\n```\n````\nb"), ["a", "b"])

    def test_a_longer_closer_closes(self):
        self.assertEqual(self.kept("a\n```\nquoted\n`````\nb"), ["a", "b"])
        self.assertTrue(fence_closes("`````", "`", 3))
        self.assertFalse(fence_closes("``", "`", 3))
        self.assertFalse(fence_closes("~~~", "`", 3))
        self.assertFalse(fence_closes("``` bash", "`", 3))

    def test_backtick_info_with_a_backtick_does_not_open(self):
        self.assertIsNone(fence_open("``` a`b"))
        self.assertEqual(fence_open("~~~ a`b"), ("~", 3))
        self.assertEqual(self.kept("``` a`b\nb"), ["``` a`b", "b"])

    def test_leading_whitespace_is_allowed(self):
        self.assertEqual(fence_open("    ```bash"), ("`", 3))
        self.assertTrue(fence_closes("    ```  ", "`", 3))
        self.assertEqual(self.kept("- x\n  ```\n  quoted\n  ```\nb"),
                         ["- x", "b"])

    def test_unterminated_fence_swallows_the_rest(self):
        self.assertEqual(self.kept("a\n````\nquoted\n```\nb"), ["a"])

    def test_line_numbers_are_one_based(self):
        self.assertEqual(list(unfenced(["a", "```", "x", "```", "b"])),
                         [(1, "a"), (5, "b")])


if __name__ == "__main__":
    unittest.main()
