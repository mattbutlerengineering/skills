"""human_gates.py (ADR-0056) — the three gates and one issue's gate
history.

The suite was written at this interface before it existed, against the
copies inside gate_digest.py and rejection_mining.py; re-pointing it
here changed the import lines and nothing else, which is what makes it
the net for the move rather than a restatement of it.

What it owns that neither tool's suite had: the partition property. For
one event history, the passages, the rejections and the bypasses
(ADR-0137) together are exactly the completed stays, and no stay is in
two of them. That invariant lived as
prose in a docstring, so nothing caught the day the two hand-written
window tests stopped agreeing — now there is one window test, in
completed_stays, and this asserts what it guarantees.
"""
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling helper import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_gh import FakeGh  # noqa: E402
import cost_ledger  # noqa: E402
from human_gates import (BYPASSED, GATES, PASSED, REJECTED, Waiting,
                         completed_stays, gate_bypasses, gate_labels,
                         gate_passages, gate_rejections, label_events,
                         open_queues, read_gate_issues, read_labelers,
                         read_timelines,
                         read_work_order_issues, waited_seconds,
                         waiting_issues, waiting_since)


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

    def test_an_admitted_timestamp_is_normalised_to_utc_z_form(self):
        # A ledger row's `at` is the first ten characters of a timestamp
        # and its run_id embeds one: an offset form would date the row by
        # its local day and key one instant two ways.
        events = label_events([
            labeled("2026-07-31T21:00:00-05:00", "wo:draft"),
            labeled("2026-08-01T02:00:00.750000+00:00", "wo:prd-approved"),
        ])
        self.assertEqual([ts for ts, _, _ in events],
                         ["2026-08-01T02:00:00Z", "2026-08-01T02:00:00Z"])

    @unittest.skipIf(sys.version_info < (3, 11),
                     "fromisoformat reads the basic format from 3.11")
    def test_a_basic_format_timestamp_becomes_a_row_the_ledger_takes(self):
        # Admitted verbatim, 20260801T110000Z gave gate_entry at
        # '20260801T1', which line_problems refuses — and record_new
        # refuses the whole batch on every later run, since timelines
        # never change.
        events = label_events([
            labeled("20260801T100000Z", "wo:draft"),
            labeled("20260801T110000Z", "wo:prd-approved"),
            unlabeled("20260801T110000Z", "wo:draft"),
        ])
        (gate, waited, passed_at, started_at), = gate_passages(events)
        row = cost_ledger.gate_entry("WO-0001", gate, waited, passed_at,
                                     started_at)
        self.assertEqual(cost_ledger.line_problems(row), [])
        self.assertEqual(row["at"], "2026-08-01")

    def test_a_well_formed_timeline_is_unchanged_by_the_third_clause(self):
        # The same three flips with a parseable closing timestamp still
        # pass the gate — the guard rejects malformed input, not input.
        events = label_events([
            labeled("2026-08-01T00:00:00Z", "wo:draft"),
            labeled("2026-08-02T00:00:00Z", "wo:prd-approved"),
            unlabeled("2026-08-02T00:00:00Z", "wo:draft"),
        ])
        self.assertEqual(gate_passages(events),
                         [("prd", 86400, "2026-08-02T00:00:00Z",
                          "2026-08-01T00:00:00Z")])


def timeline_gh(pages_by_issue=None, **kwargs):
    """A FakeGh answering every timeline read in --slurp's
    array-of-pages shape; pages_by_issue maps an issue number to its
    pages, and an issue it does not name answers one empty page."""
    canned = pages_by_issue or {}

    def timeline(args):
        number = int(args[1].split("/")[-2])
        return json.dumps(canned.get(number, [[]]))

    return FakeGh(answers={("api",): timeline}, **kwargs)


