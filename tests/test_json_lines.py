"""cli.json_lines — one JSON-lines read under the ADR-0075 guard (the
2026-10-25 consolidation). Seven readers each held a copy, and three of
them (conductor_close.history, dashboard._corrections, kb_harvest.mine)
caught only ValueError, so one line nested past the recursion limit
raised RecursionError out of the reader instead of becoming a problem.
"""
import tempfile
import unittest
from pathlib import Path

import cli
import conductor_close
import dashboard
import kb_harvest

# json.loads raises RecursionError for this, not JSONDecodeError (3.14
# needs a million levels; tests/test_cli.py pins the same depth).
DEEP = "[" * 1_000_000 + "]" * 1_000_000


class TestJsonLines(unittest.TestCase):
    def test_blank_lines_are_skipped_and_numbering_is_the_files(self):
        self.assertEqual(list(cli.json_lines('{"a": 1}\n\n  \n[2]\n')),
                         [(1, {"a": 1}, None), (4, [2], None)])

    def test_an_unparseable_line_is_an_error_and_the_walk_goes_on(self):
        rows = list(cli.json_lines('nope\n' + DEEP + '\n{"b": 2}\n'))
        self.assertEqual([(n, v) for n, v, _ in rows],
                         [(1, None), (2, None), (3, {"b": 2})])
        self.assertTrue(rows[0][2].startswith("Expecting value"))
        self.assertIsInstance(rows[1][2], str)
        self.assertIsNone(rows[2][2])


class TestCallersFailClosed(unittest.TestCase):
    """Each caller keeps its own policy; none of them raises."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_conductor_close_history_refuses_the_file(self):
        self.write(conductor_close.SCORECARDS, DEEP + "\n")
        rows, problems = conductor_close.history(self.root)
        self.assertIsNone(rows)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            f"cd: {conductor_close.SCORECARDS}:1 is not valid JSON:"))

    def test_dashboard_corrections_reports_the_line(self):
        self.write(dashboard.CORRECTIONS, DEEP + '\n{"wo": "WO-0001"}\n')
        problems = []
        self.assertEqual(dashboard._corrections(self.root, problems),
                         {"WO-0001": 1})
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            f"dashboard: {dashboard.CORRECTIONS}:1 is not valid JSON:"))

    def test_kb_harvest_skips_the_line(self):
        path = self.write("t.jsonl", DEEP + '\n{"type": "user"}\n')
        result, problems = kb_harvest.mine([path])
        self.assertEqual(problems, [])
        self.assertEqual(result["scanned"]["skipped_lines"], 1)


if __name__ == "__main__":
    unittest.main()
