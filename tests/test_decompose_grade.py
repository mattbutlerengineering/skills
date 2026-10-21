"""decompose_grade.py — the offline Decompose breakdown grader.

The run is docs/features/decompose-eval-suite/ (ADR-0114). Every case runs
through the public interface with inline texts or the cut files under
plugin-evals/decompose/fixtures/csv-export/cuts/, offline, with exact
strings; nothing here calls a model or the network.
"""
import ast
import difflib
import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import decompose_grade as dg

ROOT = Path(__file__).resolve().parents[1]
CUTS = ROOT / "plugin-evals/decompose/fixtures/csv-export/cuts"
FIXTURE = ROOT / "evals/fixtures/decompose-feature/docs/features/csv-export"
TEMPLATE = ROOT / "skills/decompose/TEMPLATE.md"
BAD_CUTS = ("bad-coverage", "bad-dangling", "bad-accept", "bad-sized")
SLOT = re.compile(r"<[^<>\n]+>")
BACKTICKED = re.compile(r"`[^`\n]*`")
TYPED_ID = re.compile(r"\b(?:PRD|WO|ADR)-\d+")


def cut(name):
    return (CUTS / f"{name}.md").read_text(encoding="utf-8")


def slots_outside_code(text):
    return SLOT.findall(BACKTICKED.sub("", text))


def changed_lines(a, b):
    """max(lines only in a, lines only in b) of a line diff."""
    marks = [line[0] for line in difflib.ndiff(a.splitlines(),
                                               b.splitlines())]
    return max(marks.count("-"), marks.count("+"))


class TestCutFiles(unittest.TestCase):
    def test_the_five_cut_files_exist(self):
        for name in ("good", *BAD_CUTS):
            self.assertTrue((CUTS / f"{name}.md").is_file(), name)

    def test_each_bad_cut_differs_from_good_by_at_most_two_lines(self):
        for name in BAD_CUTS:
            diff = changed_lines(cut("good"), cut(name))
            self.assertTrue(1 <= diff <= 2, f"{name}: {diff} line(s)")

    def test_good_holds_no_template_slot_outside_backticks(self):
        template = slots_outside_code(TEMPLATE.read_text(encoding="utf-8"))
        self.assertTrue(template)
        found = set(slots_outside_code(cut("good")))
        self.assertEqual(sorted(found & set(template)), [])

    def test_no_cut_carries_a_typed_id_or_a_docs_path(self):
        for name in ("good", *BAD_CUTS):
            text = cut(name)
            self.assertEqual(TYPED_ID.findall(text), [], name)
            self.assertNotIn("docs/", text, name)

    def test_each_cut_starts_with_decompose_frontmatter(self):
        for name in ("good", *BAD_CUTS):
            head = cut(name).split("---", 2)
            self.assertEqual(head[0], "", name)
            self.assertIn("stage: decompose", head[1], name)


ARCH = """# Architecture: Demo

## Components

### Alpha Service

- Responsibility: stores records.

### Beta Worker (async)

- Responsibility: drains the queue and retries up to 3 times.

## Interfaces & contracts

### POST /alpha

- Output: 201 with the stored record.
"""

GOOD_BREAKDOWN = """---
stage: decompose
---

# Breakdown: Demo

- [ ] **A1 Alpha endpoint** — Alpha Service stores a record
  - Accept: `POST /alpha` returns 201 with the stored record.
  - Blocked by: —
- [ ] **A2 Beta job** — Beta Worker drains the queue
  - Accept: the worker retries a failed job 3 times before it gives up.
  - Blocked by: A1
"""

NO_ITEMS = "no-items: breakdown holds no checkbox work items"
PARTS = ("coverage", "dependencies", "accept", "sizing")
BANNED_IMPORTS = {"socket", "urllib", "http", "subprocess", "anthropic",
                  "openai", "requests", "cli"}
ALLOWED_LOCAL = {"knowledge_plane", "decompose_signals"}


def imported_names(nodes):
    names = set()
    for node in nodes:
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