class TestReadTimelines(unittest.TestCase):
    """#740 (ADR-0090): the one timeline read — fetch, flatten the
    pages, admit the label events, and say what admission refused —
    behind the injected gh port, so no caller can take half of it. The
    #491 refusal used to be a second call each caller had to remember;
    rejection_mining forgot it (#791)."""

    def test_pages_are_flattened_into_one_event_list(self):
        run = timeline_gh({7: [
            [labeled("2026-08-01T00:00:00Z", "wo:draft")],
            [unlabeled("2026-08-02T00:00:00Z", "wo:draft")],
        ]})
        events, problems = read_timelines([7], run, "gd")
        self.assertEqual(problems, [])
        self.assertEqual(events, {7: [
            ("2026-08-01T00:00:00Z", "labeled", "wo:draft"),
            ("2026-08-02T00:00:00Z", "unlabeled", "wo:draft"),
        ]})

    def test_the_read_goes_through_the_slug_paginated_and_slurped(self):
        run = timeline_gh()
        read_timelines([7], run, "dashboard", slug="o/r")
        read_timelines([8], run, "gd")
        self.assertEqual(run.calls, [
            ["api", "repos/o/r/issues/7/timeline", "--paginate",
             "--slurp"],
            ["api", "repos/{owner}/{repo}/issues/8/timeline",
             "--paginate", "--slurp"],
        ])

    def test_a_read_timeline_with_no_events_is_present_and_empty(self):
        self.assertEqual(read_timelines([7], timeline_gh(), "gd"),
                         ({7: []}, []))

    def test_a_failed_fetch_is_absent_and_a_labelled_problem(self):
        events, problems = read_timelines(
            [7, 8], timeline_gh(failing=["api"]), "rm")
        self.assertEqual(events, {})
        self.assertEqual(problems, [
            "rm: gh api timeline for #7 failed: boom",
            "rm: gh api timeline for #8 failed: boom"])

    def test_an_unparseable_timeline_is_absent_not_empty(self):
        events, problems = read_timelines(
            [7], FakeGh(answers={("api",): "not json"}), "dashboard")
        self.assertEqual(events, {})
        self.assertEqual(problems, [
            "dashboard: gh api timeline for #7 returned unparseable JSON:"
            " Expecting value: line 1 column 1 (char 0)"])

    def test_a_refused_timestamp_is_a_problem_under_every_label(self):
        run = timeline_gh({7: [[
            labeled("2026-08-01T00:00:00Z", "wo:draft"),
            unlabeled("yesterday", "wo:draft"),
        ]]})
        for label in ("gd", "rm", "dashboard"):
            events, problems = read_timelines([7], run, label)
            self.assertEqual(problems, [
                f"{label}: timeline for #7 refused 1 malformed"
                " timestamp(s)"])
            # the refused event never reaches the walk
            self.assertEqual(events, {7: [
                ("2026-08-01T00:00:00Z", "labeled", "wo:draft")]})

    def test_a_naive_timestamp_is_refused_by_the_same_second_clause(self):
        # "2026-08-01" parses but carries no UTC offset — admission
        # drops it on _is_timestamp's second clause, so it is reported
        # too, not just the unparseable case.
        run = timeline_gh({7: [[labeled("2026-08-01", "wo:draft")]]})
        self.assertEqual(read_timelines([7], run, "gd")[1], [
            "gd: timeline for #7 refused 1 malformed timestamp(s)"])

    def test_a_nameless_flip_or_a_non_flip_is_not_a_refusal(self):
        # Dropped by the first clause or not a flip at all — a
        # different reason, so it must not raise this problem.
        run = timeline_gh({7: [[
            {"event": "labeled", "label": {}},
            {"event": "commented", "created_at": "not-a-timestamp"},
        ]]})
        self.assertEqual(read_timelines([7], run, "gd"), ({7: []}, []))

    def test_a_dropped_unlabeled_event_is_surfaced_to_the_miner(self):
        """#740's defect at the interface: drop the `unlabeled` closing
        a rejected stay and the rejection is lost, so the reader must
        say so to every caller, the miner included."""
        run = timeline_gh({7: [[
            labeled("2026-08-10T09:00:00Z", "wo:needs-review"),
            unlabeled("not-a-timestamp", "wo:needs-review"),
            labeled("2026-08-11T09:00:00Z", "wo:failed"),
        ]]})
        events, problems = read_timelines([7], run, "rm")
        self.assertEqual(gate_rejections(events[7]), [])
        self.assertEqual(problems, [
            "rm: timeline for #7 refused 1 malformed timestamp(s)"])


def labeled_by(ts, name, login):
    return {**labeled(ts, name), "actor": {"login": login}}


