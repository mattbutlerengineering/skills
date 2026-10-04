"""cost_ledger.py (the ADR-0034/0037 cost-ledger seam) — pure-function +
fixture tests.

Same discipline as test_budget_guard: every function is exercised through
its public interface and tests assert the EXACT strings callers will
print. The classes here absorbed the ledger tests that used to live in
test_budget_guard (entry/append, against budget_guard.ledger_entry and
append_ledger_line) and test_cost_report (read, against
cost_report.read_ledger) — one grammar, one home, one test file.
"""
import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import cost_ledger
import cost_report
import human_gates
import work_queue


# fixture records come from the seam under test — entry() itself is
# covered by TestEntry, so building fixtures with it is not circular
entry = cost_ledger.entry


class TestEntry(unittest.TestCase):
    def test_builds_the_ledger_fields_plus_at(self):
        record = cost_ledger.entry(
            "WO-0006", "r-1", "claude-sonnet-5", 9000, 16.25,
            "budget-exhausted", "2026-08-02")
        self.assertEqual(
            tuple(record),
            cost_ledger.LEDGER_FIELDS + cost_ledger.LEDGER_OPTIONAL_FIELDS)
        self.assertEqual(record["wo"], "WO-0006")
        self.assertEqual(record["cost"], 16.25)
        self.assertEqual(record["outcome"], "budget-exhausted")
        self.assertEqual(record["at"], "2026-08-02")

    def test_a_built_entry_has_no_shape_problems(self):
        record = cost_ledger.entry("WO-0001", "r-1", "m", 100, 1.0, "merged",
                                   "2026-08-02")
        self.assertEqual(cost_ledger.line_problems(record), [])


class TestAppend(unittest.TestCase):
    def test_appends_one_line_creating_the_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = cost_ledger.entry(
                "WO-0006", "r-1", "m", 100, 1.0, "merged", "2026-08-02")
            cost_ledger.append(tmp, record)
            ledger = Path(tmp) / cost_ledger.COST_LEDGER
            self.assertEqual(
                ledger.read_text(encoding="utf-8"),
                json.dumps(record) + "\n")

    def test_appends_without_touching_existing_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = cost_ledger.entry(
                "WO-0001", "r-1", "m", 100, 1.0, "merged", "2026-08-01")
            second = cost_ledger.entry(
                "WO-0002", "r-2", "m", 200, 2.0, "budget-exhausted",
                "2026-08-02")
            cost_ledger.append(tmp, first)
            cost_ledger.append(tmp, second)
            ledger = Path(tmp) / cost_ledger.COST_LEDGER
            lines = ledger.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines, [json.dumps(first), json.dumps(second)])


class TestWoToken(unittest.TestCase):
    def test_a_valid_token_is_returned(self):
        record = entry("WO-0009", "r-1", "m", 1, 0.1, "merged", "2026-08-02")
        self.assertEqual(cost_ledger.wo_token(record), "WO-0009")

    def test_an_invalid_or_absent_token_is_none(self):
        for record in ({"wo": "nonsense"}, {"wo": 7}, {}, None):
            self.assertIsNone(cost_ledger.wo_token(record), record)


