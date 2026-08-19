"""The gate vocabulary and one issue's gate history, tested at the
interface it is moving to (ADR-0056).

Written against today's code, where the vocabulary still lives inside
gate_digest.py and the rejection half inside rejection_mining.py — the
import lines below are the whole of the awkwardness, and they are the
measurement: a suite about what a gate IS should not have to name two
leaf tools to get at it. When human_gates.py lands, only those lines
move; no case here changes.

What this suite owns that neither tool's suite has: the partition
property. For one event history, the passages and the rejections
together are exactly the completed stays, and no stay is in both. That
invariant lives today as prose in a docstring (rejection_mining.py), so
nothing catches the day the two hand-written window tests stop
agreeing.
"""
import unittest

from gate_digest import GATES, gate_passages, label_events, waiting_since
from rejection_mining import gate_rejections


def labeled(ts, name):
    return {"event": "labeled", "label": {"name": name}, "created_at": ts}


def unlabeled(ts, name):
    return {"event": "unlabeled", "label": {"name": name},
            "created_at": ts}


class TestGates(unittest.TestCase):
    def test_the_three_gates_are_named_in_pipeline_order(self):
        self.assertEqual([gate[0] for gate in GATES],
                         ["prd", "blueprint", "merge"])

    def test_a_gate_names_its_queue_its_pass_label_and_its_heading(self):
        self.assertEqual(GATES[0],
                         ("prd", "wo:draft", "wo:prd-approved", "PRD gate"))

    def test_the_prd_gates_pass_label_is_the_blueprint_gates_queue(self):
        # six label slots across the three gates, five distinct labels:
        # passing the PRD gate is entering the blueprint gate's queue
        self.assertEqual(GATES[0][2], GATES[1][1])


class TestLabelEvents(unittest.TestCase):
    def test_keeps_only_label_flips_in_timeline_order(self):
        timeline = [
            {"event": "commented", "created_at": "2026-07-01T09:00:00Z"},
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            {"event": "labeled", "label": {}},
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
        ]
        self.assertEqual(label_events(timeline), [
            ("2026-07-01T09:00:00Z", "labeled", "wo:draft"),
            ("2026-07-02T09:00:00Z", "unlabeled", "wo:draft"),
        ])

    def test_an_empty_timeline_yields_no_events(self):
        self.assertEqual(label_events([]), [])


class TestGatePassages(unittest.TestCase):
    def test_a_confirmed_flip_is_a_passage(self):
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            labeled("2026-07-02T09:00:00Z", "wo:prd-approved"),
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
        ])
        self.assertEqual(gate_passages(events),
                         [("prd", 86400, "2026-07-02T09:00:00Z")])

    def test_a_flip_to_anything_but_the_pass_label_is_not_a_passage(self):
        # wo:draft -> wo:blocked is a rejection, not a PRD-gate pass.
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            unlabeled("2026-07-03T09:00:00Z", "wo:draft"),
            labeled("2026-07-03T09:00:00Z", "wo:blocked"),
        ])
        self.assertEqual(gate_passages(events), [])

    def test_a_rejected_stay_is_not_confirmed_by_a_later_pass(self):
        # First stay ends in wo:blocked (rejection); the gate is re-entered
        # and passed later. Only the second stay is a passage — the later
        # confirmation must not reach back past the re-entry.
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
            labeled("2026-07-02T09:00:00Z", "wo:blocked"),
            labeled("2026-07-05T09:00:00Z", "wo:draft"),
            labeled("2026-07-06T09:00:00Z", "wo:prd-approved"),
            unlabeled("2026-07-06T09:00:00Z", "wo:draft"),
        ])
        self.assertEqual(gate_passages(events),
                         [("prd", 86400, "2026-07-06T09:00:00Z")])

    def test_a_re_entered_gate_yields_one_passage_per_pair(self):
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:needs-review"),
            unlabeled("2026-07-01T10:00:00Z", "wo:needs-review"),
            labeled("2026-07-01T10:00:00Z", "wo:merged"),
            labeled("2026-07-05T09:00:00Z", "wo:needs-review"),
            unlabeled("2026-07-05T11:00:00Z", "wo:needs-review"),
            labeled("2026-07-05T11:00:00Z", "wo:merged"),
        ])
        self.assertEqual(gate_passages(events), [
            ("merge", 3600, "2026-07-01T10:00:00Z"),
            ("merge", 7200, "2026-07-05T11:00:00Z"),
        ])


REJECTED_STAY = [
    labeled("2026-08-10T09:00:00Z", "wo:needs-review"),
    unlabeled("2026-08-11T09:00:00Z", "wo:needs-review"),
    labeled("2026-08-11T09:00:00Z", "wo:failed"),
]