class TestReadLabelers(unittest.TestCase):
    """Who applied a label most recently, through read_timelines' own
    read and admission (ADR-0090) — the dispatch plane's owner-only
    ready label (ADR-0032) is a question about the latest labeled
    event's actor, and an unreadable timeline must never answer it."""

    def test_the_latest_labeled_event_names_the_labeler(self):
        run = timeline_gh({7: [[
            labeled_by("2026-08-01T00:00:00Z", "wo:ready-for-agent", "o"),
            unlabeled("2026-08-02T00:00:00Z", "wo:ready-for-agent"),
        ], [
            labeled_by("2026-08-03T00:00:00Z", "wo:ready-for-agent",
                       "drive-by"),
            labeled_by("2026-08-04T00:00:00Z", "wo:draft", "o"),
        ]]})
        self.assertEqual(
            read_labelers([7], "wo:ready-for-agent", run, "wq"),
            ({7: "drive-by"}, []))

    def test_a_timeline_without_the_label_answers_none(self):
        self.assertEqual(
            read_labelers([7], "wo:ready-for-agent", timeline_gh(), "wq"),
            ({7: None}, []))

    def test_an_actorless_labeled_event_answers_the_empty_name(self):
        run = timeline_gh({7: [[
            labeled("2026-08-01T00:00:00Z", "wo:ready-for-agent")]]})
        self.assertEqual(
            read_labelers([7], "wo:ready-for-agent", run, "wq"),
            ({7: ""}, []))

    def test_a_failed_fetch_is_absent_and_a_labelled_problem(self):
        self.assertEqual(
            read_labelers([7], "wo:ready-for-agent",
                          timeline_gh(failing=["api"]), "wq"),
            ({}, ["wq: gh api timeline for #7 failed: boom"]))

    def test_a_refused_timestamp_leaves_the_issue_absent(self):
        """Fail closed: a dropped flip could be the latest application,
        so a timeline admission refused anything from answers nothing."""
        run = timeline_gh({7: [[
            labeled_by("2026-08-01T00:00:00Z", "wo:ready-for-agent", "o"),
            labeled_by("yesterday", "wo:ready-for-agent", "drive-by"),
        ]]})
        self.assertEqual(
            read_labelers([7], "wo:ready-for-agent", run, "wq"),
            ({}, ["wq: timeline for #7 refused 1 malformed timestamp(s)"]))


NOW = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)


def open_issue(number, *labels):
    return {"number": number, "title": f"WO #{number}", "state": "OPEN",
            "labels": [{"name": name} for name in labels]}


class TestReadGateIssues(unittest.TestCase):
    """The listing and its mirrored issues' timelines: the startup the
    gate digest and the rejection miner shared as two copies (the
    2026-10-25 consolidation)."""

    LISTING = [{"number": 3, "state": "OPEN", "body": ""},
               {"number": 5, "state": "CLOSED", "body": ""},
               {"number": 8, "state": "OPEN", "body": ""}]

    def gh(self, **kwargs):
        def timeline(args):
            return json.dumps([[]])
        return FakeGh(answers={("label", "list"): json.dumps(
                                   [{"name": "wo:merged"}]),
                               ("issue", "list"): json.dumps(self.LISTING),
                               ("api",): timeline}, **kwargs)

    def test_only_mirrored_issues_have_their_timelines_read(self):
        run = self.gh()
        issues = read_gate_issues({3: "WO-0001", 5: "WO-0002"}, run, "gd")
        self.assertEqual(issues.listing, self.LISTING)
        self.assertEqual(issues.mirrored, [3, 5])
        self.assertEqual(issues.events, {3: [], 5: []})
        self.assertEqual((issues.truncated, issues.problems), (False, []))
        self.assertEqual(run.calls[1], [
            "issue", "list", "--state", "all", "--search",
            'label:"wo:merged"', "--json",
            "number,title,state,labels,body", "--limit", "1000"])

    def test_an_unreadable_listing_reads_no_timelines(self):
        run = self.gh(failing=["issue", "list"])
        issues = read_gate_issues({3: "WO-0001"}, run, "rm")
        self.assertIsNone(issues.listing)
        self.assertEqual((issues.mirrored, issues.events), ([], {}))
        self.assertEqual(len(issues.problems), 1)
        self.assertTrue(issues.problems[0].startswith("rm: gh issue list"))
        self.assertEqual(len(run.calls), 2)

    def test_a_mirrored_issue_the_search_missed_still_has_its_timeline_read(
            self):
        # #9 lost every wo: label, so the label search cannot find it —
        # but a row mirrors it, and its history still holds stays.
        run = tracker_gh([], rest={9: rest_issue(9, "closed", ["type:chore"])})
        issues = read_gate_issues({9: "WO-0003"}, run, "gd")
        self.assertEqual(issues.mirrored, [9])
        self.assertEqual(issues.events, {9: []})
        self.assertEqual(issues.problems, [])


