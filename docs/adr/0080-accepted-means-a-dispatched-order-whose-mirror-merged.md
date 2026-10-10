# Accepted means a dispatched order whose mirror merged

- Status: accepted
- Date: 2026-10-10

## Context

ADR-0069 defined the north-star metric as accepted work orders per
gate-wait hour and counted as accepted the dispatched ledger rows with
`outcome == "merged"`. The ledger never holds that value: the assembler
writes its row when the agent job ends, before any merge
(`.github/workflows/assembler.yml` writes `completed` or `agent-failed`),
and nothing writes a later row. So the filter selects nothing by
construction and the metric reads 0 however much dispatched work merges.

By 2026-10-10 the factory had dispatched and merged two real work orders
(WO-0074, WO-0076; mirror issues #536 and #574, both `wo:merged`), which
is what ADR-0069 said the baseline waited for. Computed honestly, the
literal formula reports 0 and the label-joined reading reports 2.

Writing a `merged` row at merge time was considered and rejected: it gives
CI a write path into the ledger, and ADR-0077 keeps write credentials away
from the dispatched path on purpose. The merge already has an
authoritative, durable record — the mirror issue's `wo:merged` label,
applied by the merged-label leg (ADR-0045).

## Decision

A work order is **accepted** when the assembler dispatched it (at least
one `completed` ledger row for its WO id) **and** its mirror issue carries
`wo:merged`. The metric is the count of accepted work orders — distinct WO
ids, not runs — divided by gate-wait hours, which ADR-0069 defines and
this ADR leaves unchanged:

```
dispatched_ids = {e["wo"] for e in cost_ledger.dispatched(entries)
                  if e["outcome"] == "completed"}
accepted = [wo for wo in dispatched_ids if "wo:merged" in mirror_labels(wo)]
metric = len(accepted) / gate_hours
```

Raw acceptance is reported alongside as `len(accepted) / len(dispatched_ids)`.
Everything else in ADR-0069 stands: escapes stay outside the number, the
dollar-weighted alternative stays rejected.

The 2026-10-10 baseline, under this definition, is 2 accepted orders over
2,775.9 gate-wait hours: **0.00072 per gate-wait hour**, with raw
acceptance 2/2. Inputs and caveats are in
`docs/research/autonomy-baseline.md`.

## Consequences

- ADR-0069 is superseded in part: its `outcome == "merged"` filter is
  retired; its formula shape and denominator stay live.
- Computing the metric now needs the tracker (mirror issue labels), not
  the ledger alone. Any future report or dashboard field that wires the
  computation reads labels the way the gate digest already does.
- Counting distinct WO ids means a work order that took six runs counts
  once; its runs still show up in cost.
