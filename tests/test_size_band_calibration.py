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


CONFIG = {"budgets_usd": {"S": 5, "M": 15, "L": 40}}


def order(n, band, cost, run=RUN_A):
    return {"wo": wo(n), "band": band, "run": run, "cost": cost}


class TestBre(unittest.TestCase):
    def test_twice_the_budget_is_plus_one_and_half_is_minus_one(self):
        self.assertEqual(sbc.bre(10.0, 5), 1.0)
        self.assertEqual(sbc.bre(2.5, 5), -1.0)

    def test_the_budget_itself_is_zero(self):
        self.assertEqual(sbc.bre(5.0, 5), 0.0)

    def test_worked_by_hand_against_the_smaller_of_the_two(self):
        # overrun: (20 - 5) / min(20, 5) = 3; underrun: (3 - 12) / 3 = -3
        self.assertEqual(sbc.bre(20.0, 5), 3.0)
        self.assertEqual(sbc.bre(3.0, 12), -3.0)


class TestInterval(unittest.TestCase):
    def test_four_values_are_refused(self):
        self.assertIsNone(sbc.interval([1.0, 2.0, 3.0, 4.0], 5))

    def test_five_values_are_the_observed_range_and_the_middle_rank(self):
        # ranks ceil(0.5)=1, ceil(2.5)=3, ceil(4.5)=5
        self.assertEqual(sbc.interval([-1.0, 0.0, 0.5, 1.0, 3.0], 5),
                         {"p10": -1.0, "p50": 0.5, "p90": 3.0})

    def test_ten_values_use_ceil_of_p_n_over_100_with_no_interpolation(self):
        values = [float(v) for v in range(1, 11)]
        # ranks ceil(1)=1, ceil(5)=5, ceil(9)=9
        self.assertEqual(sbc.interval(values, 5),
                         {"p10": 1.0, "p50": 5.0, "p90": 9.0})

    def test_twelve_values_round_the_rank_up(self):
        values = [float(v) for v in range(1, 13)]
        # ranks ceil(1.2)=2, ceil(6)=6, ceil(10.8)=11
        self.assertEqual(sbc.interval(values, 5),
                         {"p10": 2.0, "p50": 6.0, "p90": 11.0})

    def test_every_returned_value_is_a_member_of_the_input(self):
        values = [0.3, 7.7, -2.2, 1.1, 9.9, 4.4, 5.5]
        result = sbc.interval(values, 5)
        self.assertTrue(set(result.values()) <= set(values))

    def test_input_order_does_not_matter(self):
        values = [3.0, -1.0, 1.0, 0.5, 0.0, 2.0]
        self.assertEqual(sbc.interval(values, 5),
                         sbc.interval(sorted(values), 5))

    def test_a_custom_floor_moves_the_refusal_point(self):
        self.assertIsNone(sbc.interval([1.0, 2.0], 3))
        self.assertEqual(sbc.interval([1.0, 2.0, 3.0], 3),
                         {"p10": 1.0, "p50": 2.0, "p90": 3.0})

    def test_the_input_is_not_mutated(self):
        values = [3.0, 1.0, 2.0, 5.0, 4.0]
        sbc.interval(values, 5)
        self.assertEqual(values, [3.0, 1.0, 2.0, 5.0, 4.0])


class TestOverBudget(unittest.TestCase):
    def test_counts_the_work_orders_with_bre_above_zero(self):
        self.assertEqual(sbc.over_budget([-1.0, 0.0, 0.5, 1.0, 3.0]), 3)
        self.assertEqual(sbc.over_budget([]), 0)


class TestBandStats(unittest.TestCase):
    ORDERS = [order(1, "S", 2.5), order(2, "S", 5.0), order(3, "S", 7.5),
              order(4, "S", 10.0), order(5, "S", 20.0),
              order(6, "M", 15.0)]

    def test_the_budget_comes_from_the_fixture_config(self):
        stats, problems = sbc.band_stats("S", self.ORDERS, CONFIG)
        self.assertEqual(problems, [])
        self.assertEqual(stats["budget"], 5)
        self.assertEqual(stats["bre"], [-1.0, 0.0, 0.5, 1.0, 3.0])
        config = {"budgets_usd": {"S": 10, "M": 15, "L": 40}}
        other, _ = sbc.band_stats("S", self.ORDERS, config)
        self.assertEqual(other["budget"], 10)

    def test_a_band_at_the_floor_has_an_interval_and_totals(self):
        stats, _ = sbc.band_stats("S", self.ORDERS, CONFIG)
        self.assertEqual(stats["n"], 5)
        self.assertEqual(stats["floor"], 5)
        self.assertEqual(stats["interval"],
                         {"p10": -1.0, "p50": 0.5, "p90": 3.0})
        self.assertEqual(stats["over"], 3)
        self.assertEqual(stats["cost_total"], 45.0)
        self.assertEqual(stats["cost_mean"], 9.0)

    def test_a_band_below_the_floor_has_no_interval(self):
        stats, _ = sbc.band_stats("M", self.ORDERS, CONFIG)
        self.assertEqual((stats["n"], stats["interval"]), (1, None))

    def test_the_floor_comes_from_factory_config(self):
        config = {**CONFIG, "conductor": {"calibrate_floor": 1}}
        stats, _ = sbc.band_stats("M", self.ORDERS, config)
        self.assertEqual(stats["floor"], 1)
        self.assertEqual(stats["interval"],
                         {"p10": 0.0, "p50": 0.0, "p90": 0.0})

    def test_an_empty_band_has_no_rows_and_no_interval(self):
        stats, _ = sbc.band_stats("L", self.ORDERS, CONFIG)
        self.assertEqual((stats["n"], stats["bre"], stats["interval"]),
                         (0, [], None))

    def test_a_config_without_budgets_is_a_problem(self):
        stats, problems = sbc.band_stats("S", self.ORDERS, {})
        self.assertIsNone(stats)
        self.assertEqual(
            problems, ["config: factory.json has no budgets_usd table"])


if __name__ == "__main__":
    unittest.main()