def entry(number, state, labels):
    """An issue-list entry carrying every field the gate readers ask for."""
    return {"number": number, "title": f"issue {number}", "state": state,
            "labels": [{"name": name} for name in labels], "body": ""}


def rest_issue(number, state, labels, **extra):
    """The REST issue object `gh api repos/.../issues/N` answers with."""
    return {"number": number, "title": f"issue {number}", "state": state,
            "labels": [{"name": name, "color": "fff"} for name in labels],
            "body": "", "comments": 0, **extra}


LIVE_LABELS = [{"name": name} for name in
               ("wo:merged", "type:chore", "wo:draft", "wo:blocked")]


def tracker_gh(issues, rest=None, labels=LIVE_LABELS, failing_numbers=()):
    """A fake gh that answers the narrowed read the way GitHub does: the
    label search returns only the listed issues carrying one of the
    searched labels (comma-separated values are OR), and `gh api
    repos/.../issues/N` answers from `rest` — 404 for a number absent
    from it, a plain failure for one in `failing_numbers`."""
    def search(args):
        query = args[args.index("--search") + 1]
        assert query.startswith("label:"), query
        wanted = {name.strip('"') for name in query[6:].split(",")}
        return json.dumps([issue for issue in issues
                           if wanted & {label["name"]
                                        for label in issue["labels"]}])

    def issue_api(args):
        path = args[1]
        if path.endswith("/timeline"):
            return json.dumps([[]])
        number = int(path.rsplit("/", 1)[1])
        if number in failing_numbers:
            raise subprocess.CalledProcessError(
                1, "gh", stderr="HTTP 502: Bad Gateway\n")
        if number not in (rest or {}):
            raise subprocess.CalledProcessError(
                1, "gh", stderr="gh: Not Found (HTTP 404)\n")
        return json.dumps(rest[number])

    return FakeGh(answers={("label", "list"): json.dumps(labels),
                           ("issue", "list"): search,
                           ("api",): issue_api})


