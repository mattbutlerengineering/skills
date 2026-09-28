"""human_gates.py (ADR-0056) — the three gates and one issue's gate
history.

The suite was written at this interface before it existed, against the
copies inside gate_digest.py and rejection_mining.py; re-pointing it
here changed the import lines and nothing else, which is what makes it
the net for the move rather than a restatement of it.

What it owns that neither tool's suite had: the partition property. For
one event history, the passages and the rejections together are exactly
the completed stays, and no stay is in both. That invariant lived as
prose in a docstring, so nothing caught the day the two hand-written
window tests stopped agreeing — now there is one window test, in
completed_stays, and this asserts what it guarantees.
"""
import unittest

from human_gates import (GATES, completed_stays, gate_labels,
                         gate_passages, gate_rejections, label_events,
                         refused_timestamps, waited_seconds, waiting_since)


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

    def test_a_gate_row_names_its_fields(self):
        """Why the row is a namedtuple: detector J asks for the labels by
        name instead of slicing gate[1:3], and the three sites that
        iterate the rows keep unpacking them positionally."""
        prd = GATES[0]
        self.assertEqual((prd.name, prd.queue, prd.passed, prd.heading),
                         tuple(prd))


class TestGateLabels(unittest.TestCase):
    def test_every_label_the_gates_name_five_distinct_of_six(self):
        self.assertEqual(gate_labels(),
                         {"wo:draft", "wo:prd-approved",
                          "wo:blueprint-approved", "wo:needs-review",
                          "wo:merged"})

    def test_it_is_the_queue_and_pass_labels_of_every_gate(self):
        for gate in GATES:
            with self.subTest(gate=gate.name):
                self.assertIn(gate.queue, gate_labels())
                self.assertIn(gate.passed, gate_labels())


class TestWaitedSeconds(unittest.TestCase):
    def test_whole_seconds_between_two_github_timestamps(self):
        self.assertEqual(waited_seconds("2026-07-01T09:00:00Z",
                                        "2026-07-02T09:00:00Z"), 86400)

    def test_the_z_suffix_is_read_on_every_supported_python(self):
        # fromisoformat accepts Z only from 3.11; the replace is why this
        # runs the same on 3.9
        self.assertEqual(waited_seconds("2026-07-01T09:00:00Z",
                                        "2026-07-01T09:00:00+00:00"), 0)


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

    def test_a_timestamp_that_is_not_one_is_not_a_well_formed_flip(self):
        # A truthy created_at is not enough: waited_seconds parses it as
        # ISO-8601, so a string that cannot parse is exactly as unusable
        # as a missing one. The drop rule covers all three.
        timeline = [
            labeled("2026-08-01T00:00:00Z", "wo:draft"),
            unlabeled("yesterday", "wo:draft"),
        ]
        self.assertEqual(label_events(timeline), [
            ("2026-08-01T00:00:00Z", "labeled", "wo:draft"),
        ])

    def test_a_malformed_timestamp_does_not_reach_the_parse(self):
        # The crash the drop rule prevents, at the caller that hit it:
        # only a completed, CONFIRMED stay reaches waited_seconds, so
        # this timeline needs all three flips to reproduce it.
        events = label_events([
            labeled("2026-08-01T00:00:00Z", "wo:draft"),
            labeled("2026-08-02T00:00:00Z", "wo:prd-approved"),
            unlabeled("yesterday", "wo:draft"),
        ])
        self.assertEqual(gate_passages(events), [])

    def test_a_naive_timestamp_is_not_one_either(self):
        # "2026-08-01" parses, to a datetime with no tzinfo. Subtracting
        # it from an aware one raises TypeError, so parseability alone
        # is not the precondition waited_seconds actually needs — the
        # gate has to admit only aware timestamps.
        events = label_events([
            labeled("2026-08-01", "wo:draft"),
            labeled("2026-08-02T00:00:00Z", "wo:prd-approved"),
            unlabeled("2026-08-02T00:00:00Z", "wo:draft"),
        ])
        self.assertNotIn("2026-08-01", [ts for ts, _, _ in events])
        self.assertEqual(gate_passages(events), [])

    def test_a_well_formed_timeline_is_unchanged_by_the_third_clause(self):
        # The same three flips with a parseable closing timestamp still
        # pass the gate — the guard rejects malformed input, not input.
        events = label_events([
            labeled("2026-08-01T00:00:00Z", "wo:draft"),
            labeled("2026-08-02T00:00:00Z", "wo:prd-approved"),
            unlabeled("2026-08-02T00:00:00Z", "wo:draft"),
        ])
        self.assertEqual(gate_passages(events),
                         [("prd", 86400, "2026-08-02T00:00:00Z")])


