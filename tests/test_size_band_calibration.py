"""size_band_calibration.py — size-band error intervals from past cost.

The run is docs/features/size-band-calibration/ (ADR-0112's import edges).
Every case runs through the public interface with fixture ledger entries
and fixture breakdown text; the cost side is cost_ledger's, the band side
is the breakdown row's `size:` (Owner decision 4: a read-time join, the
ledger gains no field).
"""
import ast
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import cli
import cost_ledger
import decompose_signals
import factory_config
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


RUN_C = "docs/features/gamma"


def record(run, count=None, items=None, reason=None):
    replan = ({"unmeasurable": reason} if reason else
              {"label": "observed", "count": count, "items_at_d": items,
               "added": 0, "dropped": 0, "split": 0, "merged": 0,
               "renamed": 0})
    return {"path": run, "replan": replan}


def fixed(runs, problems=()):
    """An injected measure returning a fixed result and recording its
    arguments."""
    calls = []

    def measure(root, run):
        calls.append((root, run))
        result = {"runs": runs} if runs is not None else None
        return result, list(problems)
    measure.calls = calls
    return measure


class TestReplanByBand(unittest.TestCase):
    RUNS = [record(RUN_A, 2, 8), record(RUN_B, 1, 4),
            record(RUN_C, reason="no decompose commit")]

    def figures(self, orders, runs=None):
        figures, problems = sbc.replan_by_band(
            orders, fixed(self.RUNS if runs is None else runs), ROOT,
            "git")
        self.assertEqual(problems, [])
        return figures

    def test_a_band_pools_the_runs_that_hold_its_work_orders(self):
        figures = self.figures([order(1, "S", 1.0, RUN_A),
                                order(2, "S", 1.0, RUN_A),
                                order(3, "S", 1.0, RUN_B)])
        self.assertEqual(figures["S"], {"count": 3, "items": 12, "runs": 2,
                                        "unmeasurable": 0})

    def test_unmeasurable_runs_are_counted_not_summed(self):
        figures = self.figures([order(1, "M", 1.0, RUN_A),
                                order(2, "M", 1.0, RUN_C)])
        self.assertEqual(figures["M"], {"count": 2, "items": 8, "runs": 1,
                                        "unmeasurable": 1})

    def test_all_unmeasurable_runs_name_the_reason_never_zero(self):
        figures = self.figures([order(1, "L", 1.0, RUN_C)])
        self.assertEqual(figures["L"], {"unmeasurable":
                                        "no decompose commit"})

    def test_a_band_with_no_contributing_run_is_unmeasurable(self):
        figures = self.figures([order(1, "S", 1.0, RUN_A)])
        self.assertEqual(figures["M"], {"unmeasurable":
                                        "no run holds a work order of this"
                                        " band"})

    def test_a_run_the_measurement_never_saw_is_unmeasurable(self):
        figures = self.figures([order(1, "S", 1.0, "docs/features/new")])
        self.assertEqual(figures["S"], {"unmeasurable":
                                        "run not in the measurement"})

    def test_a_failed_measurement_is_one_problem_and_all_unmeasurable(self):
        failed = ["size-band-calibration: git for-each-ref failed: boom"]
        measure = fixed(None, failed)
        figures, problems = sbc.replan_by_band(
            [order(1, "S", 1.0, RUN_A)], measure, ROOT, "git")
        self.assertEqual(problems, failed)
        reason = "git history could not be read"
        self.assertEqual(figures, {band: {"unmeasurable": reason}
                                   for band in ("S", "M", "L")})

    def test_the_measure_is_called_once_with_the_root_and_runner(self):
        measure = fixed(self.RUNS)
        sbc.replan_by_band([order(1, "S", 1.0, RUN_A)], measure, ROOT, "git")
        self.assertEqual(measure.calls, [(ROOT, "git")])


PREFIX = "size-band-calibration:"
USAGE = "python3 size_band_calibration.py"
REPLAN = "re-plan 1/10 over 1 run(s) (0 unmeasurable)"


def write(root, relative, text):
    path = Path(root) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class Repo:
    """A temp repo: factory.json, a ledger and one breakdown per run."""

    def __init__(self, case, config=CONFIG):
        tmp = tempfile.TemporaryDirectory()
        case.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        if config is not None:
            write(self.root, ".github/factory.json", json.dumps(config))

    def breakdown(self, run, *rows):
        write(self.root, f"{run}/breakdown.md", "\n".join(rows) + "\n")

    def ledger(self, *entries):
        write(self.root, cost_ledger.COST_LEDGER,
              "".join(json.dumps(e) + "\n" for e in entries))


def run_main(argv, repo, measure=None, run=None):
    out = io.StringIO()
    with redirect_stdout(out):
        code = sbc.main(argv, root=repo.root, run=run,
                        measure=measure or fixed([record(RUN_A, 1, 10)]))
    return code, out.getvalue().splitlines()