class TestReadWorkOrderIssues(unittest.TestCase):
    """The narrowed tracker read (#2205): every issue a wo:
    label marks, found by one OR search over the repo's live wo: labels,
    plus each mirrored issue that carries none, fetched by number — so a
    reader sees exactly what the whole-tracker listing showed it, without
    reading the whole tracker."""

    FIELDS = "number,state,labels"

    def test_one_search_over_every_live_wo_label(self):
        run = tracker_gh([entry(4, "OPEN", ["wo:draft"]),
                          entry(6, "OPEN", ["type:chore"])])
        read = read_work_order_issues([4], self.FIELDS, run, "sweeps")
        self.assertEqual(read.value, [entry(4, "OPEN", ["wo:draft"])])
        self.assertEqual((read.problems, read.truncated), ([], False))
        self.assertEqual(run.calls, [
            ["label", "list", "--json", "name", "--limit", "1000"],
            ["issue", "list", "--state", "all", "--search",
             'label:"wo:blocked","wo:draft","wo:merged"', "--json",
             self.FIELDS, "--limit", "1000"]])

    def test_a_named_repo_scopes_every_read_to_it(self):
        # The dashboard observes checkouts other than the one gh runs
        # in, so a slug it names must reach the label list and the
        # search as -R, not only the by-number REST path (#2212).
        run = tracker_gh([entry(4, "OPEN", ["wo:draft"])],
                         rest={7: rest_issue(7, "open", [])})
        read = read_work_order_issues([4, 7], self.FIELDS, run, "dashboard",
                                      slug="o/r")
        self.assertEqual([entry["number"] for entry in read.value], [4, 7])
        self.assertEqual(run.calls, [
            ["label", "list", "-R", "o/r", "--json", "name", "--limit",
             "1000"],
            ["issue", "list", "-R", "o/r", "--state", "all", "--search",
             'label:"wo:blocked","wo:draft","wo:merged"', "--json",
             self.FIELDS, "--limit", "1000"],
            ["api", "repos/o/r/issues/7"]])

    def test_a_mirrored_issue_with_no_wo_label_is_fetched_by_number(self):
        run = tracker_gh(
            [entry(4, "OPEN", ["wo:draft"])],
            rest={7: rest_issue(7, "closed", ["type:chore"])})
        read = read_work_order_issues([4, 7], self.FIELDS, run, "sweeps")
        self.assertEqual(read.value, [
            entry(4, "OPEN", ["wo:draft"]),
            {"number": 7, "state": "CLOSED",
             "labels": [{"name": "type:chore", "color": "fff"}]}])
        self.assertEqual(read.problems, [])
        self.assertEqual(run.calls[2],
                         ["api", "repos/{owner}/{repo}/issues/7"])

    def test_a_fetched_issue_links_to_its_page_not_the_api(self):
        run = tracker_gh([], rest={5: rest_issue(
            5, "open", [], url="https://api.github.com/repos/o/r/issues/5",
            html_url="https://github.com/o/r/issues/5")})
        read = read_work_order_issues([5], "number,url", run, "dashboard")
        self.assertEqual(read.value, [
            {"number": 5, "url": "https://github.com/o/r/issues/5"}])

    def test_every_gate_field_survives_the_fetch_by_number(self):
        run = tracker_gh([], rest={7: rest_issue(7, "open", [])})
        read = read_work_order_issues(
            [7], "number,title,state,labels,body", run, "gd")
        self.assertEqual(read.value, [{"number": 7, "title": "issue 7",
                                       "state": "OPEN", "labels": [],
                                       "body": ""}])

    def test_a_mirrored_number_that_is_no_issue_stays_absent(self):
        # The whole-tracker listing never held a missing issue, a pull
        # request, or one transferred away (answered under another
        # number), so neither does this — absence is what reconcile
        # reports as "not in the issue listing".
        run = tracker_gh([], rest={
            8: rest_issue(8, "closed", [], pull_request={"url": "x"}),
            11: rest_issue(12, "open", [])})
        read = read_work_order_issues([8, 10, 11], self.FIELDS, run, "gd")
        self.assertEqual((read.value, read.problems), ([], []))

    def test_a_failed_fetch_by_number_makes_the_listing_unusable(self):
        run = tracker_gh([], failing_numbers=(7,))
        read = read_work_order_issues([7], self.FIELDS, run, "sweeps")
        self.assertIsNone(read.value)
        self.assertEqual(read.problems, [
            "sweeps: gh api issue #7 failed: HTTP 502: Bad Gateway"])

    def test_a_repo_with_no_wo_labels_searches_nothing(self):
        run = tracker_gh([], labels=[{"name": "type:chore"}],
                         rest={7: rest_issue(7, "open", [])})
        read = read_work_order_issues([7], self.FIELDS, run, "gd")
        self.assertEqual([call[:2] for call in run.calls],
                         [["label", "list"], ["api", "repos/{owner}/{repo}/issues/7"]])
        self.assertEqual(len(read.value), 1)

    def test_an_unreadable_label_list_is_an_unusable_listing(self):
        run = FakeGh(failing=["label", "list"])
        read = read_work_order_issues([7], self.FIELDS, run, "gd")
        self.assertIsNone(read.value)
        self.assertEqual(read.problems, ["gd: gh label list failed: boom"])
        self.assertEqual(len(run.calls), 1)

    def test_a_full_search_window_is_reported_as_truncated(self):
        # GitHub search stops at 1000 results whatever --limit asks, so
        # the window IS 1000: a capped search reads as a full window
        # instead of a silently short one.
        run = tracker_gh([entry(n, "CLOSED", ["wo:merged"])
                          for n in range(1, 1001)])
        read = read_work_order_issues([], self.FIELDS, run, "gd")
        self.assertTrue(read.truncated)
        self.assertEqual(read.problems, [
            "gd: gh issue list returned a full 1000-entry window — older"
            " entries are invisible; raise the window or narrow the query"])