class TestGradeCore(unittest.TestCase):
    def test_a_breakdown_with_no_rows_scores_zero_with_one_line(self):
        result = dg.grade("# Breakdown: Demo\n\nprose only\n", ARCH)
        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["feedback"], [NO_ITEMS])
        self.assertEqual(sorted(result["parts"]), sorted(PARTS))

    def test_an_architecture_with_no_components_section_raises(self):
        with self.assertRaises(ValueError) as caught:
            dg.grade(GOOD_BREAKDOWN, "# Architecture\n\n## Approach\n\nx\n")
        self.assertEqual(str(caught.exception), "holds no components")

    def test_a_components_section_with_no_headings_raises(self):
        arch = "# Architecture\n\n## Components\n\nprose only\n"
        with self.assertRaises(ValueError) as caught:
            dg.grade(GOOD_BREAKDOWN, arch)
        self.assertEqual(str(caught.exception), "holds no components")

    def test_a_two_item_breakdown_with_one_edge_scores_all_ones(self):
        result = dg.grade(GOOD_BREAKDOWN, ARCH)
        self.assertEqual(result, {
            "score": 1.0, "feedback": [],
            "parts": {"coverage": 1.0, "dependencies": 1.0, "accept": 1.0,
                      "sizing": 1.0}})

    def test_no_edges_leave_the_dependencies_part_at_one(self):
        text = GOOD_BREAKDOWN.replace("Blocked by: A1", "Blocked by: —")
        self.assertEqual(dg.grade(text, ARCH)["parts"]["dependencies"], 1.0)

    def test_the_score_is_the_mean_of_the_parts_rounded_to_three_places(self):
        # (1 + 1 + 1 + 0.5) / 4 = 0.875; (0.5 + 1 + 1 + 2/3) / 4 = 0.79166
        self.assertEqual(dg.combine({"coverage": 1.0, "dependencies": 1.0,
                                     "accept": 1.0, "sizing": 0.5}), 0.875)
        self.assertEqual(dg.combine({"coverage": 0.5, "dependencies": 1.0,
                                     "accept": 1.0, "sizing": 2 / 3}), 0.792)

    def test_the_summary_line_has_three_place_figures(self):
        record = {"score": 0.875, "feedback": [],
                  "parts": {"coverage": 1.0, "dependencies": 1.0,
                            "accept": 1.0, "sizing": 0.5}}
        self.assertEqual(
            dg.summary(record),
            "decompose-grade: score 0.875 (coverage 1.000,"
            " dependencies 1.000, accept 1.000, sizing 0.500)")

    def test_a_row_with_no_bold_span_takes_its_row_text_as_its_key(self):
        text = "- [ ] plain row text — more\n- [ ] **B2 Bold** — x\n"
        self.assertEqual([i["key"] for i in dg.read_items(text)],
                         ["plain row text", "B2"])

    def test_the_same_inputs_give_an_equal_record_twice(self):
        self.assertEqual(dg.grade(GOOD_BREAKDOWN, ARCH),
                         dg.grade(GOOD_BREAKDOWN, ARCH))


class TestGradeImports(unittest.TestCase):
    def setUp(self):
        self.tree = ast.parse(
            (ROOT / "decompose_grade.py").read_text(encoding="utf-8"))

    def test_module_level_imports_are_stdlib_and_the_two_leaf_modules(self):
        names = imported_names(self.tree.body)
        self.assertEqual(
            sorted(n for n in names
                   if n not in sys.stdlib_module_names), sorted(
                       names & ALLOWED_LOCAL))
        self.assertEqual(names & BANNED_IMPORTS, set())

    def test_no_import_anywhere_reaches_the_network_or_a_model(self):
        names = imported_names(ast.walk(self.tree))
        self.assertEqual(names & (BANNED_IMPORTS - {"cli"}), set())

    def test_the_core_does_not_import_cli(self):
        # cli is reachable only from main (the front door, S14).
        core = [n for n in self.tree.body
                if not (isinstance(n, ast.FunctionDef) and n.name == "main")]
        self.assertNotIn("cli", imported_names(ast.walk(ast.Module(
            body=core, type_ignores=[]))))


GOOD_ACCEPT = "`POST /alpha` returns 201 with the stored record."
BOTH = "Alpha Service and Beta Worker"


def row(key, blocked="—", title=BOTH, accept=GOOD_ACCEPT, inline=None):
    """One checkbox row in TEMPLATE form; `blocked=None` drops the clause."""
    head = f"- [ ] **{key} Thing** — {title}"
    if inline is not None:
        head += f" — size:S, blocked by: {inline}"
    lines = [head, f"  - Accept: {accept}"]
    if blocked is not None:
        lines.append(f"  - Blocked by: {blocked}")
    return "\n".join(lines)


def breakdown(*rows):
    return "# Breakdown: Demo\n\n" + "\n".join(rows) + "\n"


def lines_of(result, prefix):
    return [f for f in result["feedback"] if f.startswith(prefix)]


