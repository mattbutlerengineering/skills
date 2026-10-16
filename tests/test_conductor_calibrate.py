"""conductor_calibrate.py's per-step actuals and `calibrate` (#799): one row
per run joined from the batch ledger and the cost ledger, and pricing
suggestions over those rows that print their sample sizes and refuse
below a floor. The fixture is consumer batch b20261013 (#6367, size M,
spec weighted 3): spec spent $5.83 of its $6.44 ceiling, build passed
its $2.14 ceiling once then completed, review spent its ceiling twice
and the item was blocked. Its launch rows are built by
conductor_flow.state_row, the writer conductor_run launches through, so
the fixture cannot invent a row shape no writer emits (#829). Its build
rows carry the item in `wo`, as that batch's tools wrote them (#940), so
they are attempts and hits but no build sample. Tests assert the EXACT
rows, suggestions, warnings and problem strings.
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import conductor
import conductor_calibrate as cal
import conductor_flow as flow
import factory_config

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402

BATCH = "b20261013"
NOW = datetime(2026, 10, 13, 20, 0, tzinfo=timezone.utc)
POLICY = {"routing": {"implementation": "s", "architecture_review": "f"},
          "effort": {"implementation": "medium",
                     "architecture_review": "high"}}
CEILINGS = {"spec": 6.44, "build": 2.14, "verify": 2.14, "review": 2.14,
            "ship": 2.14}
BANDS = {"spec": "architecture_review", "review": "architecture_review"}
WEIGHTS = factory_config.DEFAULT_STEP_WEIGHTS


def when(hour, minute=0):
    return datetime(2026, 10, 13, hour, minute, tzinfo=timezone.utc)


def at(hour, minute=0):
    return conductor.stamp(when(hour, minute))


def planned(step):
    band = BANDS.get(step, "implementation")
    return {"step": step, "charter": "c", "band": band,
            "model": POLICY["routing"][band],
            "effort": POLICY["effort"][band],
            "ceiling_usd": CEILINGS[step]}


def plan(batch=BATCH, item="#6367"):
    return {"at": at(9), "kind": "plan", "item": None, "batch": batch,
            "items": [{"item": item, "type": "feature", "size": "M",
                       "steps": [planned(step) for step in CEILINGS],
                       "estimate_usd": 15, "after": []}],
            "policy": POLICY, "estimate_usd": 15, "month_to_date_usd": 0.0,
            "cap_usd": 300}


def run_id(step, seq, batch=BATCH, item="#6367"):
    return conductor.run_id(batch, item, step, seq)


def attempt(step, seq, start, end, outcome, batch=BATCH, item="#6367"):
    """The launch state row and the run row of one Worker run: the launch
    as conductor_run writes it, through flow.state_row."""
    band = BANDS.get(step, "implementation")
    rid = run_id(step, seq, batch, item)
    return [flow.state_row(start, item, "x", step, flow.LAUNCHED,
                           run_id=rid, pid=7),
            {"at": conductor.stamp(end), "kind": "run", "item": item,
             "step": step,
             "charter": "c", "band": band, "model": POLICY["routing"][band],
             "models_reported": [POLICY["routing"][band]],
             "effort": POLICY["effort"][band], "run_id": rid, "pid": 7,
             "outcome": outcome}]


ROWS = [plan(),
        *attempt("spec", 1, when(10), when(10, 40), "completed"),
        *attempt("build", 1, when(11), when(11, 30), "agent-failed"),
        *attempt("build", 2, when(12), when(12, 20), "completed"),
        *attempt("verify", 1, when(13), when(13, 10), "completed"),
        *attempt("review", 1, when(14), when(14, 30), "agent-failed"),
        *attempt("review", 2, when(15), when(15, 30), "agent-failed")]
CLOSED = {"at": at(19), "kind": "close", "item": None, "merged": [],
          "blocked": ["#6367"]}


def spend(rid, cost, wo="#6367"):
    return {"wo": wo, "run_id": rid, "model": "s", "tokens": 10,
            "cost": cost, "outcome": "completed", "at": "2026-10-13"}


SPEND = [spend(run_id("spec", 1), 5.83), spend(run_id("build", 1), 2.17),
         spend(run_id("build", 2), 1.30), spend(run_id("verify", 1), 0.9),
         spend(run_id("review", 1), 2.14), spend(run_id("review", 2), 2.14)]


def actual(step, seq, band, model, effort, cost, wall_s, outcome):
    return {"batch": BATCH, "item": "#6367", "type": "feature", "size": "M",
            "step": step, "wo": "#6367", "attempt": seq,
            "run_id": run_id(step, seq),
            "band": band, "model": model, "effort": effort,
            "ceiling_usd": CEILINGS[step], "cost_usd": cost,
            "wall_s": wall_s, "outcome": outcome}


ACTUALS = [
    actual("spec", 1, "architecture_review", "f", "high", 5.83, 2400,
           "completed"),
    actual("build", 1, "implementation", "s", "medium", 2.17, 1800,
           "agent-failed"),
    actual("build", 2, "implementation", "s", "medium", 1.3, 1200,
           "completed"),
    actual("verify", 1, "implementation", "s", "medium", 0.9, 600,
           "completed"),
    actual("review", 1, "architecture_review", "f", "high", 2.14, 1800,
           "agent-failed"),
    actual("review", 2, "architecture_review", "f", "high", 2.14, 1800,
           "agent-failed")]


def lines(rows):
    return "".join(json.dumps(row) + "\n" for row in rows)


def write(root, ledgers, costs, config=None):
    root = Path(root)
    path = root / ".github/factory.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config or {}) + "\n", encoding="utf-8")
    for batch, rows in ledgers.items():
        path = root / conductor.LEDGER.format(batch=batch)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(lines(rows), encoding="utf-8")
    path = root / "docs/factory/costs.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(lines(costs), encoding="utf-8")


class TestActuals(unittest.TestCase):
    def test_one_row_per_run_joins_plan_launch_run_and_spend(self):
        self.assertEqual(cal.actuals(ROWS, range(1, len(ROWS) + 1),
                                       "L", SPEND), (ACTUALS, []))

    def test_a_run_with_no_spend_row_fails_naming_its_line(self):
        self.assertEqual(cal.actuals(ROWS, range(1, len(ROWS) + 1), "L",
                                       SPEND[1:]),
                         (None, [f"cd: L:3 run {run_id('spec', 1)} has no"
                                 " docs/factory/costs.jsonl row with its"
                                 " run_id"]))

    def test_wall_time_reads_the_launch_row_the_conductor_writes(self):
        found, _ = cal.actuals(ROWS, range(1, len(ROWS) + 1), "L", SPEND)
        self.assertEqual([row["wall_s"] for row in found],
                         [2400, 1800, 1200, 600, 1800, 1800])

    def test_a_run_for_an_item_the_plan_does_not_hold_fails(self):
        stray = {**ROWS[-1], "item": "#9"}
        rows = ROWS + [stray]
        self.assertEqual(cal.actuals(rows, range(1, len(rows) + 1), "L",
                                       SPEND),
                         (None, [f"cd: L:{len(rows)} run"
                                 f" {run_id('review', 2)} is for #9, which"
                                 " the plan does not hold"]))

    def test_a_run_of_a_step_the_plan_does_not_give_its_item_fails(self):
        stray = {**ROWS[-1], "step": "deploy"}
        rows = ROWS + [stray]
        self.assertEqual(cal.actuals(rows, range(1, len(rows) + 1), "L",
                                       SPEND),
                         (None, [f"cd: L:{len(rows)} run"
                                 f" {run_id('review', 2)} is a deploy run,"
                                 " a step the plan does not give #6367"]))

    def test_a_missing_plan_row_fails(self):
        self.assertEqual(cal.actuals(ROWS[1:], range(1, len(ROWS)), "L",
                                       SPEND),
                         (None, ["cd: L has no plan row"]))


def batch_of(batch, item, costs, build_rows=1):
    """A further closed batch: one item, every step completing first
    time at `costs[step]`, and build run once per breakdown row (each
    row its own work order, at `costs['build']`)."""
    rows, spent = [plan(batch, item)], []
    seq = {}
    hour = 10
    for step in CEILINGS:
        for row in range(1, (build_rows if step == "build" else 1) + 1):
            seq[step] = seq.get(step, 0) + 1
            rows += attempt(step, seq[step], when(hour), when(hour, 10),
                            "completed", batch, item)
            wo = f"WO-{row:04d}" if step == "build" else item
            spent.append(spend(run_id(step, seq[step], batch, item),
                               costs[step], wo))
            hour += 1
    return rows, spent


def actuals_of(costs, build_rows=1, batches=5):
    rows = []
    for n in range(1, batches + 1):
        ledger, spent = batch_of(f"b{n}", f"#{n}", costs, build_rows)
        found, problems = cal.actuals(
            ledger, range(1, len(ledger) + 1), "L", spent)
        assert problems == [], problems
        rows += found
    return rows


BUILD_ASIDE = ("build: 2 run(s) set aside from the sample: their spend row"
               " names the item, not a work order (older tools, or a runner"
               " lost before it metered); they still count as attempts")
BUILD_WARNING = ("build: 1 of 2 attempts spent the ceiling; the weight is"
                 " too low")
REVIEW_WARNING = ("review: 2 of 2 attempts spent the ceiling; the weight is"
                  " too low")


class TestCalibrate(unittest.TestCase):
    def test_below_the_floor_it_prints_n_and_suggests_nothing(self):
        self.assertEqual(cal.calibrate(ACTUALS, WEIGHTS), {
            "floor": 5,
            "steps": {
                "spec": {"n": 1, "attempts": 1, "ceiling_hits": 0,
                         "mean_usd": 5.83, "max_usd": 5.83},
                "build": {"n": 0, "attempts": 2, "ceiling_hits": 1,
                          "mean_usd": None, "max_usd": None},
                "verify": {"n": 1, "attempts": 1, "ceiling_hits": 0,
                           "mean_usd": 0.9, "max_usd": 0.9},
                "review": {"n": 1, "attempts": 2, "ceiling_hits": 2,
                           "mean_usd": 4.28, "max_usd": 4.28}},
            "step_weights": None,
            "sizes": {"M": {"n": 1, "mean_usd": 14.48, "max_usd": 14.48,
                            "budget_usd": None}},
            "warnings": [BUILD_WARNING, REVIEW_WARNING],
            "set_aside": [BUILD_ASIDE],
            "refused": ["step_weights: no run of build to scale its weight"
                        " from",
                        "step_weights: no run of ship to scale its weight"
                        " from",
                        "step_weights: n=0 for build; n=1 for spec, verify,"
                        " review, below the floor of 5",
                        "budgets_usd: n=1 for M, below the floor of 5"]})

    def test_the_floor_is_the_callers(self):
        # #940: five is many batches for a single-owner repo.
        card = cal.calibrate(ACTUALS, WEIGHTS, floor=1)
        self.assertEqual(card["floor"], 1)
        self.assertEqual(card["sizes"]["M"]["budget_usd"], 15)
        self.assertEqual(card["refused"], [
            "step_weights: no run of build to scale its weight from",
            "step_weights: no run of ship to scale its weight from",
            "step_weights: n=0 for build, below the floor of 1"])

    def test_steps_spending_their_ceilings_suggest_the_weights_in_force(self):
        card = cal.calibrate(actuals_of(CEILINGS), WEIGHTS)
        self.assertEqual(card["step_weights"], WEIGHTS)
        self.assertEqual(card["refused"], [])

    def test_weights_scale_each_step_by_its_spend_over_its_ceiling(self):
        costs = {"spec": 6.44, "build": 2.14, "verify": 1.07,
                 "review": 4.28, "ship": 1.07}
        card = cal.calibrate(actuals_of(costs), WEIGHTS)
        self.assertEqual(card["step_weights"], {
            "spec": 3.0, "build": 1.0, "verify": 0.5, "review": 6.0,
            "ship": 0.5})
        self.assertEqual(card["sizes"], {"M": {
            "n": 5, "mean_usd": 15.0, "max_usd": 15.0, "budget_usd": 15}})

    def test_a_build_sample_is_one_breakdown_rows_run(self):
        card = cal.calibrate(actuals_of(CEILINGS, build_rows=5), WEIGHTS)
        self.assertEqual(card["steps"]["build"], {
            "n": 25, "attempts": 25, "ceiling_hits": 25,
            "mean_usd": 2.14, "max_usd": 2.14})
        self.assertEqual(card["step_weights"]["build"], 1.0)

    def test_a_retried_row_is_one_sample_over_its_attempts(self):
        found, _ = cal.actuals(ROWS, range(1, len(ROWS) + 1), "L", SPEND)
        self.assertEqual([(row["step"], row["attempt"]) for row in found],
                         [("spec", 1), ("build", 1), ("build", 2),
                          ("verify", 1), ("review", 1), ("review", 2)])

    def test_a_zero_ceiling_refuses_rather_than_dividing(self):
        rows = [{**row, "ceiling_usd": 0} if row["step"] == "verify" else row
                for row in actuals_of(CEILINGS)]
        card = cal.calibrate(rows, WEIGHTS)
        self.assertIsNone(card["step_weights"])
        self.assertEqual(card["refused"], [
            "step_weights: verify has a $0 ceiling to scale its weight"
            " from"])

    def test_no_rows_suggests_nothing(self):
        self.assertEqual(cal.calibrate([], WEIGHTS), {
            "floor": 5, "steps": {}, "step_weights": None, "sizes": {},
            "warnings": [], "set_aside": [],
            "refused": ["no closed batch has a run to calibrate from"]})


def spec_rows(costs):
    """One spec row per batch, each spent `costs[i]` of the $6.44
    ceiling: a step's attempts across batches."""
    return [{**actual("spec", 1, "architecture_review", "f", "high", cost,
                      600, "completed"), "batch": f"b{n}", "item": f"#{n}",
             "wo": f"#{n}"} for n, cost in enumerate(costs, 1)]


