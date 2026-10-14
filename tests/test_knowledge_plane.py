"""knowledge_plane seam tests (ADR-0037): the typed-ID token grammar,
the dispatch-plane row grammar, the run walk, and repo_root — asserted
at the seam's own interface instead of once per caller suite.
"""
import tempfile
import unittest
from pathlib import Path

import knowledge_plane
from gates_selftest import (clean_repo_fixture,
                            evidence_honesty_defect_fixture,
                            link_integrity_defect_fixture,
                            wo_citation_defect_fixture)
from knowledge_plane import (ADR_TOKEN, CLOSES_TOKEN, FIELD_LIMIT,
                             PRD_TOKEN, ROW, WO_TOKEN, breakdown_files,
                             breakdown_rows, fence_closes, fence_open,
                             local_link_targets, mirror_map, parse_row,
                             parse_run, repo_root, resolve_link, run_dirs,
                             sanitize, unfenced)


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


class TestParseRow(unittest.TestCase):
    """The breakdown row as one parsed record (issue #737): every
    dispatch-plane reader takes its fields from parse_row or
    breakdown_rows, so 'is this a row, and what does it say' has one
    answer — the per-line accessors it composes have no other caller."""

    FULL = ("- [ ] **WO-0017** gate-queue digest — size:S,"
            " blocked by: WO-0001, WO-0003 (PRD-0001 §Solution)"
            " (tracker: #245)")

    def test_a_full_row_parses_to_every_field(self):
        self.assertEqual(parse_row(self.FULL), {
            "text": self.FULL, "wo": "WO-0017", "done": False,
            "issue": 245, "size": "S", "title": "gate-queue digest",
            "blockers": ["WO-0001", "WO-0003"], "unreadable": None,
            "pre_ledger": False, "prd_ids": ["PRD-0001"]})

    def test_checked_rows_across_every_bullet_and_indent(self):
        for line in ("- [x] WO-0002 done", "- [X] WO-0002 done",
                     "-\t[x] WO-0002 done", "+ [x] WO-0002 done",
                     "* [x] WO-0002 done", "  - [x] WO-0002 indented"):
            with self.subTest(line=line):
                row = parse_row(line)
                self.assertEqual((row["wo"], row["done"]), ("WO-0002", True))
        self.assertFalse(parse_row("- [ ] WO-0002 open")["done"])

    def test_prose_sub_bullets_and_malformed_boxes_are_not_rows(self):
        # ROW requires whitespace after the box, so a checked box glued
        # to its text is no row — done or otherwise.
        for line in ("WO-0002 in prose", "  - Accept: cites WO-0002",
                     "  - Notes: WO-0002 (PRD-0001 §Solution) (tracker: #7)",
                     "## WO-0002 heading", "- [ballot] WO-0002",
                     "-[x] WO-0002 t", "text - [x] WO-0002 t", "",
                     "- [x]a WO-0002 no space after the box",
                     "- [x]**WO-0003** bold straight after the box",
                     "A note about the mark. (pre-ledger)"):
            with self.subTest(line=line):
                self.assertIsNone(parse_row(line))

    def test_the_first_token_is_the_work_order_and_may_be_absent(self):
        line = "- [ ] **WO-0002** thing (PRD-0001 §2) after WO-0001"
        self.assertEqual(parse_row(line)["wo"], "WO-0002")
        self.assertEqual(parse_row(line)["blockers"], [])
        self.assertIsNone(parse_row("- [ ] anonymous work")["wo"])

    def test_unreadable_blockers_are_named_not_dropped(self):
        def row(clause):
            return parse_row(f"- [ ] **WO-0002** t — size:S, blocked by:"
                             f" {clause} (PRD-0001 §2) (tracker: #7)")
        for clause in ("WO-0001", "WO-0001, WO-0003", "WO-0001 and WO-0003",
                       "WO-0001; WO-0003", "—", "-", ""):
            with self.subTest(clause=clause):
                self.assertIsNone(row(clause)["unreadable"])
        for clause, unreadable, blockers in (
                ("Export API", "Export API", []), ("WO-001", "WO-001", []),
                ("WO-0001, Export API", "Export API", ["WO-0001"])):
            with self.subTest(clause=clause):
                self.assertEqual(
                    (row(clause)["unreadable"], row(clause)["blockers"]),
                    (unreadable, blockers))

    def test_tracker_title_and_size_are_optional(self):
        row = parse_row("- [ ] WO-0008 unmirrored row (PRD-0001 §Solution)")
        self.assertEqual((row["issue"], row["title"], row["size"]),
                         (None, None, None))
        self.assertEqual(parse_row("- [x] **WO-0002** labels.json +"
                                   " label-sync")["title"],
                         "labels.json + label-sync")

    def test_pre_ledger_is_a_trailing_mark_only(self):
        for line, marked in (
                ("- [x] **WO-0002** l — size:S (PRD-0001 §Solution)"
                 " (tracker: #107) (pre-ledger)", True),
                ("- [x] WO-0002 two (PRD-0001) (pre-ledger)  ", True),
                ("- [x] WO-0020 document the (pre-ledger) annotation"
                 " (PRD-0001 §Solution) (tracker: #150)", False),
                ("- [x] WO-0001 one (PRD-0001) (tracker: #106)", False)):
            with self.subTest(line=line):
                self.assertEqual(parse_row(line)["pre_ledger"], marked)

    def test_breakdown_rows_numbers_rows_and_skips_prose(self):
        lines = ["# Breakdown", "- [x] WO-0001 one (PRD-0001 §A)",
                 "  - Notes: WO-0001 follows WO-0009",
                 "- [ ] anonymous", "- [ ] WO-0002 two"]
        self.assertEqual(
            [(row["lineno"], row["wo"]) for row in breakdown_rows(lines)],
            [(2, "WO-0001"), (4, None), (5, "WO-0002")])

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

    def test_the_checked_row_grammar_has_one_owner(self):
        # ADR-0058 amends ADR-0039's roster from three owners to two.
        # gates.MERGED_ROW was a fourth, identical to DONE_ROW in pattern
        # AND flags. A re-added copy is the drift this pins.
        import gates
        self.assertFalse(
            hasattr(gates, "MERGED_ROW"),
            "gates.MERGED_ROW is back: the checked-row grammar has one"
            " owner, knowledge_plane.row_done (ADR-0058)")


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
    fixtures (gates_selftest.py) gates' detector tests and selftest() share
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
            wo_citation_defect_fixture(root)
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
            link_integrity_defect_fixture(root)
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
            evidence_honesty_defect_fixture(root)
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
            wo_citation_defect_fixture(root)
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
            clean_repo_fixture(root)
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
    the mirror grammar. It is built from two knowledge-plane names —
    breakdown_files and breakdown_rows — and names no
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