class TestOpenQueues(unittest.TestCase):
    """#740 (ADR-0090): the open gate queues, built once. gate_digest
    and dashboard each built them by hand, and the unreadable-age fix
    (#665) had to be made in both."""

    MIRROR = {7: "WO-0101", 8: "WO-0102", 9: "WO-0103"}

    def test_every_gate_is_listed_in_pipeline_order_even_empty(self):
        self.assertEqual(open_queues([], self.MIRROR, {}, NOW),
                         [(gate, []) for gate in GATES])

    def test_an_aged_item_is_aged_at_the_literal_now(self):
        issue = open_issue(7, "wo:draft", "size:S")
        queues = open_queues([issue], self.MIRROR, {7: [
            ("2026-08-14T10:00:00Z", "labeled", "wo:draft")]}, NOW)
        self.assertEqual(queues[0],
                         (GATES[0], [Waiting(issue, 7200, True)]))

    def test_an_unread_timeline_is_unaged_and_says_so(self):
        issue = open_issue(7, "wo:draft")
        queues = open_queues([issue], self.MIRROR, {}, NOW)
        self.assertEqual(queues[0][1], [Waiting(issue, None, False)])

    def test_a_read_timeline_with_no_arrival_is_unknown_not_unread(self):
        issue = open_issue(7, "wo:draft")
        queues = open_queues([issue], self.MIRROR, {7: []}, NOW)
        self.assertEqual(queues[0][1], [Waiting(issue, None, True)])

    def test_only_mirrored_issues_carrying_the_queue_label_wait(self):
        issues = [open_issue(9, "wo:needs-review"),
                  open_issue(8, "wo:needs-review"),
                  open_issue(7, "wo:claimed"),
                  open_issue(40, "wo:draft")]
        queues = open_queues(issues, self.MIRROR, {}, NOW)
        self.assertEqual([[w.issue["number"] for w in items]
                          for _, items in queues], [[], [], [8, 9]])

    def test_waiting_issues_names_who_open_queues_will_age(self):
        # The reads a caller must make before open_queues can age
        # anything — the same membership open_queues applies.
        issues = [open_issue(9, "wo:needs-review"),
                  open_issue(7, "wo:claimed"),
                  open_issue(8, "wo:draft", "wo:needs-review"),
                  open_issue(40, "wo:draft")]
        self.assertEqual(waiting_issues(issues, self.MIRROR), [8, 9])