def band_line(band, text):
    return f"{PREFIX} band {band} — {text}"


def no_rows(band):
    return band_line(band, "no metered work order joins this band;"
                     " re-plan unmeasurable")


def sized(*costs, start=1, band="S"):
    """Breakdown rows and ledger entries for one work order per cost."""
    numbers = range(start, start + len(costs))
    return ([row(n, band) for n in numbers],
            [ledger(wo(n), cost, f"run{n}")
             for n, cost in zip(numbers, costs)])


class TestReport(unittest.TestCase):
    def test_a_band_at_four_is_refused_with_cost_and_replan_only(self):
        repo = Repo(self)
        rows, entries = sized(2.5, 5.0, 7.5, 10.0)
        repo.breakdown(RUN_A, *rows)
        repo.ledger(*entries)
        code, lines = run_main([], repo)
        total = 2.5 + 5.0 + 7.5 + 10.0
        self.assertEqual(lines, [
            band_line("S", "refused: n 4 work order(s) is below the minimum"
                      f" of 5, no interval printed; cost ${total:.3f} total;"
                      f" {REPLAN}"),
            no_rows("M"), no_rows("L"),
            f"{PREFIX} 4 work order(s), 0 problem(s)"])
        self.assertEqual(code, 0)

    def test_the_same_band_at_five_prints_the_interval(self):
        repo = Repo(self)
        costs = (2.5, 5.0, 7.5, 10.0, 20.0)
        rows, entries = sized(*costs)
        repo.breakdown(RUN_A, *rows)
        repo.ledger(*entries)
        code, lines = run_main([], repo)
        errors = sorted((c - 5) / min(c, 5) for c in costs)
        p10, p50, p90 = errors[0], errors[2], errors[4]
        over = sum(1 for e in errors if e > 0)
        total = sum(costs)
        self.assertEqual(lines[0], band_line(
            "S", f"BRE P10 {p10:+.3f}, P50 {p50:+.3f}, P90 {p90:+.3f} over 5"
            " work order(s) against a $5 budget (nearest rank; at n = 5 P10"
            " and P90 are the observed range); over budget"
            f" {over} of 5; cost ${total / 5:.3f} mean, ${total:.3f} total;"
            f" {REPLAN}"))
        self.assertEqual(lines[0].count("P10 -1.000, P50 +0.500, P90 +3.000"),
                         1)
        self.assertEqual(lines[1:], [no_rows("M"), no_rows("L"),
                                     f"{PREFIX} 5 work order(s), 0 problem(s)"])
        self.assertEqual(code, 0)

    def test_an_all_unmetered_ledger_excludes_every_row(self):
        repo = Repo(self)
        repo.breakdown(RUN_A, row(1, "S"))
        repo.ledger(*[ledger(wo(1), 0.0, f"o{n}", "owner-session:unmetered")
                      for n in range(3)])
        code, lines = run_main([], repo)
        self.assertEqual(lines, [
            f"{PREFIX} excluded 3 owner-session:unmetered row(s) — cost never"
            " recorded, none estimated",
            no_rows("S"), no_rows("M"), no_rows("L"),
            f"{PREFIX} 0 work order(s), 0 problem(s)"])
        self.assertEqual(code, 0)

    def test_a_mixed_ledger_prints_each_nonzero_exclusion_in_order(self):
        repo = Repo(self)
        repo.breakdown(RUN_A, row(1, "M"), row(2, "L"), row(3, "S"),
                       row(3, "M"), row(4))
        repo.ledger(
            ledger(wo(1), 3.0, "a"), ledger(wo(1), 4.0, "b"),
            cost_ledger.gate_entry(wo(1), "human", 30, "2026-10-01T00:00:00Z"),
            ledger(wo(1), 0.0, "o", "owner-session:unmetered"),
            ledger(wo(2), 0.0, "z"), ledger("#9", 5.0, "i"),
            ledger(wo(4), 6.0, "n"), ledger(wo(3), 7.0, "c"))
        code, lines = run_main([], repo)
        self.assertEqual(lines[:5], [
            f"{PREFIX} excluded 1 owner-session:unmetered row(s) — cost never"
            " recorded, none estimated",
            f"{PREFIX} excluded 1 gate-latency row(s) — waits, not spend",
            f"{PREFIX} excluded 1 row(s) with cost 0 — no cost recorded",
            f"{PREFIX} excluded 2 row(s) whose wo names no sized breakdown"
            " row",
            f"{PREFIX} excluded 1 row(s) whose wo has conflicting sizes"])
        self.assertEqual(lines[5:], [
            no_rows("S"),
            band_line("M", "refused: n 1 work order(s) is below the minimum"
                      f" of 5, no interval printed; cost ${3.0 + 4.0:.3f} total;"
                      f" {REPLAN}"),
            no_rows("L"),
            f"{PREFIX} 1 work order(s), 0 problem(s)"])
        self.assertEqual(code, 0)

    def test_the_replan_figure_never_reads_zero_over_zero(self):
        repo = Repo(self)
        rows, entries = sized(1.0)
        repo.breakdown(RUN_A, *rows)
        repo.ledger(*entries)
        _, lines = run_main([], repo, measure=fixed(
            [record(RUN_A, reason="no decompose commit")]))
        self.assertTrue(lines[0].endswith(
            "re-plan unmeasurable — no decompose commit"))

    def test_a_failed_measurement_is_a_problem_and_the_report_stands(self):
        repo = Repo(self)
        rows, entries = sized(1.0)
        repo.breakdown(RUN_A, *rows)
        repo.ledger(*entries)
        failed = [f"{PREFIX} git for-each-ref failed: boom"]
        code, lines = run_main([], repo, measure=fixed(None, failed))
        self.assertEqual(lines[0], failed[0])
        self.assertTrue(lines[1].endswith(
            "re-plan unmeasurable — git history could not be read"))
        self.assertEqual(lines[-1], f"{PREFIX} 1 work order(s), 1 problem(s)")
        self.assertEqual(code, 1)