class TestLocalLinkTargets(unittest.TestCase):
    """The one local-link grammar (issue #739): CommonMark inline link
    destinations — titled, <angle-bracketed>, image — with URLs and
    in-page anchors excluded. Fence and inline-code skipping stays each
    caller's policy, so the grammar reads whatever text it is handed."""

    def test_the_issue_table(self):
        for text, want in (('[a](x.md "T")', ["x.md"]),
                           ("[a](x.md 'T')", ["x.md"]),
                           ("[a](x.md (T))", ["x.md"]),
                           ("[a](<my file.md>)", ["my file.md"]),
                           ('[a](<my file.md> "T")', ["my file.md"]),
                           ("[a]( x.md)", ["x.md"]),
                           ("[a](x.md)", ["x.md"])):
            with self.subTest(text=text):
                self.assertEqual(local_link_targets(text), want)

    def test_image_links_are_links(self):
        self.assertEqual(local_link_targets("![logo](img/logo.png)"),
                         ["img/logo.png"])

    def test_fragments_and_queries_are_kept_as_written(self):
        self.assertEqual(local_link_targets("[a](x.md#top) [b](y.md?v=1)"),
                         ["x.md#top", "y.md?v=1"])

    def test_urls_anchors_and_empty_targets_are_not_local(self):
        self.assertEqual(local_link_targets(
            "[a](#top) [b](https://x.io/a.md) [c](mailto:a@b.c) [d]()"
            " [e](<>)"), [])

    def test_balanced_parentheses_stay_in_the_target(self):
        self.assertEqual(local_link_targets("[a](docs/a(1).md)"),
                         ["docs/a(1).md"])

    def test_a_space_without_a_title_is_not_a_link(self):
        self.assertEqual(local_link_targets("[a](x.md junk)"), [])

    def test_every_link_on_a_line_in_order(self):
        self.assertEqual(local_link_targets("[a](a.md), [b](b.md)\n[c](c.md)"),
                         ["a.md", "b.md", "c.md"])

    def test_fences_and_inline_code_are_the_callers_policy(self):
        self.assertEqual(local_link_targets("`[a](a.md)`"), ["a.md"])


