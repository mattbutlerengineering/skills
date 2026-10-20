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
import sys
from collections import Counter
from pathlib import Path

import cost_ledger
import decompose_signals
import factory_config
from cli import read_file, report, runner
from factory_config import (SIZES as BANDS, resolve_budget,
                            resolve_calibrate_floor)
from knowledge_plane import parse_row, repo_root, run_dirs

LABEL = "size-band-calibration"
USAGE = "python3 size_band_calibration.py"


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


def non_finite(entries):
    """Problem strings for dispatched rows whose cost is NaN or infinite.
    json.loads accepts both and the ledger shape rule (a non-negative
    number) lets them through; either would print as "$nan" or "+inf"
    in a figure that exits 0, so the report stops instead."""
    return [f"{LABEL}: ledger row for {entry['wo']} ({entry['run_id']}) has"
            f" a non-finite cost {entry['cost']!r}"
            for entry in cost_ledger.dispatched(entries)
            if not math.isfinite(entry["cost"])]


def _unusable(token, cost, mapping, ambiguous):
    """The exclusion a dispatched row falls into, or None when it is used."""
    if cost == 0:
        return "zero_cost"
    if token in ambiguous:
        return "ambiguous"
    if token not in mapping:
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
    reasons = [(e, _unusable(e["wo"], e["cost"], mapping, ambiguous))
               for e in spend]
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


UNREADABLE_HISTORY = "git history could not be read"
NO_RUN = "no run holds a work order of this band"
NOT_MEASURED = "run not in the measurement"


def _band_replan(runs, records):
    """One band's pooled re-plan figure from the runs holding its work
    orders: the sum of `count` over the sum of `items_at_d` across the
    measurable ones, the number of runs and of unmeasurable ones; or
    {unmeasurable: reason} when no contributing run is measurable. A
    run's figure is the run's, not a work order's."""
    if not runs:
        return {"unmeasurable": NO_RUN}
    replans = [records[run]["replan"] if run in records
               else {"unmeasurable": NOT_MEASURED} for run in sorted(runs)]
    measured = [r for r in replans if "unmeasurable" not in r]
    if not measured:
        return {"unmeasurable": replans[0]["unmeasurable"]}
    return {"count": sum(r["count"] for r in measured),
            "items": sum(r["items_at_d"] for r in measured),
            "runs": len(measured),
            "unmeasurable": len(replans) - len(measured)}


def replan_by_band(orders, measure, root, run):
    """(figures, problems): per band S, M and L, the re-plan rate pooled
    over the measurable runs that hold at least one of its work orders,
    joined on the run directory `bands` kept. `measure(root, run)` is
    decompose_signals.measure's contract, injected so tests pass a fixed
    result. A failed measurement passes its problems through and leaves
    every band unmeasurable; the rest of the report stands."""
    result, problems = measure(root, run)
    if result is None:
        return {band: {"unmeasurable": UNREADABLE_HISTORY}
                for band in BANDS}, problems
    records = {r["path"]: r for r in result["runs"]}
    return {band: _band_replan({o["run"] for o in orders
                                if o["band"] == band}, records)
            for band in BANDS}, problems


EXCLUSIONS = (
    ("owner_session", "owner-session:unmetered row(s) — cost never recorded,"
     " none estimated"),
    ("gate", "gate-latency row(s) — waits, not spend"),
    ("zero_cost", "row(s) with cost 0 — no cost recorded"),
    ("unjoined", "row(s) whose wo names no sized breakdown row"),
    ("ambiguous", "row(s) whose wo has conflicting sizes"))


def _replan_text(figure):
    if "count" not in figure:
        return f"re-plan unmeasurable — {figure['unmeasurable']}"
    return (f"re-plan {figure['count']}/{figure['items']} over"
            f" {figure['runs']} run(s) ({figure['unmeasurable']}"
            " unmeasurable)")


def _band_line(stats, figure):
    band, n = stats["band"], stats["n"]
    if n == 0:
        return (f"{LABEL}: band {band} — no metered work order joins this"
                " band; re-plan unmeasurable")
    replan = _replan_text(figure)
    total = f"${stats['cost_total']:.3f} total"
    if stats["interval"] is None:
        return (f"{LABEL}: band {band} — refused: n {n} work order(s) is"
                f" below the minimum of {stats['floor']}, no interval"
                f" printed; cost {total}; {replan}")
    p = stats["interval"]
    return (f"{LABEL}: band {band} — BRE P10 {p['p10']:+.3f}, P50"
            f" {p['p50']:+.3f}, P90 {p['p90']:+.3f} over {n} work order(s)"
            f" against a ${stats['budget']:g} budget (nearest rank; at"
            " n = 5 P10 and P90 are the observed range); over budget"
            f" {stats['over']} of {n}; cost ${stats['cost_mean']:.3f} mean,"
            f" {total}; {replan}")


def render(exclusions, stats, figures):
    """The report's lines, before the summary: one per nonzero exclusion
    in EXCLUSIONS' order, then one per band S, M and L. `stats` is
    {band: band_stats} and `figures` replan_by_band's."""
    lines = [f"{LABEL}: excluded {exclusions[key]} {text}"
             for key, text in EXCLUSIONS if exclusions[key]]
    return lines + [_band_line(stats[band], figures[band])
                    for band in BANDS]


def _config_problems(config):
    """band_stats' config problems for every band, each stated once."""
    found = [p for band in BANDS for p in band_stats(band, [], config)[1]]
    return list(dict.fromkeys(found))


def _read_breakdowns(root):
    """((path, lines) per readable breakdown, problems): read through
    cli.read_file, so an unreadable one is a labelled problem and its
    work orders fall into the unjoined exclusion."""
    files, problems = [], []
    for run_dir in run_dirs(root):
        path = run_dir / "breakdown.md"
        text, problem = read_file(
            path, path.relative_to(root).as_posix(), str)
        if problem:
            problems.append(f"{LABEL}: {problem}")
        elif text is not None:
            files.append((path, text.splitlines()))
    return files, problems


def main(argv, root=None, run=None, measure=decompose_signals.measure):
    """`python3 size_band_calibration.py` — print every exclusion and each
    band's interval or refusal beside its cost and re-plan rate. Exit 0
    when nothing failed (refusals and empty bands are data), 1 with
    problems, 2 on any argument."""
    if argv:
        print(f"{LABEL}: {' '.join(argv)!r} — unknown argument\n\n"
              f"  {USAGE}")
        return 2
    root = Path(root) if root is not None else repo_root()
    config, problems = factory_config.load(root)
    problems = problems or _config_problems(config)
    entries, ledger_problems = [], []
    if not problems:
        entries, ledger_problems = cost_ledger.read(root)
        ledger_problems = ledger_problems + non_finite(entries)
    if problems or ledger_problems:
        return report(LABEL, problems + ledger_problems,
                      prefix="0 work order(s), ")
    files, problems = _read_breakdowns(root)
    mapping, ambiguous = bands(files, root)
    used, exclusions = select(entries, mapping, ambiguous)
    orders = work_orders(used, mapping)
    run = run or runner("git", timeout=decompose_signals.GIT_TIMEOUT)
    figures, measure_problems = replan_by_band(orders, measure, root, run)
    stats = {band: band_stats(band, orders, config)[0] for band in BANDS}
    for line in render(exclusions, stats, figures):
        print(line)
    return report(LABEL, problems + measure_problems,
                  prefix=f"{len(orders)} work order(s), ")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
