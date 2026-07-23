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
import tempfile
import unittest
from pathlib import Path

import cost_ledger


# fixture records come from the seam under test — entry() itself is
# covered by TestEntry, so building fixtures with it is not circular
entry = cost_ledger.entry


class TestEntry(unittest.TestCase):
    def test_builds_exactly_the_ledger_fields(self):
        record = cost_ledger.entry(
            "WO-0006", "r-1", "claude-sonnet-5", 9000, 16.25,
            "budget-exhausted")
        self.assertEqual(tuple(record), cost_ledger.LEDGER_FIELDS)
        self.assertEqual(record["wo"], "WO-0006")
        self.assertEqual(record["cost"], 16.25)
        self.assertEqual(record["outcome"], "budget-exhausted")

    def test_a_built_entry_has_no_shape_problems(self):
        record = cost_ledger.entry("WO-0001", "r-1", "m", 100, 1.0, "merged")
        self.assertEqual(cost_ledger.line_problems(record), [])


class TestAppend(unittest.TestCase):
    def test_appends_one_line_creating_the_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = cost_ledger.entry(
                "WO-0006", "r-1", "m", 100, 1.0, "merged")
            cost_ledger.append(tmp, record)
            ledger = Path(tmp) / cost_ledger.COST_LEDGER
            self.assertEqual(
                ledger.read_text(encoding="utf-8"),
                json.dumps(record) + "\n")

    def test_appends_without_touching_existing_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = cost_ledger.entry(
                "WO-0001", "r-1", "m", 100, 1.0, "merged")
            second = cost_ledger.entry(
                "WO-0002", "r-2", "m", 200, 2.0, "budget-exhausted")
            cost_ledger.append(tmp, first)
            cost_ledger.append(tmp, second)
            ledger = Path(tmp) / cost_ledger.COST_LEDGER
            lines = ledger.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines, [json.dumps(first), json.dumps(second)])


class TestWoToken(unittest.TestCase):
    def test_a_valid_token_is_returned(self):
        record = entry("WO-0009", "r-1", "m", 1, 0.1, "merged")
        self.assertEqual(cost_ledger.wo_token(record), "WO-0009")

    def test_an_invalid_or_absent_token_is_none(self):
        for record in ({"wo": "nonsense"}, {"wo": 7}, {}, None):
            self.assertIsNone(cost_ledger.wo_token(record), record)


class TestLineProblems(unittest.TestCase):
    def test_a_well_formed_record_has_no_problems(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged")
        self.assertEqual(cost_ledger.line_problems(record), [])

    def test_missing_fields_are_named_sorted(self):
        self.assertEqual(
            cost_ledger.line_problems({"wo": "WO-0001", "run_id": "r-1",
                                       "model": "m", "outcome": "merged"}),
            ["ledger line is missing field(s): cost, tokens"])

    def test_unknown_fields_are_named(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged")
        record["surprise"] = True
        self.assertEqual(cost_ledger.line_problems(record),
                         ["ledger line has unknown field(s): surprise"])

    def test_bad_field_values_in_ledger_field_order(self):
        record = entry("nonsense", "", "m", -5, -1.0, "merged")
        self.assertEqual(cost_ledger.line_problems(record), [
            "wo 'nonsense' is not a WO-#### token",
            "run_id must be a non-empty string",
            "tokens must be a non-negative integer",
            "cost must be a non-negative number",
        ])

    def test_bool_tokens_and_cost_are_problems(self):
        # bool is an int subclass in Python; True must not pass as a count
        # or a dollar amount.
        record = entry("WO-0001", "r-1", "m", True, True, "merged")
        self.assertEqual(cost_ledger.line_problems(record), [
            "tokens must be a non-negative integer",
            "cost must be a non-negative number",
        ])


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

    def test_the_round_trip_through_gate_wait(self):
        record = cost_ledger.gate_entry(
            "WO-0003", "prd", 86400, "2026-07-01T09:00:00Z")
        self.assertEqual(cost_ledger.gate_wait(record), ("prd", 86400))


class TestGateWait(unittest.TestCase):
    def test_a_dispatched_run_row_is_not_a_gate_row(self):
        record = entry("WO-0006", "r-1", "claude-sonnet-5", 9000, 16.25,
                       "merged")
        self.assertIsNone(cost_ledger.gate_wait(record))

    def test_malformed_or_absent_outcomes_are_none(self):
        for record in ({"outcome": "gate_wait:prd:"},
                       {"outcome": "gate_wait:prd:12"},
                       {"outcome": "gate_wait:12s"},
                       {"outcome": 7}, {}, None):
            self.assertIsNone(cost_ledger.gate_wait(record), record)


class TestParse(unittest.TestCase):
    def test_blank_lines_are_skipped_and_linenos_kept(self):
        record = entry("WO-0001", "r-1", "m", 100, 1.5, "merged")
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


class TestRead(unittest.TestCase):
    def ledger(self, tmp, text):
        path = Path(tmp) / cost_ledger.COST_LEDGER
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_a_missing_ledger_is_empty_not_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cost_ledger.read(tmp), ([], []))

    def test_reads_well_formed_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            e1 = entry("WO-0001", "r-1", "m", 100, 1.5, "merged")
            e2 = entry("WO-0002", "r-2", "m", 200, 2.5, "merged")
            self.ledger(tmp, json.dumps(e1) + "\n" + json.dumps(e2) + "\n")
            self.assertEqual(cost_ledger.read(tmp), ([e1, e2], []))

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
            bad = entry("WO-0001", "r-1", "m", 100, -5.0, "merged")
            self.ledger(tmp, json.dumps(bad) + "\n")
            self.assertEqual(cost_ledger.read(tmp), ([], [
                "ledger: docs/factory/costs.jsonl:1 cost must be a"
                " non-negative number"]))

    def test_an_injected_ledger_path_overrides_the_repo_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp) / "custom.jsonl"
            e1 = entry("WO-0001", "r-1", "m", 100, 1.5, "merged")
            custom.write_text(json.dumps(e1) + "\n", encoding="utf-8")
            self.assertEqual(
                cost_ledger.read("/does/not/exist", ledger_path=custom),
                ([e1], []))


if __name__ == "__main__":
    unittest.main()