class TestCeilingWarnings(unittest.TestCase):
    """#940: below the floor the counters still give a verdict. A step
    whose attempts spent their ceiling half the time or more, at two
    attempts or more, is underweighted; the suggestion cannot say so,
    because a run that stopped at its ceiling scales a weight down, not
    up."""

    def test_half_the_attempts_or_more_at_two_or_more_warns(self):
        self.assertEqual(cal.calibrate(ACTUALS, WEIGHTS)["warnings"],
                         [BUILD_WARNING, REVIEW_WARNING])

    def test_one_attempt_never_warns(self):
        card = cal.calibrate(spec_rows([6.44]), WEIGHTS)
        self.assertEqual(card["steps"]["spec"]["ceiling_hits"], 1)
        self.assertEqual(card["warnings"], [])

    def test_under_half_the_attempts_does_not_warn(self):
        self.assertEqual(
            cal.calibrate(spec_rows([6.44, 5.0, 5.0]), WEIGHTS)["warnings"],
            [])
        self.assertEqual(
            cal.calibrate(spec_rows([6.44, 5.0, 6.44, 5.0]),
                          WEIGHTS)["warnings"],
            ["spec: 2 of 4 attempts spent the ceiling; the weight is too"
             " low"])

    def test_it_warns_above_the_floor_too_where_the_suggestion_cannot(self):
        # Every run stopped at its ceiling: the scaled suggestion keeps
        # every weight (#830), and only the warning says they are low.
        card = cal.calibrate(actuals_of(CEILINGS), WEIGHTS)
        self.assertEqual(card["step_weights"], WEIGHTS)
        self.assertEqual(card["warnings"], [
            f"{step}: 5 of 5 attempts spent the ceiling; the weight is too"
            " low" for step in CEILINGS])

    def test_a_lost_runners_ceiling_row_is_a_hit(self):
        # #967: a runner lost before it metered is charged its step's
        # full ceiling, under the item, not a work order. The ceiling was
        # spent, whoever spent it.
        lost = [{**actual("review", 1, "architecture_review", "f", "high",
                          2.14, None, "runner-lost:cost-at-ceiling"),
                 "batch": f"b{n}", "item": f"#{n}", "wo": f"#{n}"}
                for n in (1, 2)]
        card = cal.calibrate(lost, WEIGHTS)
        self.assertEqual(card["steps"]["review"],
                         {"n": 2, "attempts": 2, "ceiling_hits": 2,
                          "mean_usd": 2.14, "max_usd": 2.14})
        self.assertEqual(card["warnings"], [REVIEW_WARNING])