MISS_BETA = 'coverage-miss: component "Beta Worker" is named by no item'


class TestCoverageCheck(unittest.TestCase):
    def test_a_component_named_by_no_row_block_is_a_miss(self):
        result = dg.grade(breakdown(row("A1", title="Alpha Service only")),
                          ARCH)
        self.assertEqual(result["feedback"], [MISS_BETA])
        self.assertEqual(result["parts"]["coverage"], 0.5)

    def test_matching_is_case_insensitive_and_reads_sub_bullets(self):
        text = breakdown(row("A1", title="alpha service only",
                             accept=GOOD_ACCEPT + " BETA WORKER runs."))
        self.assertEqual(dg.grade(text, ARCH)["feedback"], [])

    def test_a_trailing_parenthetical_is_not_part_of_the_name(self):
        arch = ARCH.replace("### Beta Worker (async)", "### Beta Worker (async, v2)")
        self.assertEqual(
            dg.grade(breakdown(row("A1")), arch)["feedback"], [])

    def test_a_name_shorter_than_four_characters_is_not_graded(self):
        arch = ARCH.replace("### Beta Worker (async)", "### API")
        result = dg.grade(breakdown(row("A1", title="Alpha Service")), arch)
        self.assertEqual(result["feedback"], [])
        self.assertEqual(result["parts"]["coverage"], 1.0)

    def test_a_component_name_is_not_matched_inside_a_longer_word(self):
        result = dg.grade(
            breakdown(row("A1", title="Alpha Service and Beta Workers")),
            ARCH)
        self.assertEqual(result["feedback"], [MISS_BETA])


class TestDependencyCheck(unittest.TestCase):
    def test_a_blocker_naming_an_item_key_resolves(self):
        text = breakdown(row("A1"), row("A2", blocked="A1"))
        self.assertEqual(dg.grade(text, ARCH)["feedback"], [])

    def test_the_clause_may_be_inline_and_any_case(self):
        text = breakdown(row("A1"), row("A2", blocked=None, inline="A9"))
        self.assertEqual(
            dg.grade(text, ARCH)["feedback"],
            ['dangling-blocked-by: A2 is blocked by "A9",'
             ' which names no item'])
        text = text.replace("blocked by:", "Blocked By:")
        self.assertEqual(len(dg.grade(text, ARCH)["feedback"]), 1)

    def test_the_clause_splits_on_semicolons_and_commas(self):
        text = breakdown(row("A1"), row("A2"),
                         row("A3", blocked="A1; A2, A7"))
        result = dg.grade(text, ARCH)
        self.assertEqual(result["feedback"], [
            'dangling-blocked-by: A3 is blocked by "A7",'
            ' which names no item'])
        self.assertEqual(result["parts"]["dependencies"], round(2 / 3, 3))

    def test_dash_none_and_absent_clauses_make_no_edge(self):
        for blocked in ("—", "-", "none", "None", None):
            text = breakdown(row("A1", blocked=blocked))
            result = dg.grade(text, ARCH)
            self.assertEqual(result["feedback"], [], blocked)
            self.assertEqual(result["parts"]["dependencies"], 1.0, blocked)

    def test_an_element_that_starts_with_a_key_resolves_with_its_title(self):
        text = breakdown(row("A1"), row("A2", blocked="A1 Thing"))
        self.assertEqual(dg.grade(text, ARCH)["feedback"], [])

    def test_a_key_is_matched_at_a_word_boundary(self):
        text = breakdown(row("A1"), row("A2", blocked="A10"))
        self.assertEqual(
            dg.grade(text, ARCH)["feedback"],
            ['dangling-blocked-by: A2 is blocked by "A10",'
             ' which names no item'])

    def test_an_item_naming_itself_is_dangling(self):
        text = breakdown(row("A1", blocked="A1"))
        self.assertEqual(
            dg.grade(text, ARCH)["feedback"],
            ['dangling-blocked-by: A1 is blocked by "A1",'
             ' which names no item'])

    def test_two_dangling_elements_give_two_lines_in_item_order(self):
        text = breakdown(row("A1", blocked="A8"), row("A2", blocked="A9"))
        self.assertEqual(
            dg.grade(text, ARCH)["feedback"],
            ['dangling-blocked-by: A1 is blocked by "A8",'
             ' which names no item',
             'dangling-blocked-by: A2 is blocked by "A9",'
             ' which names no item'])

    def test_coverage_lines_come_before_dependency_lines(self):
        text = breakdown(row("A1", title="Alpha Service", blocked="A9"))
        self.assertEqual(
            dg.grade(text, ARCH)["feedback"],
            [MISS_BETA, 'dangling-blocked-by: A1 is blocked by "A9",'
                        ' which names no item'])


