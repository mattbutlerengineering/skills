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


if __name__ == "__main__":
    unittest.main()
