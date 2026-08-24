"""plane_drift.py — ADR-0032's cross-plane check, at its own interface.

The rule two tools read: sweeps files it as an intake, the dashboard
renders it. Pure — the listing comes in as data, so no test here needs a
runner. Coverage moved from tests/test_sweeps.py (TestReconcileDrift) and
tests/test_dashboard.py (TestDrift), which each pinned one copy.
"""
import unittest

import plane_drift


def issue(number, state="OPEN", labels=()):
    """One `gh issue list --json number,state,labels` entry."""
    return {"number": number, "state": state,
            "labels": [{"name": name} for name in labels]}


def rows(*lines):
    """One breakdown's worth of rows, as reconcile_drift takes them."""
    return [("docs/features/demo/breakdown.md", list(lines))]


class TestIssueLifecycle(unittest.TestCase):
    """`issue_lifecycle` at its own interface, which it has never had.

    Its only coverage today is through `reconcile_drift`, which reaches it
    with well-formed entries — so the strictness it applies to a malformed
    one has never been asserted anywhere. Pinned here BEFORE the walk is
    replaced, so what survives the replacement is a measurement rather
    than a claim."""

    def test_wo_labels_come_back_sorted(self):
        self.assertEqual(
            plane_drift.issue_lifecycle(
                issue(1, labels=("wo:merged", "wo:in-progress"))),
            ["wo:in-progress", "wo:merged"])

    def test_a_label_outside_the_lifecycle_prefix_is_dropped(self):
        self.assertEqual(
            plane_drift.issue_lifecycle(
                issue(1, labels=("size:M", "wo:merged", "bug"))),
            ["wo:merged"])

    def test_a_duplicate_lifecycle_label_survives(self):
        # reconcile_drift counts these to report an issue carrying more
        # than one lifecycle label at once, so deduplicating here would
        # silence that line.
        self.assertEqual(
            plane_drift.issue_lifecycle(
                issue(1, labels=("wo:merged", "wo:merged"))),
            ["wo:merged", "wo:merged"])

    def test_the_prefix_test_is_case_sensitive(self):
        self.assertEqual(
            plane_drift.issue_lifecycle(issue(1, labels=("WO:MERGED",))), [])

    def test_an_entry_that_is_not_an_object_contributes_nothing(self):
        self.assertEqual(plane_drift.issue_lifecycle(
            {"number": 1, "labels": ["wo:merged", None, [], 7]}), [])

    def test_an_entry_with_no_usable_name_contributes_nothing(self):
        self.assertEqual(plane_drift.issue_lifecycle(
            {"number": 1, "labels": [{}, {"name": None}, {"name": 7},
                                     {"name": ""}, {"colour": "ededed"}]}),
            [])

    def test_a_usable_name_survives_beside_unusable_ones(self):
        self.assertEqual(plane_drift.issue_lifecycle(
            {"number": 1, "labels": [{}, {"name": "wo:merged"}, None]}),
            ["wo:merged"])

    def test_a_labels_key_that_is_not_a_list_is_no_labels(self):
        for labels in (None, "wo:merged", 3, {"name": "wo:merged"}):
            with self.subTest(labels=labels):
                self.assertEqual(plane_drift.issue_lifecycle(
                    {"number": 1, "labels": labels}), [])

    def test_an_absent_labels_key_is_no_labels(self):
        self.assertEqual(plane_drift.issue_lifecycle({"number": 1}), [])

    def test_an_empty_labels_array_is_no_labels(self):
        self.assertEqual(plane_drift.issue_lifecycle(
            {"number": 1, "labels": []}), [])