class TestSetAside(unittest.TestCase):
    """#940: a build row keyed by its item, not a work order (older tools
    wrote the item into `wo`; a lost runner's row names the item, #967),
    collapses every such row of a batch into one unit against one row's
    ceiling. It is an attempt, and a hit when it spent the ceiling, but
    no unit of the sample, and the output says how many and why."""

    def rows(self):
        found = actuals_of(CEILINGS, build_rows=5)
        return [{**row, "wo": row["item"]}
                if row["step"] == "build" and row["batch"] == "b1" else row
                for row in found]

    def test_pre_work_order_build_rows_leave_the_sample_not_the_counts(self):
        card = cal.calibrate(self.rows(), WEIGHTS)
        self.assertEqual(card["steps"]["build"], {
            "n": 20, "attempts": 25, "ceiling_hits": 25,
            "mean_usd": 2.14, "max_usd": 2.14})
        self.assertEqual(card["step_weights"]["build"], 1.0)
        self.assertEqual(card["set_aside"], [
            "build: 5 run(s) set aside from the sample: their spend row"
            " names the item, not a work order (older tools, or a runner"
            " lost before it metered); they still count as attempts"])

    def test_their_spend_still_counts_toward_the_items_budget(self):
        self.assertEqual(cal.calibrate(self.rows(), WEIGHTS)["sizes"],
                         cal.calibrate(actuals_of(CEILINGS, build_rows=5),
                                       WEIGHTS)["sizes"])

    def test_a_lost_build_run_is_set_aside_and_a_hit(self):
        rows = [{**row, "wo": row["item"],
                 "outcome": "runner-lost:cost-at-ceiling"}
                if row["step"] == "build" and row["batch"] == "b1" else row
                for row in actuals_of(CEILINGS, build_rows=2)]
        card = cal.calibrate(rows, WEIGHTS)
        self.assertEqual(card["steps"]["build"],
                         {"n": 8, "attempts": 10, "ceiling_hits": 10,
                          "mean_usd": 2.14, "max_usd": 2.14})
        self.assertEqual(card["set_aside"][0][:34],
                         "build: 2 run(s) set aside from the")

    def test_a_step_keyed_by_its_item_is_never_set_aside(self):
        # Every step but build runs once per item under the item's key.
        card = cal.calibrate(actuals_of(CEILINGS), WEIGHTS)
        self.assertEqual(card["set_aside"], [])
        self.assertEqual(card["steps"]["spec"]["n"], 5)


