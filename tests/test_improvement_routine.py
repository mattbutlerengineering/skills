"""The daily improvement routine's protocol (docs/factory/
improvement-routine.md) is the routine's runtime interface: the cloud
routine reads it from the repo on every run. These tests pin the clauses
an Owner decision put there, so a later edit cannot drop one silently.
"""
import unittest
from pathlib import Path

PROTOCOL = Path(__file__).resolve().parents[1] / "docs" / "factory" \
    / "improvement-routine.md"


class TestTheDailyRoutineReadsTheToolsmithQueue(unittest.TestCase):
    """#818 part 2, decided by the Owner on 2026-10-14: the toolsmith
    queue's only other reader is the retro-reflect routine, whose
    trigger is deferred, so the daily routine reads it meanwhile."""

    def text(self):
        return " ".join(PROTOCOL.read_text(encoding="utf-8").split())

    def test_orient_finds_the_queue_by_its_marker(self):
        self.assertIn("The toolsmith queue: the open issue whose body"
                      " starts with `<!-- factory-toolsmith-queue -->`",
                      self.text())

    def test_reflect_counts_queue_entries_and_never_writes_the_queue(self):
        text = self.text()
        self.assertIn("Every toolsmith-queue entry inside the window",
                      text)
        self.assertIn("never edits or comments on the toolsmith queue",
                      text)

    def test_the_decision_is_recorded_with_its_date(self):
        self.assertIn("**2026-10-14: the daily routine reads the"
                      " toolsmith queue, by owner decision** (#818)",
                      self.text())


if __name__ == "__main__":
    unittest.main()