def untestable(item, reason):
    return (f"untestable-accept: {item} has no checkable Accept line"
            f" ({reason})")


class TestAcceptCheck(unittest.TestCase):
    def grade_accept(self, accept):
        return dg.grade(breakdown(row("A1", accept=accept)), ARCH)

    def test_a_concrete_accept_line_emits_nothing(self):
        result = self.grade_accept(GOOD_ACCEPT)
        self.assertEqual(result["feedback"], [])
        self.assertEqual(result["parts"]["accept"], 1.0)

    def test_an_item_with_no_accept_sub_bullet_is_empty(self):
        text = breakdown(f"- [ ] **A1 Thing** — {BOTH}\n  - Blocked by: —")
        self.assertEqual(dg.grade(text, ARCH)["feedback"],
                         [untestable("A1", "empty")])

    def test_an_empty_accept_line_is_empty(self):
        for accept in ("", "  ", "."):
            self.assertEqual(self.grade_accept(accept)["feedback"],
                             [untestable("A1", "empty")], repr(accept))

    def test_an_unfilled_slot_outside_backticks_is_a_placeholder(self):
        result = self.grade_accept("<checkable acceptance criterion>")
        self.assertEqual(result["feedback"],
                         [untestable("A1", "placeholder")])
        self.assertEqual(result["parts"]["accept"], 0.0)

    def test_a_slot_inside_backticks_is_not_a_placeholder(self):
        accept = GOOD_ACCEPT + " The object is named `<prefix>/<slug>.csv`."
        self.assertEqual(self.grade_accept(accept)["feedback"], [])

    def test_a_listed_hedge_with_an_anchor_leaves_too_few_words(self):
        for accept in ("`POST /alpha` works correctly.",
                       "Alpha Service handles errors appropriately.",
                       "Works correctly and handles errors appropriately."):
            self.assertEqual(self.grade_accept(accept)["feedback"],
                             [untestable("A1", "unanchored")], accept)

    def test_filler_words_with_no_anchor_earn_nothing(self):
        accept = ("the thing behaves nicely under many circumstances and"
                  " users are happy with the outcome overall")
        self.assertEqual(self.grade_accept(accept)["feedback"],
                         [untestable("A1", "unanchored")])

    def test_a_backticked_name_absent_from_the_fixture_earns_nothing(self):
        accept = "`invented_name` is returned to the caller promptly"
        self.assertEqual(self.grade_accept(accept)["feedback"],
                         [untestable("A1", "unanchored")])

    def test_each_anchor_kind_is_accepted(self):
        for accept in (
                "Alpha Service rejects a malformed request cleanly",
                "the route `POST /alpha` rejects a malformed request",
                "a malformed request is rejected with status 201 always",
                "POST /alpha rejects a malformed request cleanly"):
            self.assertEqual(self.grade_accept(accept)["feedback"], [],
                             accept)

    def test_the_prd_widens_the_anchor_vocabulary(self):
        accept = "the export lands within 5 minutes of the scheduled time"
        self.assertEqual(self.grade_accept(accept)["feedback"],
                         [untestable("A1", "unanchored")])
        text = breakdown(row("A1", accept=accept))
        prd = "Success: a CSV within 5 minutes."
        self.assertEqual(dg.grade(text, ARCH, prd)["feedback"], [])

    def test_an_item_fails_the_accept_part_once(self):
        text = breakdown(row("A1", accept="<slot>"), row("A2"))
        result = dg.grade(text, ARCH)
        self.assertEqual(result["parts"]["accept"], 0.5)

    def test_accept_lines_come_after_dependency_lines_in_item_order(self):
        text = breakdown(row("A1", accept="", blocked="A9"),
                         row("A2", accept="fine"))
        self.assertEqual(
            dg.grade(text, ARCH)["feedback"],
            ['dangling-blocked-by: A1 is blocked by "A9",'
             ' which names no item',
             untestable("A1", "empty"), untestable("A2", "unanchored")])

    def test_known_limit_an_unlisted_hedge_with_three_other_words_passes(self):
        # Stated limit (architecture.md, Accept check): the hedge list is
        # finite, so an unlisted vague phrase that carries an anchor and
        # three other words is not caught. The harness llm graders are the
        # in-harness check for this; the grader says nothing here.
        accept = "`POST /alpha` is basically fine overall"
        self.assertEqual(self.grade_accept(accept)["feedback"], [])


