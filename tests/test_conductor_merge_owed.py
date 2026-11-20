"""A merge turn that stalls because the item's cover no longer holds: a
train item whose ADR the turn renumbered (confirm_reservations) has a
gate file nobody approved, so it "needs its own merge ask" (ADR-0036
condition 3). After the Owner's retry, `next` lists it in merge_due so
that ask is raised, and offers the resumed merge only once the cover
reads COVERED, never a turn that merge_problems refuses on every retry.
A facet of tests/test_conductor_merge.py (its row builders), split out
so the suites run as parallel modules.
"""
import sys
import unittest
from pathlib import Path

import conductor_flow as flow
import conductor_merge as merge
import conductor_next as nxt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_git import FakeGit, raw_diff  # noqa: E402
from test_conductor_flow import (NOW, START, alive, answered,  # noqa: E402
                                 moved, stall_ask)
from test_conductor_merge import feature_shipped, own, train  # noqa: E402

OLD = "docs/adr/0130-x.md"
NEW = "docs/adr/0131-x.md"
# The turn renumbered the ADR, the cover re-check stalled it, and the
# Owner answered retry.
STALLED = (feature_shipped({OLD: "a"}) + train("ask-2", ["#12"])
           + [moved("#12", "ship", "merging", pid=5),
              moved("#12", "merging", "stalled", cause="merge-failed"),
              stall_ask("ask-3", "#12", ("retry", "block"))])
RETRIED = STALLED + [answered("ask-3", "retry", "#12")]
FACTS = {"#12": {"gate_blobs": {NEW: "b"}}}


def ready(rows, facts=FACTS):
    found, _, problems = flow.survey(START + rows, NOW, 3, alive, facts)
    assert problems == [], problems
    return [entry for entry in found if entry["item"] == "#12"]


class TestARenumberedTrainItem(unittest.TestCase):
    def test_a_retried_owed_merge_is_due_its_own_ask(self):
        self.assertEqual(flow.merge_due(START + RETRIED, FACTS), ["#12"])

    def test_a_retried_owed_merge_is_not_offered(self):
        self.assertEqual(ready(RETRIED), [])

    def test_an_unanswered_stall_is_not_due_yet(self):
        self.assertEqual(flow.merge_due(START + STALLED, FACTS), [])

    def test_its_own_merge_answer_resumes_the_merge(self):
        rows = RETRIED + own("ask-4", "#12")
        self.assertEqual(flow.merge_due(START + rows, FACTS), [])
        self.assertEqual(ready(rows), [{"item": "#12", "step": "merge"}])
        self.assertEqual(merge.merge_problems(START + rows, "#12",
                                              {NEW: "b"}), [])

    def test_a_resumed_merge_waits_for_its_gate_blobs(self):
        self.assertEqual(ready(RETRIED + own("ask-4", "#12"), facts={}), [])

    def test_next_reads_the_stalled_merge_s_gate_blobs(self):
        git = FakeGit({("diff",): raw_diff([NEW], {NEW: "b"})})
        self.assertEqual(nxt.shipped_facts(git, "b1", START + RETRIED),
                         (FACTS, []))


class TestAStillCoveredStalledMerge(unittest.TestCase):
    def test_a_retried_covered_merge_resumes_and_is_not_due(self):
        facts = {"#12": {"gate_blobs": {OLD: "a"}}}
        self.assertEqual(ready(RETRIED, facts),
                         [{"item": "#12", "step": "merge"}])
        self.assertEqual(flow.merge_due(START + RETRIED, facts), [])


if __name__ == "__main__":
    unittest.main()
