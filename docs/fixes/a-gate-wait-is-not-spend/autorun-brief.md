# Autorun brief — a gate wait is not spend

## Scale

Maintenance run, `re-entry: implement`. Artifacts at
`docs/fixes/a-gate-wait-is-not-spend/`.

## What and why

`cost_ledger.dispatched` is documented as "The ONE row-selection rule"
for which ledger rows count as spend, and it exists because gate-latency
observations (ADR-0041) are $0 wait records rather than runs. Three
readers of the ledger honour it. `dashboard._spend` — a fourth reader,
sitting in the same module as one of the three and walking the same list
from the same `cost_ledger.read` call — sums every row instead.

The console therefore shows a measured `$0.00` for work orders that were
never dispatched. That is live today: four work orders in this repo's own
ledger have gate rows and nothing else.

## Scope

In scope: `dashboard._spend` and its tests.

Out of scope: `cost_ledger.py`, `cost_report.py` and `work_queue.py` —
they already hold the rule and need no change. `dashboard.html` — it
already distinguishes a null spend (renders an em dash) from a zero one
(renders `$0.00`); the page is right and the data feeding it is wrong.

## Constraints

Stdlib only. `_spend` stays pure over already-read entries.

## Success

A work order whose only ledger rows are gate-latency observations has no
spend in the console's factory-output table, and the module has one
definition of a spend row rather than two.

## Release authorization

None. Prepare and stop.
