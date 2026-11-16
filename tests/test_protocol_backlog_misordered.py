"""Audit defect #1856: parse_backlog skips what check_backlog rejects."""
import tempfile
import unittest
from pathlib import Path

import protocol


class TestMisorderedClaim(unittest.TestCase):
    def test_parse_skips_what_check_rejects(self):
        text = ("# Backlog\n- seed one (claimed: feature:a) (from: product)\n"
                "- seed two (from: product)\n")
        self.assertEqual(protocol.parse_backlog(text), [
            {"line": 3, "text": "seed two", "origin": "product",
             "claimed": None}])

if __name__ == "__main__":
    unittest.main()
