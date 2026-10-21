"""decompose_grade.py — the offline Decompose breakdown grader.

The run is docs/features/decompose-eval-suite/ (ADR-0114). Every case runs
through the public interface with inline texts or the cut files under
plugin-evals/decompose/fixtures/csv-export/cuts/, offline, with exact
strings; nothing here calls a model or the network.
"""
import ast
import difflib
import re
import sys
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