class TestRefusedTimestamps(unittest.TestCase):
    """#491: label_events' third clause drops a malformed timestamp
    silently — no crash (#326), but no count either. refused_timestamps
    answers the count a gd:/dashboard: problem string needs, over the
    same raw timeline, without label_events itself growing a problems
    channel."""

    def test_a_malformed_timestamp_is_refused(self):
        timeline = [
            labeled("2026-08-01T00:00:00Z", "wo:draft"),
            unlabeled("yesterday", "wo:draft"),
        ]
        self.assertEqual(refused_timestamps(timeline), 1)

    def test_a_well_formed_timeline_refuses_nothing(self):
        timeline = [
            labeled("2026-08-01T00:00:00Z", "wo:draft"),
            unlabeled("2026-08-02T00:00:00Z", "wo:draft"),
        ]
        self.assertEqual(refused_timestamps(timeline), 0)

    def test_a_naive_timestamp_is_refused_by_the_same_second_clause(self):
        # "2026-08-01" parses but carries no UTC offset — label_events
        # drops it on _is_timestamp's second clause, so it counts here
        # too, not just the unparseable case.
        timeline = [labeled("2026-08-01", "wo:draft")]
        self.assertEqual(refused_timestamps(timeline), 1)

    def test_a_nameless_flip_is_not_a_refused_timestamp(self):
        # Dropped by the first clause (no name), not the third — a
        # different reason, so it must not inflate this count.
        timeline = [{"event": "labeled", "label": {}}]
        self.assertEqual(refused_timestamps(timeline), 0)

    def test_a_non_flip_event_is_not_a_refused_timestamp(self):
        timeline = [{"event": "commented",
                     "created_at": "not-a-timestamp"}]
        self.assertEqual(refused_timestamps(timeline), 0)

    def test_the_refused_count_never_shows_up_in_label_events(self):
        timeline = [
            labeled("2026-08-01T00:00:00Z", "wo:draft"),
            unlabeled("yesterday", "wo:draft"),
        ]
        self.assertEqual(label_events(timeline),
                         [("2026-08-01T00:00:00Z", "labeled", "wo:draft")])
        self.assertEqual(refused_timestamps(timeline), 1)


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


    def test_an_added_pass_label_ends_the_stay_it_confirms(self):
        """#536's real history (bead wo-ldf): the owner added each pass
        label without removing the queue label, and the claim stripped
        both 15-19s later. The wait is the human's, so each stay ends at
        its pass label, not at the automation's later removal."""
        events = label_events([
            labeled("2026-09-24T04:08:31Z", "wo:draft"),
            labeled("2026-09-24T04:31:31Z", "wo:prd-approved"),
            labeled("2026-09-24T04:31:35Z", "wo:blueprint-approved"),
            unlabeled("2026-09-24T04:31:50Z", "wo:draft"),
            unlabeled("2026-09-24T04:31:50Z", "wo:prd-approved"),
        ])
        self.assertEqual(gate_passages(events), [
            ("prd", 1380, "2026-09-24T04:31:31Z"),
            ("blueprint", 4, "2026-09-24T04:31:35Z"),
        ])

    def test_a_lingering_queue_label_cannot_fold_in_the_next_gate(self):
        # PRD passed on day 2, blueprint on day 9, both queue labels
        # stripped on day 9: the PRD wait is one day, not eight.
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            labeled("2026-07-02T09:00:00Z", "wo:prd-approved"),
            labeled("2026-07-09T09:00:00Z", "wo:blueprint-approved"),
            unlabeled("2026-07-09T09:00:10Z", "wo:draft"),
            unlabeled("2026-07-09T09:00:10Z", "wo:prd-approved"),
        ])
        self.assertEqual(gate_passages(events)[0],
                         ("prd", 86400, "2026-07-02T09:00:00Z"))

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


class TestCompletedStays(unittest.TestCase):
    """One walk and one window test, returning the list the digest and
    the miner divide between them."""

    PRD = GATES[0]

    def test_a_pass_label_inside_the_window_confirms_the_stay(self):
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            labeled("2026-07-02T09:00:00Z", "wo:prd-approved"),
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
        ])
        self.assertEqual(completed_stays(events, self.PRD),
                         [("2026-07-01T09:00:00Z",
                           "2026-07-02T09:00:00Z", True)])

    def test_a_confirmation_past_the_next_re_entry_confirms_nothing(self):
        # the window runs from a stay's start up to the gate's next
        # re-entry, so the second stay's pass cannot reach back
        events = label_events(PARTITION_HISTORY)
        self.assertEqual(completed_stays(events, self.PRD), [
            ("2026-08-01T09:00:00Z", "2026-08-02T09:00:00Z", False),
            ("2026-08-03T09:00:00Z", "2026-08-04T09:00:00Z", True),
        ])

    def test_an_open_stay_is_absent_still_waiting(self):
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft")])
        self.assertEqual(completed_stays(events, self.PRD), [])

    def test_an_empty_history_yields_no_stays(self):
        self.assertEqual(completed_stays([], self.PRD), [])


class TestThePartition(unittest.TestCase):
    """The invariant that joins the digest and the miner: a completed
    stay is confirmed or it is not, so the two of them divide one list
    between them. This class is what executes it, and the window test it
    describes now has one spelling to execute."""

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