class TestGatePassages(unittest.TestCase):
    def test_a_confirmed_flip_is_a_passage(self):
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            labeled("2026-07-02T09:00:00Z", "wo:prd-approved"),
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
        ])
        self.assertEqual(gate_passages(events),
                         [("prd", 86400, "2026-07-02T09:00:00Z",
                          "2026-07-01T09:00:00Z")])

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
                         [("prd", 86400, "2026-07-06T09:00:00Z",
                          "2026-07-05T09:00:00Z")])

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
            ("merge", 3600, "2026-07-01T10:00:00Z",
                          "2026-07-01T09:00:00Z"),
            ("merge", 7200, "2026-07-05T11:00:00Z",
                          "2026-07-05T09:00:00Z"),
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
            ("prd", 1380, "2026-09-24T04:31:31Z",
                          "2026-09-24T04:08:31Z"),
            ("blueprint", 4, "2026-09-24T04:31:35Z",
                          "2026-09-24T04:31:31Z"),
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
                         ("prd", 86400, "2026-07-02T09:00:00Z",
                          "2026-07-01T09:00:00Z"))

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

    # #2309 (ADR-0137): a rejection is a stay that ends in wo:failed /
    # wo:blocked or moves backward in GATES order. A forward skip past
    # the gate is neither approval nor rejection.

    def test_a_forward_skip_past_the_gate_is_not_a_rejection(self):
        # #113's live shape: wo:draft off and wo:merged on in one second
        events = label_events([
            labeled("2026-08-10T09:00:00Z", "wo:draft"),
            unlabeled("2026-08-11T09:00:00Z", "wo:draft"),
            labeled("2026-08-11T09:00:00Z", "wo:merged"),
        ])
        self.assertEqual(gate_rejections(events), [])

    def test_a_skip_to_a_label_outside_the_gates_is_not_a_rejection(self):
        events = label_events([
            labeled("2026-08-10T09:00:00Z", "wo:draft"),
            labeled("2026-08-11T09:00:00Z", "wo:in-progress"),
            unlabeled("2026-08-11T09:00:00Z", "wo:draft"),
        ])
        self.assertEqual(gate_rejections(events), [])

    def test_a_backward_move_in_gates_order_is_a_rejection(self):
        events = label_events([
            labeled("2026-08-10T09:00:00Z", "wo:needs-review"),
            unlabeled("2026-08-11T09:00:00Z", "wo:needs-review"),
            labeled("2026-08-11T09:00:00Z", "wo:prd-approved"),
        ])
        self.assertEqual(gate_rejections(events),
                         [("merge", "2026-08-11T09:00:00Z")])

    def test_a_block_added_beside_the_queue_label_is_a_rejection(self):
        # the human adds wo:blocked mid-stay; a later flip strips wo:draft
        events = label_events([
            labeled("2026-08-10T09:00:00Z", "wo:draft"),
            labeled("2026-08-11T09:00:00Z", "wo:blocked"),
            unlabeled("2026-08-12T09:00:00Z", "wo:draft"),
        ])
        self.assertEqual(gate_rejections(events),
                         [("prd", "2026-08-12T09:00:00Z")])

    def test_a_failure_applied_just_after_the_removal_is_a_rejection(self):
        # two edits, not one: the queue label off, wo:failed a minute on
        events = label_events([
            labeled("2026-08-10T09:00:00Z", "wo:needs-review"),
            unlabeled("2026-08-11T09:00:00Z", "wo:needs-review"),
            labeled("2026-08-11T09:01:00Z", "wo:failed"),
        ])
        self.assertEqual(gate_rejections(events),
                         [("merge", "2026-08-11T09:00:00Z")])

    def test_a_removal_with_no_later_lifecycle_label_is_not_a_rejection(self):
        events = label_events([
            labeled("2026-08-10T09:00:00Z", "wo:draft"),
            unlabeled("2026-08-11T09:00:00Z", "wo:draft"),
            labeled("2026-08-11T09:00:00Z", "size:S"),
        ])
        self.assertEqual(gate_rejections(events), [])


class TestGateBypasses(unittest.TestCase):
    """#2309 (ADR-0137): the third class of completed stay — left
    forward without the pass label. The miner skips it; nothing counts it
    as the human's approval either."""

    def test_a_forward_skip_is_a_bypass_of_the_gate_it_skipped(self):
        events = label_events([
            labeled("2026-08-10T09:00:00Z", "wo:draft"),
            unlabeled("2026-08-11T09:00:00Z", "wo:draft"),
            labeled("2026-08-11T09:00:00Z", "wo:merged"),
        ])
        self.assertEqual(gate_bypasses(events),
                         [("prd", "2026-08-11T09:00:00Z")])
        self.assertEqual(gate_passages(events), [])

    def test_a_rejection_or_a_passage_is_not_a_bypass(self):
        self.assertEqual(gate_bypasses(label_events(REJECTED_STAY)), [])
        self.assertEqual(gate_bypasses(label_events(CONFIRMED_STAY)), [])


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