def mis_sized(item, count):
    return f"mis-sized: {item} names {count} components (limit 3)"


FOUR = {"A": "Alpha Service", "B": "Beta Worker", "C": "Gamma Router",
        "D": "Delta Store"}
ARCH4 = ARCH.replace(
    "## Interfaces", "### Gamma Router\n\n- Responsibility: routes.\n\n"
    "### Delta Store\n\n- Responsibility: stores.\n\n## Interfaces")


class TestSizeCheck(unittest.TestCase):
    def test_an_item_naming_four_components_is_mis_sized(self):
        result = dg.grade(breakdown(row("A1", title=" ".join(FOUR.values()))),
                          ARCH4)
        self.assertEqual(result["feedback"], [mis_sized("A1", 4)])
        self.assertEqual(result["parts"]["sizing"], 0.0)

    def test_an_item_naming_exactly_three_is_not(self):
        text = breakdown(row("A1", title="Alpha Service Beta Worker"
                                         " Gamma Router"),
                         row("A2", title="Delta Store"))
        self.assertEqual(dg.grade(text, ARCH4)["feedback"], [])

    def test_an_item_naming_none_is_not_mis_sized(self):
        text = breakdown(row("A1", title="Alpha Service Beta Worker"
                                         " Gamma Router"),
                         row("A2", title="Delta Store"),
                         row("A3", title="wire it up"))
        result = dg.grade(text, ARCH4)
        self.assertEqual(result["feedback"], [])
        self.assertEqual(result["parts"]["sizing"], 1.0)

    def test_sub_bullets_count_toward_the_span(self):
        text = breakdown(row("A1", title="Alpha Service",
                             accept=GOOD_ACCEPT + " Beta Worker, Gamma"
                                    " Router and Delta Store agree."))
        self.assertEqual(dg.grade(text, ARCH4)["feedback"],
                         [mis_sized("A1", 4)])

    def test_the_declared_size_band_changes_nothing(self):
        wide = " ".join(FOUR.values())
        small = row("A1", title=wide, inline="—")
        large = row("A2", title=wide, inline="—").replace("size:S", "size:L")
        self.assertIn("size:S", small)
        self.assertIn("size:L", large)
        self.assertEqual(
            dg.grade(breakdown(small, large), ARCH4)["feedback"],
            [mis_sized("A1", 4), mis_sized("A2", 4)])

    def test_accept_length_changes_nothing(self):
        short = breakdown(row("A1", title="Alpha Service"))
        long_ = breakdown(row("A1", title="Alpha Service",
                              accept=GOOD_ACCEPT * 6))
        self.assertEqual(dg.grade(short, ARCH4)["parts"]["sizing"],
                         dg.grade(long_, ARCH4)["parts"]["sizing"])

    def test_size_lines_come_last_in_item_order(self):
        wide = " ".join(FOUR.values())
        text = breakdown(row("A1", title=wide, accept=""),
                         row("A2", title=wide, blocked="A9"))
        self.assertEqual(
            dg.grade(text, ARCH4)["feedback"],
            ['dangling-blocked-by: A2 is blocked by "A9",'
             ' which names no item',
             untestable("A1", "empty"), mis_sized("A1", 4),
             mis_sized("A2", 4)])


FIXTURE_ARCH = (FIXTURE / "architecture.md").read_text(encoding="utf-8")
FIXTURE_PRD = (FIXTURE / "prd.md").read_text(encoding="utf-8")
EXPECTED = {
    "bad-coverage": (0.938, [
        'coverage-miss: component "Delivery" is named by no item']),
    "bad-dangling": (0.964, [
        'dangling-blocked-by: S6 is blocked by "S9", which names no item']),
    "bad-accept": (0.958, [untestable("S3", "unanchored")]),
    "bad-sized": (0.958, [mis_sized("S6", 4)]),
}
# check function -> the bad cut that check alone must flag
MUTATIONS = {"check_coverage": "bad-coverage",
             "check_dependencies": "bad-dangling",
             "check_accept": "bad-accept", "check_sizing": "bad-sized"}


def grade_cut(name):
    return dg.grade(cut(name), FIXTURE_ARCH, FIXTURE_PRD)


