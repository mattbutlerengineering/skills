"""size_band_calibration.py — size-band error intervals from past cost.

The run is docs/features/size-band-calibration/ (ADR-0112's import edges).
Every case runs through the public interface with fixture ledger entries
and fixture breakdown text; the cost side is cost_ledger's, the band side
is the breakdown row's `size:` (Owner decision 4: a read-time join, the
ledger gains no field).
"""
import copy
import unittest
from pathlib import Path

import cost_ledger
import size_band_calibration as sbc

ROOT = Path("/repo")
RUN_A = "docs/features/alpha"
RUN_B = "docs/features/beta"


def wo(n):
    """A work-order token, built here so no markdown scan sees one."""
    return f"WO-{n:04d}"


def row(n, size=None, title="Item"):
    tail = f" — size:{size}" if size else ""
    return f"- [ ] **{wo(n)}** {title}{tail}"


def breakdown(run, *rows):
    return ROOT / run / "breakdown.md", list(rows)


def ledger(token, cost, run_id="r1", outcome="merged"):
    return cost_ledger.entry(token, run_id, "claude-sonnet-5", 100, cost,
                             outcome, "2026-10-01")


class TestBands(unittest.TestCase):
    def test_a_token_joins_to_the_size_of_the_row_that_names_it(self):
        mapping, ambiguous = sbc.bands(
            [breakdown(RUN_A, row(1, "S"), row(2, "M")),
             breakdown(RUN_B, row(3, "L"))], ROOT)
        self.assertEqual(mapping, {
            wo(1): {"size": "S", "run": RUN_A},
            wo(2): {"size": "M", "run": RUN_A},
            wo(3): {"size": "L", "run": RUN_B}})
        self.assertEqual(ambiguous, frozenset())

    def test_the_join_adds_no_field_to_a_ledger_entry(self):
        entries = [ledger(wo(1), 2.0)]
        before = copy.deepcopy(entries)
        mapping, ambiguous = sbc.bands(
            [breakdown(RUN_A, row(1, "S"))], ROOT)
        sbc.select(entries, mapping, ambiguous)
        self.assertEqual(entries, before)
        self.assertEqual(set(entries[0]),
                         set(cost_ledger.LEDGER_FIELDS)
                         | set(cost_ledger.LEDGER_OPTIONAL_FIELDS))

    def test_a_token_under_two_sizes_is_left_out_and_ambiguous(self):
        mapping, ambiguous = sbc.bands(
            [breakdown(RUN_A, row(1, "S"), row(2, "S")),
             breakdown(RUN_B, row(1, "M"))], ROOT)
        self.assertEqual(mapping, {wo(2): {"size": "S", "run": RUN_A}})
        self.assertEqual(ambiguous, frozenset({wo(1)}))

    def test_the_same_size_twice_is_not_ambiguous(self):
        mapping, ambiguous = sbc.bands(
            [breakdown(RUN_A, row(1, "S")), breakdown(RUN_B, row(1, "S"))],
            ROOT)
        self.assertEqual(sorted(mapping), [wo(1)])
        self.assertEqual(ambiguous, frozenset())

    def test_a_row_with_no_size_is_not_defaulted(self):
        mapping, ambiguous = sbc.bands(
            [breakdown(RUN_A, row(1), "prose naming " + wo(2))], ROOT)
        self.assertEqual(mapping, {})
        self.assertEqual(ambiguous, frozenset())


class TestSelect(unittest.TestCase):
    MAPPING = {wo(1): {"size": "S", "run": RUN_A},
               wo(2): {"size": "M", "run": RUN_A}}

    def test_each_row_is_counted_once_in_the_architecture_order(self):
        gate = cost_ledger.gate_entry(wo(1), "human", 30,
                                      "2026-10-01T00:00:00Z")
        owner = ledger(wo(1), 0.0, "o1", "owner-session:unmetered")
        zero_joined = ledger(wo(1), 0.0, "z1")
        zero_unknown = ledger("#12", 0.0, "z2")
        issue_key = ledger("#12", 2.0, "i1")
        unknown = ledger(wo(9), 3.0, "u1")
        ambiguous_row = ledger(wo(5), 4.0, "a1")
        used_a, used_b = ledger(wo(1), 1.5, "u2"), ledger(wo(2), 2.5, "u3")
        used, exclusions = sbc.select(
            [gate, owner, zero_joined, zero_unknown, issue_key, unknown,
             ambiguous_row, used_a, used_b],
            self.MAPPING, frozenset({wo(5)}))
        self.assertEqual(used, [used_a, used_b])
        self.assertEqual(exclusions, {
            "gate": 1, "owner_session": 1, "zero_cost": 2,
            "unjoined": 2, "ambiguous": 1})

    def test_a_sized_breakdown_row_is_required_not_just_a_token(self):
        entry = ledger(wo(3), 5.0)
        used, exclusions = sbc.select([entry], self.MAPPING, frozenset())
        self.assertEqual(used, [])
        self.assertEqual(exclusions["unjoined"], 1)

    def test_only_unmetered_owner_sessions_leave_nothing_used(self):
        entries = [ledger(wo(1), 0.0, f"o{n}", "owner-session:unmetered")
                   for n in range(4)]
        used, exclusions = sbc.select(entries, self.MAPPING, frozenset())
        self.assertEqual(used, [])
        self.assertEqual(exclusions["owner_session"], len(entries))
        self.assertEqual(sum(exclusions.values()), len(entries))


class TestWorkOrders(unittest.TestCase):
    MAPPING = {wo(1): {"size": "S", "run": RUN_A},
               wo(2): {"size": "M", "run": RUN_B}}

    def test_six_rows_for_one_token_are_one_work_order(self):
        used = [ledger(wo(1), cost, f"r{i}")
                for i, cost in enumerate((0.5, 1.0, 1.5, 2.0, 0.25, 0.75))]
        used.append(ledger(wo(2), 4.0, "r9"))
        orders = sbc.work_orders(used, self.MAPPING)
        self.assertEqual(orders, [
            {"wo": wo(1), "band": "S", "run": RUN_A, "cost": 6.0},
            {"wo": wo(2), "band": "M", "run": RUN_B, "cost": 4.0}])

    def test_an_excluded_row_adds_no_cost(self):
        entries = [ledger(wo(1), 2.0),
                   ledger(wo(1), 0.0, "o", "owner-session:unmetered"),
                   ledger("#7", 9.0, "i")]
        used, _ = sbc.select(entries, self.MAPPING, frozenset())
        orders = sbc.work_orders(used, self.MAPPING)
        self.assertEqual([o["cost"] for o in orders], [2.0])


if __name__ == "__main__":
    unittest.main()
