"""Backlog grammar seam: protocol.py owns the docs/backlog.md entry
grammar (ADR-0029); parse_backlog and check_backlog are its public
surface. Tests assert parse shapes and exact problem strings through
those functions — no private helpers.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import protocol  # noqa: E402

CONFORMANT = """\
Seed backlog — advisory only (see docs/pipeline-protocol.md).

- Dark mode everywhere (from: feature:dark-mode)
- Fix flaky retry test (from: maintenance:retry-flake)
- A durable home for idea seeds (from: session:2026-07-05) (claimed: feature:seed-backlog)
- Ship faster (from: product)
"""


class TestParseBacklog(unittest.TestCase):
    def test_conformant_entries_parse_with_origin_and_claim(self):
        self.assertEqual(protocol.parse_backlog(CONFORMANT), [
            {"text": "Dark mode everywhere",
             "origin": "feature:dark-mode", "claimed": None},
            {"text": "Fix flaky retry test",
             "origin": "maintenance:retry-flake", "claimed": None},
            {"text": "A durable home for idea seeds",
             "origin": "session:2026-07-05",
             "claimed": "feature:seed-backlog"},
            {"text": "Ship faster", "origin": "product", "claimed": None},
        ])

    def test_malformed_lines_are_skipped_not_raised(self):
        text = ("- no origin marker at all\n"
                "- valid seed (from: product)\n"
                "- bad ref (from: sprint:12)\n")
        self.assertEqual(protocol.parse_backlog(text), [
            {"text": "valid seed", "origin": "product", "claimed": None}])

    def test_non_bullet_lines_are_ignored(self):
        text = "# header\n\nprose line\n- seed (from: feature:x)\n"
        self.assertEqual(protocol.parse_backlog(text), [
            {"text": "seed", "origin": "feature:x", "claimed": None}])

    def test_seed_text_may_contain_parentheses(self):
        text = "- omp near-miss under-triggering (8/16) (from: session:2026-07-05)\n"
        self.assertEqual(protocol.parse_backlog(text), [
            {"text": "omp near-miss under-triggering (8/16)",
             "origin": "session:2026-07-05", "claimed": None}])


class TestCheckBacklog(unittest.TestCase):
    def test_conformant_text_yields_no_problems(self):
        self.assertEqual(protocol.check_backlog(CONFORMANT), [])

    def test_bullet_without_origin_is_reported_with_line_number(self):
        text = "- valid seed (from: product)\n- dangling seed\n"
        self.assertEqual(protocol.check_backlog(text), [
            "backlog: line 2: entry does not match "
            "'- <seed text> (from: <run-ref>)'"])

    def test_bad_run_refs_in_origin_and_claim_are_reported(self):
        text = ("- seed one (from: sprint:12)\n"
                "- seed two (from: product) (claimed: FEATURE:Big)\n")
        self.assertEqual(protocol.check_backlog(text), [
            "backlog: line 1: invalid run-ref 'sprint:12'",
            "backlog: line 2: invalid run-ref 'FEATURE:Big'"])

    def test_non_bullet_lines_are_not_held_to_the_grammar(self):
        text = "# header\n\nplain prose, no (from:) marker\n"
        self.assertEqual(protocol.check_backlog(text), [])

    def test_malformed_input_never_raises(self):
        for text in ("", "- ", "-", "- (from: )", "- x (from: a) trailing"):
            with self.subTest(text=text):
                self.assertIsInstance(protocol.check_backlog(text), list)


if __name__ == "__main__":
    unittest.main()