class TestGoodVersusBadCuts(unittest.TestCase):
    def test_the_good_cut_emits_nothing_and_scores_one(self):
        result = grade_cut("good")
        self.assertEqual(result["feedback"], [])
        self.assertEqual(result["score"], 1.0)

    def test_each_bad_cut_emits_exactly_its_own_line_and_a_lower_score(self):
        for name, (score, feedback) in EXPECTED.items():
            result = grade_cut(name)
            self.assertEqual(result["feedback"], feedback, name)
            self.assertEqual(result["score"], score, name)
            self.assertLess(result["score"], grade_cut("good")["score"])

    def test_each_check_is_what_flags_its_bad_cut(self):
        # Mutation check, in place of a red run: replace each check with a
        # no-op in turn. The cut's output must change, which also proves
        # the mutation applied (a no-op patch that changed nothing would
        # leave the line in place and fail here).
        for check, name in MUTATIONS.items():
            before = grade_cut(name)
            with mock.patch.object(dg, check,
                                   lambda *args, **kw: (1.0, [])):
                after = grade_cut(name)
            self.assertNotEqual(after, before, check)
            self.assertEqual(after["feedback"], [], check)
            self.assertEqual(after["score"], 1.0, check)


USAGE = ("decompose-grade: usage: python3 decompose_grade.py <breakdown.md>"
         " <architecture.md> [<prd.md>]")
GOOD_SUMMARY = ("decompose-grade: score 1.000 (coverage 1.000,"
                " dependencies 1.000, accept 1.000, sizing 1.000)")


class TestFrontDoor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.arch = self.write("architecture.md", FIXTURE_ARCH)
        self.prd = self.write("prd.md", FIXTURE_PRD)

    def write(self, name, text):
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def run_main(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = dg.main(list(argv))
        return code, out.getvalue().splitlines()

    def test_a_good_cut_prints_the_summary_and_exits_zero(self):
        path = self.write("good.md", cut("good"))
        self.assertEqual(self.run_main(path, self.arch, self.prd), (
            0, [GOOD_SUMMARY, "decompose-grade: 0 problem(s)"]))

    def test_a_bad_cut_prints_the_summary_then_its_line_and_exits_one(self):
        path = self.write("bad.md", cut("bad-accept"))
        self.assertEqual(self.run_main(path, self.arch, self.prd), (1, [
            "decompose-grade: score 0.958 (coverage 1.000,"
            " dependencies 1.000, accept 0.833, sizing 1.000)",
            untestable("S3", "unanchored"), "decompose-grade: 1 problem(s)"]))

    def test_a_wrong_argument_count_exits_two_and_scores_nothing(self):
        for argv in ([], ["a.md"], ["a", "b", "c", "d"]):
            self.assertEqual(self.run_main(*argv), (2, [USAGE]), argv)

    def test_a_missing_file_exits_two(self):
        missing = str(self.dir / "nope.md")
        self.assertEqual(self.run_main(missing, self.arch), (
            2, [f"decompose-grade: cannot read {missing}: no such file"]))

    def test_an_unreadable_file_exits_two_with_the_guarded_read_message(self):
        bad = self.dir / "bad.md"
        bad.write_bytes(b"\xff\xfe")
        code, lines = self.run_main(str(bad), self.arch)
        self.assertEqual(code, 2)
        self.assertEqual(len(lines), 1)
        self.assertTrue(
            lines[0].startswith(f"decompose-grade: cannot read {bad}: "))

    def test_an_architecture_with_no_components_exits_two_not_one(self):
        arch = self.write("empty-arch.md", "# Architecture\n\n## Approach\n")
        path = self.write("good.md", cut("good"))
        self.assertEqual(self.run_main(path, arch), (
            2, [f"decompose-grade: {arch} holds no components"]))

    def test_the_prd_is_optional_and_only_widens_the_anchors(self):
        accept = "a due schedule lands the export within 5 minutes"
        arch = self.write("a.md", ARCH)
        path = self.write("b.md", breakdown(row("A1", accept=accept)))
        prd = self.write("p.md", "A CSV within 5 minutes.")
        code, lines = self.run_main(path, arch)
        self.assertEqual((code, lines[1]), (1, untestable("A1", "unanchored")))
        self.assertEqual(self.run_main(path, arch, prd)[0], 0)

    def test_no_file_is_written(self):
        before = sorted(p.name for p in self.dir.iterdir())
        self.run_main(self.write("good.md", cut("good")), self.arch)
        after = sorted(p.name for p in self.dir.iterdir())
        self.assertEqual(after, sorted(before + ["good.md"]))


if __name__ == "__main__":
    unittest.main()
