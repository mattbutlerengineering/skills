#!/usr/bin/env python3
"""size-band-calibration: each S/M/L band's past cost error, from the ledger.

Step 2 of the Decompose learning loop (issue #987; the run is
docs/features/size-band-calibration/, ADR-0112's import edges). Each
metered work order's cost is compared with its band's budget as Balanced
Relative Error, and a band's nearest-rank P10, P50 and P90 are printed
only when it holds at least the calibrate floor's work orders.

READ-ONLY AND LOCAL. The band is joined at read time, from a ledger row's
work-order token to the `size:` of the breakdown row that names it; the
ledger gains no field (Owner decision 4). No cost is ever estimated for a
row that recorded none, and no number is written by hand: every figure is
computed from the ledger and the breakdowns.

NOT A GATE. A refusal below the floor and a band with no joined row are
data, not problems.
"""
import math
from collections import Counter

import cost_ledger
from factory_config import resolve_budget, resolve_calibrate_floor
from knowledge_plane import parse_row

LABEL = "size-band-calibration"
BANDS = ("S", "M", "L")


def bands(files, root):
    """(mapping, ambiguous): mapping is {wo: {size, run}} from every
    breakdown row that names a work order and a size; `files` is
    (breakdown path, lines) as knowledge_plane.breakdown_files yields it
    and `run` the run directory relative to `root`. A token under two
    different sizes is left out of the mapping and named in `ambiguous`;
    a row with no size is never defaulted."""
    found = {}
    for path, lines in files:
        run = path.parent.relative_to(root).as_posix()
        for record in filter(None, map(parse_row, lines)):
            if record["wo"] is not None and record["size"] is not None:
                found.setdefault(record["wo"], set()).add(
                    (record["size"], run))
    ambiguous = frozenset(token for token, seen in found.items()
                          if len({size for size, _ in seen}) > 1)
    mapping = {token: {"size": size, "run": run}
               for token, seen in found.items() if token not in ambiguous
               for size, run in [min(seen)]}
    return mapping, ambiguous


def _unusable(entry, mapping, ambiguous):
    """The exclusion a dispatched row falls into, or None when it is used."""
    if entry["cost"] == 0:
        return "zero_cost"
    if entry["wo"] in ambiguous:
        return "ambiguous"
    if entry["wo"] not in mapping:
        return "unjoined"
    return None


def select(entries, mapping, ambiguous):
    """(used rows, exclusion counts) over validated ledger entries. Each
    row is counted once, in this order: gate-latency rows, owner-session
    rows, dispatched rows with cost 0, dispatched rows whose token has
    conflicting sizes, then dispatched rows whose token names no sized
    breakdown row. The gate and owner predicates are cost_ledger's own."""
    spend = cost_ledger.dispatched(entries)
    gate = sum(1 for e in entries if cost_ledger.gate_wait(e) is not None)
    owner = sum(1 for e in entries if cost_ledger.owner_session(e))
    reasons = [(e, _unusable(e, mapping, ambiguous)) for e in spend]
    counts = Counter(reason for _, reason in reasons if reason)
    return [e for e, reason in reasons if reason is None], {
        "gate": gate, "owner_session": owner,
        "zero_cost": counts["zero_cost"], "unjoined": counts["unjoined"],
        "ambiguous": counts["ambiguous"]}


def work_orders(used, mapping):
    """One sample per work order, in token order: the sum of the cost of
    every used row naming it, over every attempt and step."""
    totals = Counter()
    for entry in used:
        totals[entry["wo"]] += entry["cost"]
    return [{"wo": token, "band": mapping[token]["size"],
             "run": mapping[token]["run"], "cost": totals[token]}
            for token in sorted(totals)]


def bre(actual, estimate):
    """Balanced Relative Error, signed: (actual - estimate) divided by the
    smaller of the two, so a cost of twice the estimate reads +1 and half
    the estimate reads -1. Both are positive: zero-cost rows are excluded
    before a work order exists, and resolve_budget refuses a non-positive
    budget."""
    return (actual - estimate) / min(actual, estimate)


def interval(values, floor):
    """None below `floor` values, else the nearest-rank P10, P50 and P90:
    rank ceil(p * n / 100) of the sorted values, 1-based, no
    interpolation, so every figure returned was measured."""
    ordered = sorted(values)
    if len(ordered) < floor:
        return None
    return {f"p{p}": ordered[math.ceil(p * len(ordered) / 100) - 1]
            for p in (10, 50, 90)}


def over_budget(values):
    """How many BRE values are an overrun: above the band's budget."""
    return sum(1 for value in values if value > 0)


def band_stats(band, orders, config):
    """(stats, problems) for one band's work orders. The budget and the
    floor are factory_config's (the band's budgets_usd entry and
    conductor.calibrate_floor); stats is None with the config problems
    when either cannot be resolved. `bre` is sorted."""
    budget, problems = resolve_budget(band, config)
    floor, floor_problems = resolve_calibrate_floor(config)
    if problems or floor_problems:
        return None, problems + floor_problems
    costs = [o["cost"] for o in orders if o["band"] == band]
    errors = sorted(bre(cost, budget) for cost in costs)
    return {"band": band, "n": len(costs), "budget": budget, "floor": floor,
            "bre": errors, "interval": interval(errors, floor),
            "over": over_budget(errors), "cost_total": sum(costs),
            "cost_mean": sum(costs) / len(costs) if costs else 0.0}, []