CONFIRMED_STAY = [
    labeled("2026-08-10T09:00:00Z", "wo:needs-review"),
    unlabeled("2026-08-11T09:00:00Z", "wo:needs-review"),
    labeled("2026-08-11T09:00:00Z", "wo:merged"),
]


class TestGateRejections(unittest.TestCase):
    def test_a_stay_ending_without_the_pass_label_is_a_rejection(self):
        self.assertEqual(gate_rejections(label_events(REJECTED_STAY)),
                         [("merge", "2026-08-11T09:00:00Z")])

    def test_a_confirmed_passage_is_not_a_rejection(self):
        self.assertEqual(gate_rejections(label_events(CONFIRMED_STAY)), [])

    def test_an_open_stay_is_still_waiting_not_rejected(self):
        events = label_events([
            labeled("2026-08-10T09:00:00Z", "wo:needs-review")])
        self.assertEqual(gate_rejections(events), [])

    def test_a_rejected_stay_then_a_passed_reentry_mines_one(self):
        events = label_events(REJECTED_STAY + [
            labeled("2026-08-12T09:00:00Z", "wo:needs-review"),
            unlabeled("2026-08-13T09:00:00Z", "wo:needs-review"),
            labeled("2026-08-13T09:00:00Z", "wo:merged"),
        ])
        self.assertEqual(gate_rejections(events),
                         [("merge", "2026-08-11T09:00:00Z")])


# One issue's whole gate history, hand-written so the completed stays can
# be read off it by eye: the PRD gate entered, rejected into wo:blocked,
# re-entered and passed; the blueprint gate entered by that pass and never
# left; the merge gate entered and passed.
PARTITION_HISTORY = [
    labeled("2026-08-01T09:00:00Z", "wo:draft"),
    unlabeled("2026-08-02T09:00:00Z", "wo:draft"),
    labeled("2026-08-02T09:00:00Z", "wo:blocked"),
    labeled("2026-08-03T09:00:00Z", "wo:draft"),
    labeled("2026-08-04T09:00:00Z", "wo:prd-approved"),
    unlabeled("2026-08-04T09:00:00Z", "wo:draft"),
    labeled("2026-08-06T09:00:00Z", "wo:needs-review"),
    unlabeled("2026-08-07T09:00:00Z", "wo:needs-review"),
    labeled("2026-08-07T09:00:00Z", "wo:merged"),
]

# Every stay above that was entered AND left, as (gate, ended at). The
# blueprint stay is absent: wo:prd-approved goes on at 08-04 and never
# comes off, so that stay is still open.
COMPLETED_STAYS = {
    ("prd", "2026-08-02T09:00:00Z"),
    ("prd", "2026-08-04T09:00:00Z"),
    ("merge", "2026-08-07T09:00:00Z"),
}


class TestThePartition(unittest.TestCase):
    """The invariant that joins the digest and the miner: a completed
    stay is confirmed or it is not, so the two of them divide one list
    between them. Nothing executes this today — it is a sentence in a
    docstring, and the window test it describes is spelled two ways."""

    def stays(self):
        events = label_events(PARTITION_HISTORY)
        passed = {(gate, end) for gate, _, end in gate_passages(events)}
        rejected = set(gate_rejections(events))
        return passed, rejected

    def test_together_they_are_exactly_the_completed_stays(self):
        passed, rejected = self.stays()
        self.assertEqual(passed | rejected, COMPLETED_STAYS)

    def test_no_stay_is_both_a_passage_and_a_rejection(self):
        passed, rejected = self.stays()
        self.assertEqual(passed & rejected, set())

    def test_an_open_stay_is_in_neither_half(self):
        passed, rejected = self.stays()
        self.assertEqual([gate for gate, _ in passed | rejected].count(
            "blueprint"), 0)


class TestWaitingSince(unittest.TestCase):
    def test_a_still_applied_queue_label_reports_its_timestamp(self):
        events = label_events([
            labeled("2026-07-20T09:00:00Z", "wo:draft"),
        ])
        self.assertEqual(waiting_since(events, "wo:draft"),
                         "2026-07-20T09:00:00Z")

    def test_a_removed_or_never_applied_label_is_none(self):
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
        ])
        self.assertIsNone(waiting_since(events, "wo:draft"))
        self.assertIsNone(waiting_since([], "wo:draft"))

    def test_a_re_applied_label_reports_the_current_stay(self):
        events = label_events(PARTITION_HISTORY)
        self.assertEqual(waiting_since(events, "wo:draft"), None)
        self.assertEqual(waiting_since(events, "wo:prd-approved"),
                         "2026-08-04T09:00:00Z")


if __name__ == "__main__":
    unittest.main()
