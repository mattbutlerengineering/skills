"""conductor_calibrate.py's per-step actuals and `calibrate` (#799): one row
per run joined from the batch ledger and the cost ledger, and pricing
suggestions over those rows that print their sample sizes and refuse
below a floor. The fixture is consumer batch b20261013 (#6367, size M,
spec weighted 3): spec spent $5.83 of its $6.44 ceiling, build passed
its $2.14 ceiling once then completed, review spent its ceiling twice
and the item was blocked. Its launch rows are built by
conductor_flow.state_row, the writer conductor_run launches through, so
the fixture cannot invent a row shape no writer emits (#829). Tests
assert the EXACT rows, suggestions and problem strings.
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


def write(root, ledgers, costs):
    root = Path(root)
    config = root / ".github/factory.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("{}\n", encoding="utf-8")
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


class TestCalibrate(unittest.TestCase):
    def test_below_the_floor_it_prints_n_and_suggests_nothing(self):
        self.assertEqual(cal.calibrate(ACTUALS, WEIGHTS), {
            "floor": 5,
            "steps": {
                "spec": {"n": 1, "attempts": 1, "ceiling_hits": 0,
                         "mean_usd": 5.83, "max_usd": 5.83},
                "build": {"n": 1, "attempts": 2, "ceiling_hits": 1,
                          "mean_usd": 3.47, "max_usd": 3.47},
                "verify": {"n": 1, "attempts": 1, "ceiling_hits": 0,
                           "mean_usd": 0.9, "max_usd": 0.9},
                "review": {"n": 1, "attempts": 2, "ceiling_hits": 2,
                           "mean_usd": 4.28, "max_usd": 4.28}},
            "step_weights": None,
            "sizes": {"M": {"n": 1, "mean_usd": 14.48, "max_usd": 14.48,
                            "budget_usd": None}},
            "refused": ["step_weights: no run of ship to scale its weight"
                        " from",
                        "step_weights: n=1 for spec, build, verify, review,"
                        " below the floor of 5",
                        "budgets_usd: n=1 for M, below the floor of 5"]})

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
            "refused": ["no closed batch has a run to calibrate from"]})


class TestCalibrateCli(unittest.TestCase):
    def main(self, root, argv):
        return cli_contract.capture(conductor.main, argv, env={},
                                    clock=lambda: NOW, root=root)

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
