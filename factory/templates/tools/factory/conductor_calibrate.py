#!/usr/bin/env python3
"""conductor_calibrate: `conductor.py calibrate` (#799), split from
conductor_close by capability (breakdown assumption 6) when the
scorecard's row shape (#814) and cause counts (#819) would have pushed
that file past the 800-line ceiling. It imports conductor.py's row
grammar and conductor_close's rounding, which keep one owner each.

`calibrate` joins every closed batch's ledger with costs.jsonl into one
actuals row per run (step, band, model, ceiling, cost, wall time,
attempt, outcome) and prints suggested step weights and size budgets
with their sample sizes. It reads the ledgers close already commits, so
it writes no file of its own, and never writes factory.json.
"""
import json
import math
from pathlib import Path

import cost_ledger
from conductor import LEDGER, numbered, parse, parsed_at, read_text, view
from conductor_close import PLACES

# The fewest samples calibrate suggests from. One real batch is all
# there is today, so below it the verb prints n and suggests nothing.
CALIBRATE_FLOOR = 5


def actuals(rows, lines, shown, entries):
    """(one row per run, problems), PURE over the ledger's rows (each on
    its line in `lines`) and the cost ledger's entries: the join a
    recalibration needs, from the plan row (item type, size, the step's
    ceiling), the run row (band, model, effort, outcome), its spend rows
    and its launch state row (wall time; None for a run with none).
    `attempt` counts the item's runs of that step so far. It fails with
    no rows where the scorecard does: no plan row, or a run with no
    spend row."""
    plan = view(rows)["plan"]
    if plan is None:
        return None, [f"cd: {shown} has no plan row"]
    spent = {}
    for entry in entries:
        spent[entry["run_id"]] = spent.get(entry["run_id"], 0) \
            + entry["cost"]
    runs = [(lineno, row) for lineno, row in zip(lines, rows)
            if row["kind"] == "run"]
    problems = [f"cd: {shown}:{lineno} run {row['run_id']} has no"
                f" {cost_ledger.COST_LEDGER} row with its run_id"
                for lineno, row in runs if row["run_id"] not in spent]
    if problems:
        return None, problems
    launched = {row["run_id"]: row["at"] for row in rows
                if row["kind"] == "state" and row["to"] == "launched"}
    planned = {entry["item"]: entry for entry in plan["items"]}
    found, seen = [], {}
    for _, row in runs:
        entry, key = planned[row["item"]], (row["item"], row["step"])
        seen[key] = seen.get(key, 0) + 1
        start = launched.get(row["run_id"])
        found.append({
            "batch": plan["batch"], "item": row["item"],
            "type": entry["type"], "size": entry["size"],
            "step": row["step"], "attempt": seen[key],
            "run_id": row["run_id"], "band": row["band"],
            "model": row["model"], "effort": row["effort"],
            "ceiling_usd": next(step["ceiling_usd"] for step in entry["steps"]
                                if step["step"] == row["step"]),
            "cost_usd": round(spent[row["run_id"]], PLACES),
            "wall_s": (int((parsed_at(row["at"]) - parsed_at(start))
                           .total_seconds()) if start else None),
            "outcome": row["outcome"]})
    return found, []


def _spread(samples):
    return {"n": len(samples),
            "mean_usd": round(sum(samples) / len(samples), 2),
            "max_usd": round(max(samples), 2)}


def _short(table, what, floor):
    """[] when every entry of `table` has `floor` samples, else the one
    refusal naming each n below it and what has it."""
    under = {}
    for name, figures in table.items():
        if figures["n"] < floor:
            under.setdefault(figures["n"], []).append(name)
    if not under:
        return []
    return [f"{what}: " + "; ".join(f"n={n} for {', '.join(names)}"
                                    for n, names in sorted(under.items()))
            + f", below the floor of {floor}"]


def calibrate(rows, floor=CALIBRATE_FLOOR):
    """Suggested step weights and size budgets, PURE over actuals rows,
    with every figure's sample size. A step's sample is one item's spend
    on it over every attempt (ceiling_hits counts the attempts that spent
    their ceiling); a size's is one item's whole spend. The weights are
    each step's mean over the cheapest step's, suggested only when every
    step has `floor` samples; a size's budget is its dearest item,
    rounded up to the dollar, suggested only at `floor` items. It
    suggests and never writes factory.json: model and pricing choices
    stay the Owner's (PRD-0013, ADR-0034)."""
    by_step, by_item, sizes, attempts, hits = {}, {}, {}, {}, {}
    for row in rows:
        item, step, cost = (row["batch"], row["item"]), row["step"], \
            row["cost_usd"]
        by_step.setdefault(step, {})[item] = \
            by_step.get(step, {}).get(item, 0) + cost
        by_item[item] = by_item.get(item, 0) + cost
        sizes[item] = row["size"]
        attempts[step] = attempts.get(step, 0) + 1
        hits[step] = hits.get(step, 0) + (cost >= row["ceiling_usd"])
    steps = {step: {**_spread(list(items.values())),
                    "attempts": attempts[step], "ceiling_hits": hits[step]}
             for step, items in by_step.items()}
    totals = {}
    for item, total in by_item.items():
        totals.setdefault(sizes[item], []).append(total)
    budgets = {size: _spread(spent) for size, spent in totals.items()}
    for figures in budgets.values():
        figures["budget_usd"] = (math.ceil(figures["max_usd"])
                                 if figures["n"] >= floor else None)
    weights_short = _short(steps, "step_weights", floor)
    cheapest = min((figures["mean_usd"] for figures in steps.values()),
                   default=0)
    weights = None if weights_short or not cheapest else {
        step: round(figures["mean_usd"] / cheapest, 1)
        for step, figures in steps.items()}
    refused = ([] if rows else
               ["no closed batch has a run to calibrate from"])
    return {"floor": floor, "steps": steps, "step_weights": weights,
            "sizes": budgets,
            "refused": refused + weights_short
            + _short(budgets, "budgets_usd", floor)}


def closed_actuals(root):
    """(actuals rows of every closed batch's ledger at `root`, problems).
    A batch with no close row is skipped: its blocked items' spend rows
    reach costs.jsonl only at close."""
    entries, problems = cost_ledger.read(root)
    if problems:
        return None, problems
    found = []
    for ledger in sorted(Path(root).glob(LEDGER.format(batch="*"))):
        text, shown, problems = read_text(root, ledger.parent.name)
        rows, problems = (None, problems) if problems \
            else parse(text, shown)
        if problems:
            return None, problems
        if not any(row["kind"] == "close" for row in rows):
            continue
        rows, problems = actuals(rows, [n for n, _ in numbered(text)],
                                 shown, entries)
        if problems:
            return None, problems
        found += rows
    return found, []


def calibrate_cli(root, args):
    if args:
        return None
    rows, problems = closed_actuals(root)
    if rows is not None:
        print(json.dumps(calibrate(rows), indent=2))
    return problems
