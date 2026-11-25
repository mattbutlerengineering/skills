"""The daily improvement routine's protocol (docs/factory/
improvement-routine.md) is the routine's runtime interface: the cloud
routine reads it from the repo on every run. These tests pin the clauses
an Owner decision put there, so a later edit cannot drop one silently.
"""
import unittest
from pathlib import Path

PROTOCOL = Path(__file__).resolve().parents[1] / "docs" / "factory" \
    / "improvement-routine.md"


class TestTheToolsmithQueueIsRetired(unittest.TestCase):
    """#2360, chosen by the Owner on 2026-11-25 under ADR-0135: the
    toolsmith-mine workflow is gone, so the routine stops reading the
    frozen queue and the decision says why."""

    def text(self):
        return " ".join(PROTOCOL.read_text(encoding="utf-8").split())

    def test_orient_no_longer_reads_the_queue(self):
        self.assertNotIn("factory-toolsmith-queue", self.text())

    def test_the_retirement_is_recorded_with_its_date(self):
        self.assertIn("**2026-11-25: the toolsmith queue is retired**"
                      " (#2360)", self.text())


if __name__ == "__main__":
    unittest.main()