class TestWarningLines(unittest.TestCase):
    """#940: `plan` prices the next batch from the same weights, so it
    repeats the warnings as its own lines. Advisory: a closed batch that
    does not join its spend rows is one line, never a problem."""

    def test_the_lines_plan_prints(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, {BATCH: ROWS + [CLOSED]}, SPEND)
            self.assertEqual(cal.warning_lines(tmp), [
                f"cd: {BUILD_WARNING}", f"cd: {REVIEW_WARNING}"])

    def test_no_closed_batch_prints_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cal.warning_lines(tmp), [])

    def test_a_batch_that_does_not_join_is_one_line_never_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, {BATCH: ROWS + [CLOSED]}, SPEND[1:])
            self.assertEqual(cal.warning_lines(tmp), [
                "cd: ceiling warnings unread: a closed batch does not join"
                " its spend rows (conductor.py calibrate names the problem)"])


class TestCalibrateCli(unittest.TestCase):
    def main(self, root, argv):
        return cli_contract.capture(conductor.main, argv, env={},
                                    clock=lambda: NOW, root=root)

    def test_the_floor_is_read_from_factory_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, {BATCH: ROWS + [CLOSED]}, SPEND,
                  config={"conductor": {"calibrate_floor": 1}})
            code, out = self.main(tmp, ["calibrate"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out[:out.rindex("}") + 1]),
                         cal.calibrate(ACTUALS, WEIGHTS, floor=1))

    def test_a_bad_floor_is_refused_before_any_ledger_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, {BATCH: ROWS + [CLOSED]}, SPEND,
                  config={"conductor": {"calibrate_floor": "5"}})
            code, out = self.main(tmp, ["calibrate"])
        self.assertEqual((code, out), (
            1, "config: factory.json conductor.calibrate_floor must be a"
               " positive integer\ncd: 1 problem(s)\n"))

    def test_reads_every_closed_batch_and_writes_nothing(self):
        # open1 has no close row and no spend rows: it is not read.
        other, _ = batch_of("open1", "#5", dict.fromkeys(CEILINGS, 1.0))
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, {BATCH: ROWS + [CLOSED], "open1": other}, SPEND)
            before = sorted(Path(tmp).rglob("*"))
            code, out = self.main(tmp, ["calibrate"])
            self.assertEqual(sorted(Path(tmp).rglob("*")), before)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out[:out.rindex("}") + 1]),
                         cal.calibrate(ACTUALS, WEIGHTS))

    def test_a_closed_batch_with_an_unmetered_run_reports_no_number(self):
        shown = conductor.LEDGER.format(batch=BATCH)
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, {BATCH: ROWS + [CLOSED]}, SPEND[1:])
            code, out = self.main(tmp, ["calibrate"])
        self.assertEqual((code, out), (
            1, f"cd: {shown}:3 run {run_id('spec', 1)} has no"
               " docs/factory/costs.jsonl row with its run_id\n"
               "cd: 1 problem(s)\n"))

    def test_an_unreadable_ledger_is_refused_not_a_failure(self):
        # #854: one bad ledger on main is append-only evidence; calibrate
        # names it under refused and reads every other closed batch, as
        # the miner counts it (#837), so conduct's read-back still runs.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, {BATCH: ROWS + [CLOSED]}, SPEND)
            bad = Path(tmp) / conductor.LEDGER.format(batch="good")
            bad.parent.mkdir(parents=True)
            bad.write_text("not json\n", encoding="utf-8")
            code, out = self.main(tmp, ["calibrate"])
        card = cal.calibrate(ACTUALS, WEIGHTS)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out[:out.rindex("}") + 1]), {
            **card, "refused": [
                "ledgers: good does not load, so its runs are left out",
                *card["refused"]]})

    def test_extra_arguments_print_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.main(tmp, ["calibrate", "x"])
        self.assertEqual(code, 2)
        self.assertIn("conductor.py calibrate", out)


if __name__ == "__main__":
    unittest.main()
