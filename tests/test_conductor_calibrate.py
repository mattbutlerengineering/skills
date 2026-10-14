"""conductor_close.py's per-step actuals and `calibrate` (#799): one row
per run joined from the batch ledger and the cost ledger, and pricing
suggestions over those rows that print their sample sizes and refuse
below a floor. The fixture is consumer batch b20261013 (#6367, size M,
spec weighted 3): spec spent $5.83 of its $6.44 ceiling, build passed
its $2.14 ceiling once then completed, review spent its ceiling twice
and the item was blocked. Tests assert the EXACT rows, suggestions and
problem strings.
"""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import conductor
import conductor_close as close

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


def at(hour, minute=0):
    return f"2026-10-13T{hour:02d}:{minute:02d}:00Z"


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
    """The launch state row and the run row of one Worker run."""
    band = BANDS.get(step, "implementation")
    rid = run_id(step, seq, batch, item)
    return [{"at": start, "kind": "state", "item": item, "from": "x",
             "to": "launched", "reason": "r", "run_id": rid, "pid": 7},
            {"at": end, "kind": "run", "item": item, "step": step,
             "charter": "c", "band": band, "model": POLICY["routing"][band],
             "models_reported": [POLICY["routing"][band]],
             "effort": POLICY["effort"][band], "run_id": rid, "pid": 7,
             "outcome": outcome}]


ROWS = [plan(),
        *attempt("spec", 1, at(10), at(10, 40), "completed"),
        *attempt("build", 1, at(11), at(11, 30), "agent-failed"),
        *attempt("build", 2, at(12), at(12, 20), "completed"),
        *attempt("verify", 1, at(13), at(13, 10), "completed"),
        *attempt("review", 1, at(14), at(14, 30), "agent-failed"),
        *attempt("review", 2, at(15), at(15, 30), "agent-failed")]
CLOSED = {"at": at(19), "kind": "close", "item": None, "merged": [],
          "blocked": ["#6367"]}


def spend(rid, cost):
    return {"wo": "#6367", "run_id": rid, "model": "s", "tokens": 10,
            "cost": cost, "outcome": "completed", "at": "2026-10-13"}


SPEND = [spend(run_id("spec", 1), 5.83), spend(run_id("build", 1), 2.17),
         spend(run_id("build", 2), 1.30), spend(run_id("verify", 1), 0.9),
         spend(run_id("review", 1), 2.14), spend(run_id("review", 2), 2.14)]


def actual(step, seq, band, model, effort, cost, wall_s, outcome):
    return {"batch": BATCH, "item": "#6367", "type": "feature", "size": "M",
            "step": step, "attempt": seq, "run_id": run_id(step, seq),
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
    for batch, rows in ledgers.items():
        path = root / conductor.LEDGER.format(batch=batch)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(lines(rows), encoding="utf-8")
    path = root / "docs/factory/costs.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(lines(costs), encoding="utf-8")


class TestActuals(unittest.TestCase):
    def test_one_row_per_run_joins_plan_launch_run_and_spend(self):
        self.assertEqual(close.actuals(ROWS, range(1, len(ROWS) + 1),
                                       "L", SPEND), (ACTUALS, []))

    def test_a_run_with_no_spend_row_fails_naming_its_line(self):
        self.assertEqual(close.actuals(ROWS, range(1, len(ROWS) + 1), "L",
                                       SPEND[1:]),
                         (None, [f"cd: L:3 run {run_id('spec', 1)} has no"
                                 " docs/factory/costs.jsonl row with its"
                                 " run_id"]))

    def test_a_missing_plan_row_fails(self):
        self.assertEqual(close.actuals(ROWS[1:], range(1, len(ROWS)), "L",
                                       SPEND),
                         (None, ["cd: L has no plan row"]))


def batch_of(batch, item, costs):
    """A further closed batch: one item, every step completing first
    time at `costs[step]`."""
    rows = [plan(batch, item)]
    for hour, step in enumerate(CEILINGS, start=10):
        rows += attempt(step, 1, at(hour), at(hour, 10), "completed",
                        batch, item)
    return rows, [spend(run_id(step, 1, batch, item), costs[step])
                  for step in CEILINGS]


class TestCalibrate(unittest.TestCase):
    def test_below_the_floor_it_prints_n_and_suggests_nothing(self):
        self.assertEqual(close.calibrate(ACTUALS), {
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
            "refused": ["step_weights: n=1 for spec, build, verify, review,"
                        " below the floor of 5",
                        "budgets_usd: n=1 for M, below the floor of 5"]})

    def test_at_the_floor_it_suggests_weights_and_budgets(self):
        costs = {"spec": 6.0, "build": 3.0, "verify": 1.5, "review": 3.0,
                 "ship": 1.5}
        rows = []
        for n in range(1, 6):
            ledger, spent = batch_of(f"b{n}", f"#{n}", costs)
            found, problems = close.actuals(
                ledger, range(1, len(ledger) + 1), "L", spent)
            self.assertEqual(problems, [])
            rows += found
        card = close.calibrate(rows)
        self.assertEqual(card["step_weights"], {
            "spec": 4.0, "build": 2.0, "verify": 1.0, "review": 2.0,
            "ship": 1.0})
        self.assertEqual(card["sizes"], {"M": {
            "n": 5, "mean_usd": 15.0, "max_usd": 15.0, "budget_usd": 15}})
        self.assertEqual(card["refused"], [])

    def test_no_rows_suggests_nothing(self):
        self.assertEqual(close.calibrate([]), {
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
                         close.calibrate(ACTUALS))

    def test_a_closed_batch_with_an_unmetered_run_reports_no_number(self):
        shown = conductor.LEDGER.format(batch=BATCH)
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, {BATCH: ROWS + [CLOSED]}, SPEND[1:])
            code, out = self.main(tmp, ["calibrate"])
        self.assertEqual((code, out), (
            1, f"cd: {shown}:3 run {run_id('spec', 1)} has no"
               " docs/factory/costs.jsonl row with its run_id\n"
               "cd: 1 problem(s)\n"))

    def test_extra_arguments_print_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.main(tmp, ["calibrate", "x"])
        self.assertEqual(code, 2)
        self.assertIn("conductor.py calibrate", out)


if __name__ == "__main__":
    unittest.main()