class TestReconcileDrift(unittest.TestCase):
    """ADR-0032's cross-plane check. The rows are authoritative in every
    comparison; a drift line says what the DISPATCH plane must be brought
    to. Pure — the listing comes in as data, so no test needs a runner."""

    ROW = ("- [ ] **WO-0004** validator.yml — size:M, blocked by: —"
           " (PRD-0001 §Solution) (tracker: #109)")
    DONE = ROW.replace("- [ ]", "- [x]")

    def drift(self, rows_, issues):
        drift, problems = plane_drift.reconcile_drift(rows_, issues)
        self.assertEqual(problems, [])
        return drift

    def test_agreeing_planes_report_nothing(self):
        self.assertEqual(
            self.drift(rows(self.DONE),
                       [issue(109, "CLOSED", ["wo:merged"])]), [])
        self.assertEqual(
            self.drift(rows(self.ROW),
                       [issue(109, "OPEN", ["wo:in-progress"])]), [])

    def test_a_checked_row_whose_issue_is_not_merged(self):
        self.assertEqual(
            self.drift(rows(self.DONE),
                       [issue(109, "OPEN", ["wo:in-progress"])]),
            ["docs/features/demo/breakdown.md: a checked row mirrors #109,"
             " which carries wo:in-progress — the row says merged"])

    def test_a_checked_row_whose_merged_issue_is_still_open(self):
        self.assertEqual(
            self.drift(rows(self.DONE), [issue(109, "OPEN", ["wo:merged"])]),
            ["docs/features/demo/breakdown.md: a checked row mirrors #109,"
             " which is labelled wo:merged but still open"])

    def test_an_unchecked_row_whose_issue_says_merged(self):
        self.assertEqual(
            self.drift(rows(self.ROW),
                       [issue(109, "CLOSED", ["wo:merged"])]),
            ["docs/features/demo/breakdown.md: an unchecked row mirrors"
             " #109, which is labelled wo:merged — the issue is ahead of"
             " the row"])

    def test_an_unchecked_row_whose_issue_was_closed(self):
        """The symmetric case to the checked-row pair above. For a checked
        row the sweep judged BOTH the label and the state; for an unchecked
        row it judged only the label, so an issue closed under any
        non-merged label — the state WO-0018/#123 is actually in — read as
        agreement. The knowledge plane stays authoritative: the row says
        the work is outstanding, so closing the issue is the drift."""
        self.assertEqual(
            self.drift(rows(self.ROW), [issue(109, "CLOSED", ["wo:draft"])]),
            ["docs/features/demo/breakdown.md: an unchecked row mirrors"
             " #109, which is closed carrying wo:draft — the row says the"
             " work is outstanding"])

    def test_an_unchecked_row_whose_issue_was_closed_unlabelled(self):
        self.assertEqual(
            self.drift(rows(self.ROW), [issue(109, "CLOSED", [])]),
            ["docs/features/demo/breakdown.md: an unchecked row mirrors"
             " #109, which is closed carrying no wo: label — the row says"
             " the work is outstanding"])

    def test_an_unchecked_row_whose_issue_is_merely_open_is_agreement(self):
        """The guard is CLOSED, not "any non-merged label": an open issue
        mid-flight is exactly what an unchecked row should mirror, and
        flagging it would make the sweep noise on every live work order."""
        for labels in ([], ["wo:draft"], ["wo:in-progress"],
                       ["wo:ready-for-agent"], ["wo:needs-review"]):
            with self.subTest(labels=labels):
                self.assertEqual(
                    self.drift(rows(self.ROW), [issue(109, "OPEN", labels)]),
                    [])

    def test_a_row_mirroring_an_issue_that_is_not_there(self):
        self.assertEqual(
            self.drift(rows(self.ROW), [issue(7)]),
            ["docs/features/demo/breakdown.md: a row mirrors #109, which is"
             " not in the issue listing"])

    def test_two_rows_mirroring_one_issue(self):
        other = self.ROW.replace("WO-0004", "WO-0005")
        drift = self.drift(rows(self.ROW, other),
                           [issue(109, "OPEN", ["wo:in-progress"])])
        self.assertEqual(drift, [
            "#109 is mirrored by 2 rows (docs/features/demo/breakdown.md)"
            " — an issue mirrors one work order"])

    def test_an_issue_on_two_lifecycle_labels_at_once(self):
        self.assertEqual(
            self.drift(rows(self.ROW),
                       [issue(109, "OPEN", ["wo:in-progress",
                                            "wo:needs-review"])]),
            ["#109 carries 2 lifecycle labels at once (wo:in-progress,"
             " wo:needs-review) — the state machine allows one"])

    def test_a_work_order_issue_no_row_mirrors(self):
        # ADR-0032's headline failure: the dispatch plane running ahead of
        # the knowledge plane.
        self.assertEqual(
            self.drift(rows(self.ROW),
                       [issue(109, "OPEN", ["wo:in-progress"]),
                        issue(200, "OPEN", ["wo:ready-for-agent"])]),
            ["#200 carries wo:ready-for-agent but no breakdown row mirrors"
             " it — the dispatch plane is ahead of the knowledge plane"])

    def test_intake_issues_are_not_drift(self):
        # A sweep's own intake and the pinned digest carry no wo: label, so
        # the "no row mirrors it" check must pass straight over them.
        self.assertEqual(
            self.drift(rows(self.ROW),
                       [issue(109, "OPEN", ["wo:in-progress"]),
                        issue(300, "OPEN", ["source:sweep", "type:chore"])]),
            [])

    def test_a_row_with_no_tracker_marker_is_not_compared(self):
        self.assertEqual(
            self.drift(rows("- [x] **WO-0007** unmirrored (PRD-0001 §S)"),
                       []), [])

    def test_a_notes_line_naming_an_issue_is_not_a_row(self):
        self.assertEqual(
            self.drift(rows("- 2026-07-12: a note about (tracker: #109)"),
                       []), [])

    def test_a_listing_entry_without_a_number_is_a_problem(self):
        drift, problems = plane_drift.reconcile_drift(
            rows(self.ROW), [{"state": "OPEN", "labels": []},
                             issue(109, "OPEN", ["wo:in-progress"])])
        self.assertEqual(drift, [])
        self.assertEqual(problems, [
            "drift: issue listing entry 0 has no usable number"])