# A PRD stay rejected into wo:blocked, a re-entered PRD stay that skips
# forward to wo:needs-review (past the blueprint gate, never entered),
# and the merge gate passed: one stay of each class.
THREE_WAY_HISTORY = [
    labeled("2026-08-01T09:00:00Z", "wo:draft"),
    unlabeled("2026-08-02T09:00:00Z", "wo:draft"),
    labeled("2026-08-02T09:00:00Z", "wo:blocked"),
    unlabeled("2026-08-03T09:00:00Z", "wo:blocked"),
    labeled("2026-08-03T09:00:00Z", "wo:draft"),
    unlabeled("2026-08-04T09:00:00Z", "wo:draft"),
    labeled("2026-08-04T09:00:00Z", "wo:needs-review"),
    unlabeled("2026-08-05T09:00:00Z", "wo:needs-review"),
    labeled("2026-08-05T09:00:00Z", "wo:merged"),
]


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
                           "2026-07-02T09:00:00Z", PASSED)])

    def test_a_confirmation_past_the_next_re_entry_confirms_nothing(self):
        # the window runs from a stay's start up to the gate's next
        # re-entry, so the second stay's pass cannot reach back
        events = label_events(PARTITION_HISTORY)
        self.assertEqual(completed_stays(events, self.PRD), [
            ("2026-08-01T09:00:00Z", "2026-08-02T09:00:00Z", REJECTED),
            ("2026-08-03T09:00:00Z", "2026-08-04T09:00:00Z", PASSED),
        ])

    def test_a_pass_label_beside_an_open_re_entered_stay_is_not_the_closed_ones(self):
        # Issue #1951: draft -> blocked (rejection) -> draft again, then
        # the pass label lands beside the open second stay.
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft"),
            labeled("2026-07-02T09:00:00Z", "wo:blocked"),
            unlabeled("2026-07-02T09:00:00Z", "wo:draft"),
            labeled("2026-07-03T09:00:00Z", "wo:draft"),
            labeled("2026-07-04T09:00:00Z", "wo:prd-approved"),
        ])
        self.assertEqual(completed_stays(events, self.PRD), [
            ("2026-07-01T09:00:00Z", "2026-07-02T09:00:00Z", REJECTED)])

    def test_a_stay_ends_at_the_earliest_instant_not_the_smallest_string(self):
        # 11:30+02:00 is 09:30Z, before the 10:00Z unlabel, though the
        # string "10:00:00Z" sorts first (#1968).
        events = label_events([
            labeled("2026-07-01T08:00:00Z", "wo:draft"),
            labeled("2026-07-01T11:30:00+02:00", "wo:prd-approved"),
            unlabeled("2026-07-01T10:00:00Z", "wo:draft"),
        ])
        # Admission normalises every timestamp to UTC Z form, so the
        # pass label reads back as the instant it is.
        self.assertEqual(completed_stays(events, self.PRD),
                         [("2026-07-01T08:00:00Z",
                           "2026-07-01T09:30:00Z", PASSED)])

    def test_a_forward_skip_is_bypassed_not_rejected(self):
        events = label_events(THREE_WAY_HISTORY)
        self.assertEqual(completed_stays(events, self.PRD), [
            ("2026-08-01T09:00:00Z", "2026-08-02T09:00:00Z", REJECTED),
            ("2026-08-03T09:00:00Z", "2026-08-04T09:00:00Z", BYPASSED),
        ])

    def test_an_open_stay_is_absent_still_waiting(self):
        events = label_events([
            labeled("2026-07-01T09:00:00Z", "wo:draft")])
        self.assertEqual(completed_stays(events, self.PRD), [])

    def test_an_empty_history_yields_no_stays(self):
        self.assertEqual(completed_stays([], self.PRD), [])


class TestThePartition(unittest.TestCase):
    """The invariant that joins the digest and the miner: a completed
    stay is passed, rejected or bypassed (ADR-0137, amending ADR-0056's
    two-way split), so the digest's passages and the miner's rejections
    are disjoint slices of one list. This class is what executes it, and
    the window test it describes has one spelling to execute."""

    def stays(self, history=PARTITION_HISTORY):
        events = label_events(history)
        passed = {(gate, end) for gate, _, end, _ in gate_passages(events)}
        rejected = set(gate_rejections(events))
        bypassed = set(gate_bypasses(events))
        return passed, rejected, bypassed

    def test_together_they_are_exactly_the_completed_stays(self):
        passed, rejected, bypassed = self.stays()
        self.assertEqual(passed | rejected | bypassed, COMPLETED_STAYS)

    def test_no_stay_is_both_a_passage_and_a_rejection(self):
        passed, rejected, _ = self.stays()
        self.assertEqual(passed & rejected, set())

    def test_an_open_stay_is_in_no_class(self):
        passed, rejected, bypassed = self.stays()
        self.assertEqual([gate for gate, _ in passed | rejected | bypassed]
                         .count("blueprint"), 0)

    def test_a_forward_skip_is_the_third_class_and_only_that(self):
        # #2309 (ADR-0137): the partition is three-way
        passed, rejected, bypassed = self.stays(THREE_WAY_HISTORY)
        self.assertEqual(passed, {("merge", "2026-08-05T09:00:00Z")})
        self.assertEqual(rejected, {("prd", "2026-08-02T09:00:00Z")})
        self.assertEqual(bypassed, {("prd", "2026-08-04T09:00:00Z")})


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