class TestResolveLink(unittest.TestCase):
    def test_relative_targets_resolve_against_the_linking_doc(self):
        self.assertEqual(resolve_link(Path("/r"), Path("/r/docs/a.md"),
                                      "../b.md"), Path("/r/docs/../b.md"))

    def test_a_leading_slash_is_root_relative(self):
        self.assertEqual(resolve_link(Path("/r"), Path("/r/docs/a.md"),
                                      "/src/x.py"), Path("/r/src/x.py"))

    def test_fragment_and_query_are_not_part_of_the_path(self):
        for target in ("b.md#top", "b.md?v=1", "b.md?v=1#top"):
            with self.subTest(target=target):
                self.assertEqual(resolve_link(Path("/r"), Path("/r/a.md"),
                                              target), Path("/r/b.md"))

    def test_an_anchor_or_url_names_no_path(self):
        for target in ("#top", "?v=1", "https://x.io/a.md", "mailto:a@b.c"):
            with self.subTest(target=target):
                self.assertIsNone(resolve_link(Path("/r"), Path("/r/a.md"),
                                               target))


if __name__ == "__main__":
    unittest.main()


class TestAdrRecord(unittest.TestCase):
    """The ADR record (issue #747): which files are ADRs, what status each
    declares, and its standing — one reading every tool and detector
    consults instead of six globs and three status readers."""

    STANDINGS = [
        ("accepted", "active"),
        ("accepted (Owner, 2026-10-11)", "active"),
        ("amended by ADR-0085", "active"),
        ("amended by ADR-0084 (and earlier by ADR-0041)", "active"),
        ("provisional", "provisional"),
        ("superseded in part by ADR-0083 (the beads clause)", "partial"),
        ("superseded by ADR-0002", "retired"),
        ("active", "unrecognized"),
        ("", "unrecognized"),
        (None, "unrecognized"),
    ]

    def test_every_status_head_has_its_standing(self):
        for text, expected in self.STANDINGS:
            with self.subTest(status=text):
                self.assertEqual(knowledge_plane.standing(text), expected)

    def test_every_adr_filename_form_is_one_file_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr_dir = root / "docs" / "adr"
            adr_dir.mkdir(parents=True)
            for name in ("0001-a.md", "0062.md", "adr-0063-x.md",
                         "ADR-007-auth.md", "README.md", "TEMPLATE.md",
                         "notes.md", "0004_under.md"):
                (adr_dir / name).write_text("# X\n", encoding="utf-8")
            found = [(number, path.name)
                     for number, path in knowledge_plane.adr_paths(root)]
            parsed = {path.name for path, _ in parse_run(root)["adr_files"]}
        self.assertEqual(found, [("0001", "0001-a.md"), ("0062", "0062.md"),
                                 ("0007", "ADR-007-auth.md"),
                                 ("0063", "adr-0063-x.md")])
        self.assertEqual(parsed, {name for _, name in found})

    def test_no_adr_directory_is_an_empty_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(knowledge_plane.adr_paths(tmp), [])

    def test_a_status_line_is_read_with_its_line(self):
        record = knowledge_plane.adr_record(
            Path("docs/adr/0001-old.md"),
            ["# Old", "", "- Status: superseded by ADR-0002 (all of it)"])
        self.assertEqual(record, {
            "number": "0001", "written": "0001",
            "path": Path("docs/adr/0001-old.md"),
            "lineno": 3, "status": "superseded by ADR-0002 (all of it)",
            "head": "superseded by ADR-0002", "standing": "retired",
            "superseded_by": "0002"})

    def test_the_number_is_four_digits_whatever_the_file_wrote(self):
        record = knowledge_plane.adr_record(
            Path("docs/adr/ADR-007-auth.md"), ["- Status: accepted"])
        self.assertEqual((record["number"], record["written"]),
                         ("0007", "007"))

    def test_a_frontmatter_status_is_the_fallback(self):
        record = knowledge_plane.adr_record(
            Path("0062.md"),
            ["---", "date: 2026-01-01", "status: provisional", "---", "# X"])
        self.assertEqual((record["number"], record["lineno"],
                          record["status"], record["standing"]),
                         ("0062", 3, "provisional", "provisional"))

    def test_a_status_line_wins_over_frontmatter(self):
        record = knowledge_plane.adr_record(
            Path("0001-x.md"),
            ["---", "status: active", "---", "- Status: accepted"])
        self.assertEqual((record["lineno"], record["status"]),
                         (4, "accepted"))

    def test_no_status_anywhere_is_none(self):
        record = knowledge_plane.adr_record(Path("0003-bare.md"), ["# Bare"])
        self.assertEqual((record["lineno"], record["status"], record["head"],
                          record["standing"], record["superseded_by"]),
                         (0, None, None, "unrecognized", None))

    def test_adr_records_reads_the_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adr_dir = root / "docs" / "adr"
            adr_dir.mkdir(parents=True)
            (adr_dir / "0062.md").write_text(
                "# X\n\n- Status: accepted\n", encoding="utf-8")
            [record] = knowledge_plane.adr_records(root)
        self.assertEqual((record["number"], record["standing"]),
                         ("0062", "active"))