class TestAbsencePolicy(unittest.TestCase):
    """The one thing the two callers legitimately disagree about, made an
    argument instead of a second implementation."""

    ROW = ("- [ ] **WO-0004** validator.yml — size:M, blocked by: —"
           " (PRD-0001 §Solution) (tracker: #109)")
    DONE = ROW.replace("- [ ]", "- [x]")

    def test_absence_is_drift_when_the_caller_vouches_for_the_listing(self):
        # sweeps.live_issues ABORTS on a truncated window, so a row whose
        # mirror is missing means the issue is really gone. The default.
        drift, problems = plane_drift.reconcile_drift(rows(self.ROW), [])
        self.assertEqual(drift, [
            "docs/features/demo/breakdown.md: a row mirrors #109, which is"
            " not in the issue listing"])
        self.assertEqual(problems, [])

    def test_absence_says_nothing_when_the_caller_does_not(self):
        # The dashboard reports truncation and reads on, so it cannot tell
        # "gone" from "past the window" and declines to guess.
        drift, problems = plane_drift.reconcile_drift(
            rows(self.ROW), [], absent_is_drift=False)
        self.assertEqual(drift, [])
        self.assertEqual(problems, [])

    def test_the_policy_gates_only_the_membership_check(self):
        # Everything else still fires under the conservative policy: a
        # LISTED issue is a definite fact whatever the window hid.
        drift, _ = plane_drift.reconcile_drift(
            rows(self.DONE), [issue(109, "OPEN", [])], absent_is_drift=False)
        self.assertEqual(drift, [
            "docs/features/demo/breakdown.md: a checked row mirrors #109,"
            " which carries no wo: label — the row says merged"])

    def test_the_conservative_policy_still_sees_the_reverse_direction(self):
        drift, _ = plane_drift.reconcile_drift(
            [("docs/features/demo/breakdown.md", [])],
            [issue(109, "OPEN", ["wo:needs-review"])], absent_is_drift=False)
        self.assertEqual(drift, [
            "#109 carries wo:needs-review but no breakdown row mirrors it"
            " — the dispatch plane is ahead of the knowledge plane"])


if __name__ == "__main__":
    unittest.main()
