#!/usr/bin/env python3
"""conductor_close: `conductor.py scorecard <batch>` and `conductor.py
close <batch>` (PRD-0013, WO-0162, WO-0163), split from conductor.py by
capability (breakdown assumption 6). It imports conductor.py's row
grammar, which keeps one owner.

The scorecard is computed from the batch ledger and docs/factory/
costs.jsonl alone. It fails loudly, never reporting a number, when a
ledger line does not parse or breaks its kind's rules, when a `run` row
has no spend row of the same run_id, or when the plan row is missing:
each a cd: problem naming the file (and line). The Conductor's own
session is outside every dollar figure, and the row says so.
"""
import json
from datetime import datetime, timezone

import conductor_flow as flow
import cost_ledger
import factory_config
from conductor import AT_FORMAT, current_state, numbered, parse, \
    read_text, stamp

SCORECARDS = "docs/factory/scorecards.jsonl"
# Asks the Conductor raises beyond the planned spend, gate and merge
# decisions.
ESCALATIONS = ("stall", "clarify")
PLACES = 4


def _at(value):
    return datetime.strptime(value, AT_FORMAT).replace(tzinfo=timezone.utc)


def _ratio(numerator, denominator):
    return round(numerator / denominator, PLACES) if denominator else None


def _complies(run, policy):
    """True when the run's passed model and effort are the plan's policy
    snapshot for its band, and the harness reported the passed model."""
    model, _ = factory_config.resolve_model(run["band"], policy)
    effort, _ = factory_config.resolve_effort(run["band"], policy)
    return (run["model"] == model and run["effort"] == effort
            and run["model"] in run["models_reported"])


def _owner_wait_hours(rows):
    """The summed ask-to-answer wait of every answered ask, in hours."""
    asked = {row["id"]: row["at"] for row in rows if row["kind"] == "ask"}
    return sum((_at(row["at"]) - _at(asked[row["ask"]])).total_seconds()
               for row in rows if row["kind"] == "answer"
               and row["ask"] in asked) / 3600


def _review_changes(rows):
    """Requests for changes: a review sent back to build, and a second
    request that stalled the item."""
    return sum(1 for row in rows if row["kind"] == "state"
               and row["from"] == "review"
               and (row["to"] == "build" or row["reason"]
                    == flow.CHANGES_AGAIN))


def compute(rows, lines, shown, entries, now):
    """(scorecard row, problems), PURE over the ledger's rows (each on
    its line in `lines`) and the cost ledger's entries."""
    plan = flow.plan_row(rows)
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
    items = [entry["item"] for entry in plan["items"]]
    finals = [current_state(rows, item) for item in items]
    merged = finals.count("merged")
    metered = round(sum(spent[row["run_id"]] for _, row in runs), PLACES)
    estimate = plan["estimate_usd"]
    merges = [row["at"] for row in rows if row["kind"] == "state"
              and row["to"] == "merged"]
    wait = _owner_wait_hours(rows)
    return {
        "batch": plan["batch"], "at": stamp(now), "items": len(items),
        "merged": merged, "blocked": finals.count("blocked"),
        "owner_touches_per_merged": _ratio(
            sum(1 for row in rows if row["kind"] == "answer"), merged),
        "metered_usd": metered,
        "metered_usd_per_merged": _ratio(metered, merged),
        "estimate_usd": estimate,
        "estimate_error_pct": (round((metered - estimate) / estimate * 100,
                                     PLACES) if estimate else None),
        "collisions": sum(len(row.get("renumbered_from", []))
                          for row in rows if row["kind"] == "reserve"),
        "stalls": sum(1 for row in rows if row["kind"] == "state"
                      and row["to"] == "stalled"),
        "escalations": sum(1 for row in rows if row["kind"] == "ask"
                           and row["ask_kind"] in ESCALATIONS),
        "review_changes_per_item": _ratio(_review_changes(rows), len(items)),
        "start_to_last_merge_s": (int((_at(max(merges)) - _at(plan["at"]))
                                      .total_seconds()) if merges else None),
        "merged_per_owner_wait_hour": _ratio(merged, wait),
        "policy_compliance": _ratio(
            sum(1 for _, row in runs if _complies(row, plan["policy"])),
            len(runs)),
        "conductor_session": "unmetered"}, []


def scorecard(root, batch, now):
    """(scorecard row, problems) for the batch, from its ledger and the
    cost ledger at `root`."""
    text, shown, problems = read_text(root, batch)
    if problems:
        return None, problems
    rows, problems = parse(text, shown)
    if problems:
        return None, problems
    entries, problems = cost_ledger.read(root)
    if problems:
        return None, problems
    return compute(rows, [lineno for lineno, _ in numbered(text)], shown,
                   entries, now)


def scorecard_cli(root, args, now):
    if len(args) != 1:
        return None
    card, problems = scorecard(root, args[0], now)
    if card is not None:
        print(json.dumps(card, indent=2))
    return problems
