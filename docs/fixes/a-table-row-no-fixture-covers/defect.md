---
stage: capture
run: maintenance:a-table-row-no-fixture-covers
date: 2026-08-30
re-entry: implement
intake: #421
assumptions:
  - "The closure assertion lands on BOTH orientation tables even though only the maintenance one has a hole. The product table's completeness today is a fact nobody had checked; leaving it unasserted would mean the next reader has to recompute the same thing to tell the two tables apart."
  - "One new fixture, not one per uncovered path. `decompose` is reachable by exactly one shape here -- a run that re-entered at architect with architecture.md written and breakdown.md not -- so a single tree closes the row."
  - "Both directions are asserted in one test rather than two. They are the same claim about the same pair of sets, and splitting them would put half the claim in a test that can pass while the other half fails."
---

# Defect: a table row no fixture covers

Filed as intake issue #421 on 2026-08-30.

## Defect

`protocol.next_stage` can return `decompose` for a maintenance run, and
no fixture under `tests/fixtures/maintenance-orientation/` expects it.

```
$ # a maintenance run that re-entered at architect, architecture.md
$ # written, breakdown.md not
capture only          -> architect
+ architecture.md     -> decompose
+ breakdown.md        -> implement
```

The eight maintenance fixtures cover `capture`, `architect`,
`implement`, `verify`, `review`, `ship`, `operate` and `complete`.
`decompose` is the ninth reachable value, and had no tree.

## Why it stayed invisible

Nothing checked that the fixtures cover the table. `test_decision_table`
walks the fixtures that exist and asserts each returns what its
`expected` file says — a perfect score over whichever rows someone
happened to write trees for. The product/feature table is fully covered
and the maintenance table is not, and from outside the two suites looked
identical.

The concern outlives this row. `_maintenance_stage_complete`
special-cases `architect` and `decompose` on the run's `re-entry` depth,
so a change to that rule can make a row newly reachable — or make one
unreachable — with nothing that says so either way.

## Work items

1. A fixture for the `decompose` row. **Accept:** removing it fails the
   closure assertion.
2. Closure between rows and fixtures, both directions, on both tables.
   **Accept:** a row appended to `STAGE_ARTIFACTS` that no existing
   fixture reaches fails, and an `expected` file naming an impossible
   stage fails.
3. No false failure on the current tree. **Accept:** full battery green.