class TestLineProblems(unittest.TestCase):
    def test_a_well_formed_record_has_no_problems(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-08-02")
        self.assertEqual(cost_ledger.line_problems(record), [])

    def test_a_legacy_row_without_at_is_valid(self):
        # Pre-2026-08 rows predate the at field; the ledger is append-only
        # and never backfilled, so they must keep parsing cleanly.
        record = {"wo": "WO-0001", "run_id": "r-1", "model": "m",
                  "tokens": 100, "cost": 1.5, "outcome": "merged"}
        self.assertEqual(cost_ledger.line_problems(record), [])

    def test_missing_fields_are_named_sorted(self):
        self.assertEqual(
            cost_ledger.line_problems({"wo": "WO-0001", "run_id": "r-1",
                                       "model": "m", "outcome": "merged"}),
            ["ledger line is missing field(s): cost, tokens"])

    def test_unknown_fields_are_named(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-08-02")
        record["surprise"] = True
        self.assertEqual(cost_ledger.line_problems(record),
                         ["ledger line has unknown field(s): surprise"])

    def test_bad_field_values_in_ledger_field_order(self):
        record = entry("nonsense", "", "m", -5, -1.0, "merged", "2026-08-02")
        self.assertEqual(cost_ledger.line_problems(record), [
            "wo 'nonsense' is not a WO-#### token",
            "run_id must be a non-empty string",
            "tokens must be a non-negative integer",
            "cost must be a non-negative number",
        ])

    def test_bool_tokens_and_cost_are_problems(self):
        # bool is an int subclass in Python; True must not pass as a count
        # or a dollar amount.
        record = entry("WO-0001", "r-1", "m", True, True, "merged",
                       "2026-08-02")
        self.assertEqual(cost_ledger.line_problems(record), [
            "tokens must be a non-negative integer",
            "cost must be a non-negative number",
        ])

    def test_a_non_iso_at_is_a_problem(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "yesterday")
        self.assertEqual(cost_ledger.line_problems(record),
                         ["at 'yesterday' is not an ISO date (YYYY-MM-DD)"])

    def test_a_non_string_at_is_a_problem(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged", 20260802)
        self.assertEqual(cost_ledger.line_problems(record),
                         ["at 20260802 is not an ISO date (YYYY-MM-DD)"])

    def test_a_basic_format_iso_date_at_is_a_problem(self):
        # date.fromisoformat alone accepts the basic "20260802" (and week
        # dates); such a row would pass the shape check yet fall out of
        # every month window — the fail-open direction the breaker must
        # not have. Only the dashed calendar form is a valid at.
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged", "20260802")
        self.assertEqual(cost_ledger.line_problems(record),
                         ["at '20260802' is not an ISO date (YYYY-MM-DD)"])

    def test_an_impossible_calendar_date_at_is_a_problem(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-13-40")
        self.assertEqual(cost_ledger.line_problems(record),
                         ["at '2026-13-40' is not an ISO date (YYYY-MM-DD)"])


class TestGateEntry(unittest.TestCase):
    def test_a_gate_row_is_a_well_formed_zero_cost_ledger_record(self):
        record = cost_ledger.gate_entry(
            "WO-0017", "merge", 7260, "2026-07-22T05:17:00Z")
        self.assertEqual(cost_ledger.line_problems(record), [])
        self.assertEqual(record["wo"], "WO-0017")
        self.assertEqual(record["run_id"], "gate-merge-2026-07-22T05:17:00Z")
        self.assertEqual(record["tokens"], 0)
        self.assertEqual(record["cost"], 0.0)
        self.assertEqual(record["outcome"], "gate_wait:merge:7260s")

    def test_a_gate_row_derives_at_from_the_passage_timestamp(self):
        # Gate rows need no clock: the passage timestamp already carries
        # the date the monthly window keys on.
        record = cost_ledger.gate_entry(
            "WO-0017", "merge", 7260, "2026-07-22T05:17:00Z")
        self.assertEqual(record["at"], "2026-07-22")

    def test_the_round_trip_through_gate_wait(self):
        record = cost_ledger.gate_entry(
            "WO-0003", "prd", 86400, "2026-07-01T09:00:00Z")
        self.assertEqual(cost_ledger.gate_wait(record), ("prd", 86400))


class TestGateEntryCannotOutwriteItsReader(unittest.TestCase):
    """gate_entry composes the outcome field; gate_wait parses it with
    GATE_OUTCOME. A row the writer emits and the reader refuses is not
    merely a lost observation: dispatched() selects spend by exclusion,
    so an unreadable gate row is counted as a dispatched run against
    ADR-0034's monthly cap."""

    PASSED_AT = "2026-08-27T00:00:00Z"

    def test_a_gate_name_the_reader_cannot_read_is_refused(self):
        with self.assertRaises(ValueError):
            cost_ledger.gate_entry("WO-0001", "code-review", 120,
                                   self.PASSED_AT)

    def test_a_negative_wait_is_refused(self):
        with self.assertRaises(ValueError):
            cost_ledger.gate_entry("WO-0001", "merge", -30, self.PASSED_AT)

    def test_the_writer_and_the_reader_never_disagree(self):
        # The property that makes the two statements of the grammar one:
        # for ANY input, either the writer refuses or the reader parses
        # what it produced. A silent unreadable row is the failure.
        cases = ["merge", "prd", "code-review", "UX", "ux2", "", "a:b",
                 "merge s", "méfiance"]
        waits = [0, 1, 7260, -30, 12.7]
        for gate in cases:
            for wait in waits:
                with self.subTest(gate=gate, wait=wait):
                    try:
                        row = cost_ledger.gate_entry("WO-0001", gate, wait,
                                                     self.PASSED_AT)
                    except ValueError:
                        continue
                    self.assertIsNotNone(
                        cost_ledger.gate_wait(row),
                        f"wrote an unreadable row: {row['outcome']!r}")
                    self.assertEqual(cost_ledger.dispatched([row]), [])

    def test_every_shipped_gate_name_is_writable(self):
        # The guard turns "someone added a gate the ledger cannot record"
        # from a silent spend miscount into a red test here.
        for gate in human_gates.GATES:
            with self.subTest(gate=gate.name):
                row = cost_ledger.gate_entry("WO-0001", gate.name, 60,
                                             self.PASSED_AT)
                self.assertEqual(cost_ledger.gate_wait(row),
                                 (gate.name, 60))


class TestRowKey(unittest.TestCase):
    def test_the_identity_is_wo_plus_run_id(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-08-02")
        self.assertEqual(cost_ledger.row_key(record), ("WO-0001", "r-1"))

    def test_a_reobserved_gate_passage_has_the_same_key(self):
        # ADR-0041: the passage timestamp keys run_id, so a daily re-scan
        # of the same label history composes a row with the SAME identity
        # — the dedup the gate digest hangs on this function.
        first = cost_ledger.gate_entry("WO-0017", "merge", 7260,
                                       "2026-07-22T05:17:00Z")
        again = cost_ledger.gate_entry("WO-0017", "merge", 7260,
                                       "2026-07-22T05:17:00Z")
        self.assertEqual(cost_ledger.row_key(first),
                         cost_ledger.row_key(again))

    def test_distinct_passages_have_distinct_keys(self):
        earlier = cost_ledger.gate_entry("WO-0017", "merge", 7260,
                                         "2026-07-22T05:17:00Z")
        later = cost_ledger.gate_entry("WO-0017", "merge", 60,
                                       "2026-07-23T09:00:00Z")
        self.assertNotEqual(cost_ledger.row_key(earlier),
                            cost_ledger.row_key(later))


class TestInMonth(unittest.TestCase):
    def test_a_row_in_the_month_matches(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-08-02")
        self.assertTrue(cost_ledger.in_month(record, "2026-08"))

    def test_a_row_in_another_month_does_not(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-07-28")
        self.assertFalse(cost_ledger.in_month(record, "2026-08"))

    def test_a_legacy_row_is_in_no_month(self):
        # Pre-at rows belong to closed months by construction.
        legacy = {"wo": "WO-0001", "run_id": "r-1", "model": "m",
                  "tokens": 100, "cost": 1.5, "outcome": "merged"}
        self.assertFalse(cost_ledger.in_month(legacy, "2026-08"))

    def test_malformed_records_are_in_no_month(self):
        for record in ({"at": 7}, {}, None):
            self.assertFalse(cost_ledger.in_month(record, "2026-08"),
                             record)


class TestGateWait(unittest.TestCase):
    def test_a_dispatched_run_row_is_not_a_gate_row(self):
        record = entry("WO-0006", "r-1", "claude-sonnet-5", 9000, 16.25,
                       "merged", "2026-08-02")
        self.assertIsNone(cost_ledger.gate_wait(record))

    def test_malformed_or_absent_outcomes_are_none(self):
        for record in ({"outcome": "gate_wait:prd:"},
                       {"outcome": "gate_wait:prd:12"},
                       {"outcome": "gate_wait:12s"},
                       {"outcome": 7}, {}, None):
            self.assertIsNone(cost_ledger.gate_wait(record), record)


class TestParse(unittest.TestCase):
    def test_blank_lines_are_skipped_and_linenos_kept(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-08-02")
        text = "\n" + json.dumps(record) + "\n\n"
        self.assertEqual(cost_ledger.parse(text), [(2, record, [])])

    def test_invalid_json_is_an_unlocated_suffix(self):
        parsed = cost_ledger.parse("not json\n")
        self.assertEqual(len(parsed), 1)
        lineno, record, problems = parsed[0]
        self.assertEqual((lineno, record), (1, None))
        self.assertTrue(problems[0].startswith("is not valid JSON:"),
                        problems)

    def test_a_non_object_line_is_an_unlocated_suffix(self):
        self.assertEqual(cost_ledger.parse("[1, 2, 3]\n"),
                         [(1, None, ["is not a JSON object"])])


class TestLoad(unittest.TestCase):
    """The labelled file read both read() and detector G are built on:
    one existence check, one OSError-to-problem translation, one located
    problem grammar — prefixed with whatever label the caller reports
    under."""

    def ledger(self, tmp, text):
        path = Path(tmp) / cost_ledger.COST_LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_an_absent_ledger_is_none_not_empty(self):
        # None, not []: detector G's merged-row rule bites only once the
        # ledger exists, so absent and empty must stay distinguishable.
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cost_ledger.load(tmp, "G"), (None, []))

    def test_an_empty_ledger_is_distinct_from_an_absent_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.ledger(tmp, "")
            self.assertEqual(cost_ledger.load(tmp, "G"), ([], []))

    def test_a_well_formed_row_carries_no_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            e1 = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-08-01")
            self.ledger(tmp, json.dumps(e1) + "\n")
            self.assertEqual(cost_ledger.load(tmp, "ledger"),
                             ([(1, e1, [])], []))

    def test_rows_carry_located_problems_under_the_callers_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.ledger(tmp, "[1, 2]\n")
            self.assertEqual(cost_ledger.load(tmp, "G"), ([
                (1, None,
                 ["G: docs/factory/costs.jsonl:1 is not a JSON object"]),
            ], []))

    def test_an_unreadable_ledger_is_the_callers_problem_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.ledger(tmp, "")
            with mock.patch.object(Path, "read_text",
                                    side_effect=OSError("Permission denied")):
                rows, problems = cost_ledger.load(tmp, "G")
            self.assertIsNone(rows)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                "G: cannot read docs/factory/costs.jsonl:"), problems)

    def test_an_injected_ledger_path_overrides_the_repo_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp) / "custom.jsonl"
            e1 = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-08-01")
            custom.write_text(json.dumps(e1) + "\n", encoding="utf-8")
            self.assertEqual(
                cost_ledger.load("/does/not/exist", "ledger",
                                 ledger_path=custom),
                ([(1, e1, [])], []))


class TestRead(unittest.TestCase):
    def ledger(self, tmp, text):
        path = Path(tmp) / cost_ledger.COST_LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_a_missing_ledger_is_empty_not_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cost_ledger.read(tmp), ([], []))

    def test_an_empty_ledger_is_empty_not_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.ledger(tmp, "")
            self.assertEqual(cost_ledger.read(tmp), ([], []))

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-000 file")
    def test_a_ledger_the_process_may_not_read_is_a_ledger_problem(self):
        # read() reports the file-level failure under its own label and
        # returns no entries — the fail-closed half its callers act on
        with tempfile.TemporaryDirectory() as tmp:
            self.ledger(tmp, "")
            path = Path(tmp) / cost_ledger.COST_LEDGER
            path.chmod(0)
            try:
                self.assertEqual(cost_ledger.read(tmp), ([], [
                    "ledger: cannot read docs/factory/costs.jsonl: [Errno"
                    f" 13] Permission denied: '{path}'"]))
            finally:
                path.chmod(0o644)

    def test_reads_well_formed_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            e1 = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-08-01")
            e2 = entry("WO-0002", "r-2", "m", 200, 2.5, "merged",
                       "2026-08-02")
            self.ledger(tmp, json.dumps(e1) + "\n" + json.dumps(e2) + "\n")
            self.assertEqual(cost_ledger.read(tmp), ([e1, e2], []))

    def test_a_legacy_line_without_at_still_reads(self):
        # The real docs/factory/costs.jsonl has pre-at rows; read() must
        # keep returning them (append-only: they are never rewritten).
        with tempfile.TemporaryDirectory() as tmp:
            legacy = {"wo": "WO-0001", "run_id": "r-1", "model": "m",
                      "tokens": 100, "cost": 1.5, "outcome": "merged"}
            self.ledger(tmp, json.dumps(legacy) + "\n")
            self.assertEqual(cost_ledger.read(tmp), ([legacy], []))

    def test_invalid_json_is_a_problem_and_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.ledger(tmp, "not json\n")
            entries, problems = cost_ledger.read(tmp)
            self.assertEqual(entries, [])
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                "ledger: docs/factory/costs.jsonl:1 is not valid JSON:"),
                problems)

    def test_a_non_object_line_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.ledger(tmp, "[1, 2, 3]\n")
            self.assertEqual(cost_ledger.read(tmp), ([], [
                "ledger: docs/factory/costs.jsonl:1 is not a JSON object"]))

    def test_an_entry_missing_its_cost_is_excluded_and_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = {"wo": "WO-0001", "run_id": "r-1", "model": "m",
                   "tokens": 100, "outcome": "merged"}  # no cost field
            self.ledger(tmp, json.dumps(bad) + "\n")
            self.assertEqual(cost_ledger.read(tmp), ([], [
                "ledger: docs/factory/costs.jsonl:1 ledger line is missing"
                " field(s): cost"]))

    def test_a_negative_cost_is_excluded_and_flagged(self):
        # Fail closed: a negative cost would silently pull the total spend
        # DOWN, exactly the direction that could mask a real cap breach.
        with tempfile.TemporaryDirectory() as tmp:
            bad = entry("WO-0001", "r-1", "m", 100, -5.0, "merged",
                        "2026-08-02")
            self.ledger(tmp, json.dumps(bad) + "\n")
            self.assertEqual(cost_ledger.read(tmp), ([], [
                "ledger: docs/factory/costs.jsonl:1 cost must be a"
                " non-negative number"]))

    def test_an_injected_ledger_path_overrides_the_repo_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp) / "custom.jsonl"
            e1 = entry("WO-0001", "r-1", "m", 100, 1.5, "merged",
                       "2026-08-01")
            custom.write_text(json.dumps(e1) + "\n", encoding="utf-8")
            self.assertEqual(
                cost_ledger.read("/does/not/exist", ledger_path=custom),
                ([e1], []))


