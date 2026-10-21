"""decompose_grade.py — the offline Decompose breakdown grader.

The run is docs/features/decompose-eval-suite/ (ADR-0114). Every case runs
through the public interface with inline texts or the cut files under
plugin-evals/decompose/fixtures/csv-export/cuts/, offline, with exact
strings; nothing here calls a model or the network.
"""
import difflib
import re
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