class TestReportFailures(unittest.TestCase):
    def test_a_rejected_ledger_line_stops_the_band_lines(self):
        repo = Repo(self)
        repo.breakdown(RUN_A, row(1, "S"))
        write(repo.root, cost_ledger.COST_LEDGER, "not json\n")
        _, expected = cost_ledger.read(repo.root)
        code, lines = run_main([], repo)
        self.assertTrue(expected)
        self.assertEqual(lines, expected
                         + [f"{PREFIX} 0 work order(s), {len(expected)}"
                            " problem(s)"])
        self.assertEqual(code, 1)

    def test_a_bad_factory_json_stops_the_band_lines(self):
        repo = Repo(self, config=None)
        repo.breakdown(RUN_A, row(1, "S"))
        repo.ledger(ledger(wo(1), 1.0))
        _, expected = factory_config.load(repo.root)
        code, lines = run_main([], repo)
        self.assertEqual(len(expected), 1)
        self.assertTrue(expected[0].startswith("config: "))
        self.assertEqual(lines, expected
                         + [f"{PREFIX} 0 work order(s), 1 problem(s)"])
        self.assertEqual(code, 1)

    def test_a_config_without_a_budget_table_stops_the_band_lines(self):
        repo = Repo(self, config={})
        repo.breakdown(RUN_A, row(1, "S"))
        repo.ledger(ledger(wo(1), 1.0))
        code, lines = run_main([], repo)
        self.assertEqual(lines, [
            "config: factory.json has no budgets_usd table",
            f"{PREFIX} 0 work order(s), 1 problem(s)"])
        self.assertEqual(code, 1)

    def test_an_unreadable_breakdown_is_a_problem_and_unjoined(self):
        repo = Repo(self)
        path = write(repo.root, f"{RUN_A}/breakdown.md", "")
        path.write_bytes(b"\xff\xfe")
        _, problem = cli.read_file(path, f"{RUN_A}/breakdown.md", str)
        repo.ledger(ledger(wo(1), 1.0))
        code, lines = run_main([], repo)
        self.assertEqual(lines[:2], [
            f"{PREFIX} {problem}",
            f"{PREFIX} excluded 1 row(s) whose wo names no sized breakdown"
            " row"])
        self.assertEqual(lines[-1], f"{PREFIX} 0 work order(s), 1 problem(s)")
        self.assertEqual(code, 1)

    def test_any_argument_is_a_usage_error(self):
        repo = Repo(self)
        code, lines = run_main(["--record"], repo)
        self.assertEqual(lines, [f"{PREFIX} '--record' — unknown argument",
                                 "", f"  {USAGE}"])
        self.assertEqual(code, 2)


class TestLocalAndReadOnly(unittest.TestCase):
    NETWORK = {"socket", "ssl", "http", "urllib", "ftplib", "smtplib",
               "requests", "asyncio"}

    def test_the_module_imports_no_network_module(self):
        source = (Path(__file__).resolve().parent.parent
                  / "size_band_calibration.py").read_text(encoding="utf-8")
        imported = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(imported & self.NETWORK, set())

    def test_the_live_measure_runs_only_read_only_git_verbs(self):
        repo = Repo(self)
        rows, entries = sized(1.0)
        repo.breakdown(RUN_A, *rows)
        repo.ledger(*entries)
        verbs = []

        def recorder(args, input=None, cwd=None):
            verbs.append(args[0])
            return SimpleNamespace(stdout="")
        code, _ = run_main([], repo, measure=decompose_signals.measure,
                           run=recorder)
        self.assertEqual(code, 0)
        self.assertTrue(verbs)
        self.assertLessEqual(set(verbs), {"for-each-ref", "log", "show"})


if __name__ == "__main__":
    unittest.main()