class TestWhatCountsAsSpend(unittest.TestCase):
    """The two month-to-date sums, over one ledger carrying a gate row
    that cost money.

    ADR-0041 decided the rule — a gate-latency observation is a wait
    record, not a run, and never counts as spend — and both callers now
    read it from cost_ledger.dispatched. This case pinned the divergence
    before the fold (cost_report $12.50, work_queue $15.75) and pins the
    agreement after it; the row set is the same one, so the two figures
    cannot drift apart again.

    The disagreement was never reachable through a production path:
    cost_ledger.gate_entry writes every gate row 0 tokens and 0.0 cost BY
    CONSTRUCTION, so both sums returned the same number over the real
    ledger and always have. The costly gate row below is therefore
    hand-assembled into a fixture, and exists nowhere else:
    docs/factory/costs.jsonl is append-only and carries no such line.
    """

    MONTH = "2026-08"
    NOW = datetime(2026, 8, 15, tzinfo=timezone.utc)

    def fixture(self, tmp):
        """(a dispatched run, a gate passage that cost money), written to
        a ledger under `tmp`. gate_entry cannot build the second one, so
        it comes from the same field builder every well-formed row does."""
        run = entry("WO-0001", "r-1", "claude-sonnet-5", 9000, 12.50,
                    "merged", "2026-08-02")
        gate = entry("WO-0001", "gate-merge-2026-08-03T05:17:00Z", "none",
                     500, 3.25, "gate_wait:merge:7260s", "2026-08-03")
        # The row is a well-formed gate row: read() admits it and
        # gate_wait recognises it, so nothing but the spend rule is at
        # stake in the numbers below.
        self.assertEqual(cost_ledger.line_problems(gate), [])
        self.assertEqual(cost_ledger.gate_wait(gate), ("merge", 7260))
        path = Path(tmp) / cost_ledger.COST_LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(run) + "\n" + json.dumps(gate) + "\n",
                        encoding="utf-8")
        return run, gate

    def test_the_two_month_totals_agree_on_a_costly_gate_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.fixture(tmp)
            entries, problems = cost_ledger.read(tmp)
            self.assertEqual(problems, [])
            report_total = cost_report.aggregate(
                entries, self.MONTH)["total_cost"]
            queue_total, queue_problems = work_queue.month_to_date(
                tmp, self.NOW)
            self.assertEqual(queue_problems, [])
            # One number, $12.50: the $3.25 gate row is not spend to
            # either caller. Before the fold this read 12.50 versus
            # 15.75, and the second figure was the breaker's input.
            self.assertEqual(report_total, 12.50)
            self.assertEqual(queue_total, 12.50)
            self.assertEqual(report_total, queue_total)


