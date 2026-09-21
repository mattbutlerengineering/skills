---
stage: capture
run: maintenance:a-gate-wait-is-not-spend
date: 2026-08-28
re-entry: implement
assumptions:
  - The shared rule is right and the outlier is wrong. Three readers use
    cost_ledger.dispatched and its docstring calls itself the one
    row-selection rule; the fix brings the fourth reader to it rather
    than relitigating what counts as spend.
  - A work order with only gate rows has no spend, not zero spend. Both
    docstrings in play say so in as many words, and the page already
    renders the two differently.
---

# Defect — the console counts a gate wait as a $0.00 run

## Summary

`dashboard._spend` sums `cost` over every row `cost_ledger.read` returns:

```python
def _spend(entries):
    """{WO token: recorded ledger spend} over already-read entries. A
    work order with no rows has no spend (None downstream), never $0 —
    ..."""
    spend = {}
    for entry in entries:
        spend[entry["wo"]] = spend.get(entry["wo"], 0.0) + entry["cost"]
    return spend
```

Gate-latency observations (ADR-0041) are ledger rows. `gate_entry`
writes them with `model="none"`, `tokens=0` and `cost=0.0`, and they
record how long a work order waited at a human gate — not that anything
ran. So a work order whose only rows are gate observations acquires a
key in `_spend` with the value `0.0`, and `_output` puts that in the
console's factory-output table.

`dashboard.html` renders the two apart:

```js
`<td>${entry.spend == null ? "—"
  : esc(fmtMoney(entry.spend))}</td></tr>`;
```

`None` is an em dash, meaning not measured. `0.0` is `$0.00`, meaning
measured and free. The console shows the second where the first is true.

## The rule this skips, and who else keeps it

`cost_ledger.dispatched` exists for exactly this:

> The rows that count as spend, in ledger order: never a gate-latency
> observation (ADR-0041 — a wait record, not a run) [...]
>
> **The ONE row-selection rule** behind both month-to-date figures — the
> weekly report's spend breakdown and the work queue's circuit-breaker
> input — so the number ADR-0034's cap is compared against has one
> definition rather than one per caller.

`cost_report.aggregate` names the consequence of not keeping it:

> gate-latency observations (ADR-0041) are skipped, being wait records
> rather than runs, and counting them would inflate run_count and **pad
> by_wo with $0.00 lines**

That padding is what `_spend` does.

The sharpest part is that `dashboard.py` already knows. `_metrics`, forty
lines above `_spend`, is handed the same list from the same
`cost_ledger.read(root)` call at `dashboard.py:406`, and says:

> an absent or empty ledger is "no runs recorded yet", never a $0.00 that
> reads as measured-and-free. **cost_report.aggregate owns the rollup
> math (gate rows out of every spend figure)**

— and calls `cost_report.aggregate`, which calls `dispatched`. One module,
one ledger read, two functions, two definitions of a spend row.

## Reproduction

Against this repo's own committed ledger, no fixtures:

```
$ python3 -c "<read the ledger; compare _spend's keys to aggregate's by_wo>"
ledger rows: 41 problems: []
gate rows: 22  dispatched rows: 19
gate-only WOs: ['WO-0001', 'WO-0002', 'WO-0003', 'WO-0013']
WOs in _spend but not in aggregate.by_wo:
  ['WO-0001', 'WO-0002', 'WO-0003', 'WO-0013']
their console spend value: {'WO-0001': 0.0, 'WO-0002': 0.0,
                            'WO-0003': 0.0, 'WO-0013': 0.0}
```

Four work orders, today, in the console: `$0.00` where the page has an em
dash ready and the sibling metric already agrees they should have one.

## Impact

- **Four wrong cells right now**, and one more for every work order that
  passes a gate before its dispatch row is recorded.
- **Two numbers on one page disagree by construction.** `cost_per_wo` is
  `aggregate`'s lifetime total over `len(by_wo)` — a denominator that
  excludes gate-only work orders — while the table beside it lists them
  with a spend figure. A reader who counts the table's priced rows gets a
  different work-order count than the metric used.
- **The direction is the misleading one.** `$0.00` reads as "this work
  order ran and cost nothing", which is a claim about the factory's
  efficiency. The truth is "nothing has been recorded for it yet".

The dollar totals do not move — gate rows cost $0 — so no cap decision or
circuit breaker is affected. This is a reporting defect, not a spend one.

## Fix

`_spend` walks `cost_ledger.dispatched(entries)` instead of `entries`.
One call, and the module stops holding two definitions of a spend row.

## Breakdown

- [x] A work order whose only rows are gate observations has no spend.
      Criterion: `_spend` over a gate-only entry list returns `{}`, so
      `_output` emits `None` and the page renders an em dash.
- [x] Gate rows do not perturb a work order that did run. Criterion: a
      work order with a dispatched row and a gate row sums to the
      dispatched row's cost alone, and remains present.
- [x] The console's two ledger readers agree on the work-order set.
      Criterion: over any entry list, `_spend`'s keys equal
      `cost_report.aggregate(entries)["by_wo"]`'s keys.
- [x] The rule is not re-implemented. Criterion: a test that
      `cost_ledger.dispatched` is what does the filtering, so a future
      change to the rule reaches the console without a second edit.
- [x] Non-vacuity. Criterion: the fixture used above genuinely contains
      a gate row and a dispatched row, asserted, so the tests cannot pass
      by testing an empty set.