class TestDispatched(unittest.TestCase):
    """The one row-selection rule both month-to-date figures walk."""

    def rows(self):
        return [
            entry("WO-0001", "r-1", "m", 100, 1.50, "merged", "2026-08-02"),
            entry("WO-0001", "gate-merge-2026-08-03T05:17:00Z", "none", 500,
                  3.25, "gate_wait:merge:7260s", "2026-08-03"),
            entry("WO-0002", "r-2", "m", 200, 2.50, "merged", "2026-07-31"),
        ]

    def test_gate_rows_are_never_spend(self):
        run, _gate, older = self.rows()
        self.assertEqual(cost_ledger.dispatched(self.rows()), [run, older])

    def test_a_month_admits_only_that_months_dispatched_rows(self):
        run, _gate, _older = self.rows()
        self.assertEqual(cost_ledger.dispatched(self.rows(), "2026-08"),
                         [run])

    def test_no_month_is_the_lifetime_row_set(self):
        # month=None is not "this month" — it is every month, which is
        # what the report's lifetime totals are built from.
        self.assertEqual(len(cost_ledger.dispatched(self.rows())), 2)

    def test_a_legacy_row_without_at_is_in_no_month_but_is_spend(self):
        # Pre-`at` rows belong to closed months by construction, so they
        # count lifetime and in no window — in_month's rule, unchanged.
        legacy = {"wo": "WO-0001", "run_id": "r-1", "model": "m",
                  "tokens": 100, "cost": 1.5, "outcome": "merged"}
        self.assertEqual(cost_ledger.dispatched([legacy]), [legacy])
        self.assertEqual(cost_ledger.dispatched([legacy], "2026-08"), [])

    def test_an_empty_ledger_selects_nothing(self):
        self.assertEqual(cost_ledger.dispatched([], "2026-08"), [])

    def test_a_zero_cost_gate_row_is_excluded_too(self):
        # The production shape (gate_entry writes $0/0 tokens): excluded
        # for being a gate row, not for costing nothing.
        gate = cost_ledger.gate_entry("WO-0017", "merge", 7260,
                                      "2026-08-03T05:17:00Z")
        self.assertEqual(cost_ledger.dispatched([gate], "2026-08"), [])


if __name__ == "__main__":
    unittest.main()
