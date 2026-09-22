# Autonomy per human-hour: accepted orders per gate-wait hour

- Status: accepted
- Date: 2026-09-21

## Context

- Issue #434 (`wo-25y.5`, Map: Factory evolution) asked for the map's
  north-star metric — "autonomy per human-hour at the three gates" —
  computed from existing substrates: gate-latency rows, cost rows,
  acceptance rate, escapes.
- Checked against the real `docs/factory/costs.jsonl` (2026-09-21): every
  non-gate row so far carries outcome `owner-session:unmetered` — this
  repo has never yet dispatched a real work order through the assembler
  pipeline that produced a `merged`/`failed` outcome. Gate-latency rows
  exist only for the `merge` gate; `prd` and `blueprint` have never
  recorded a wait. "Escapes" is named in ADR-0033/ADR-0034's prose
  (`≥ 90% acceptance rate, zero defect escapes attributed to the class`)
  but has no field, ledger row, or accessor anywhere — the
  review-ci-automation survey (`docs/research/review-ci-automation.md`,
  finding 4) already found this and deferred defining it until the first
  class actually graduates, rather than resolving it standalone.
- The two substrates that DO have real, working accessors today:
  `cost_ledger.dispatched(entries, month=None)` (non-gate spend rows,
  each carrying an open-vocabulary `outcome`) and `cost_ledger.gate_wait
  (entry)` (`(gate, waited_seconds)` for a gate-latency row, `None`
  otherwise) — both already used by the weekly report and the work
  queue's circuit breaker.

## Decision

The metric is **accepted work orders per gate-wait hour**:

```
accepted = [e for e in cost_ledger.dispatched(entries) if e["outcome"] == "merged"]
gate_hours = sum(seconds for _, seconds in
                 filter(None, (cost_ledger.gate_wait(e) for e in entries))) / 3600
metric = len(accepted) / gate_hours
```

A pure throughput-per-attention-hour ratio: how many work orders clear
all three gates per hour of human gate-wait time. Escapes and raw
acceptance rate (`len(accepted) / len(dispatched(entries))`) are
reported **alongside** this number, never folded into it — combining a
rate with an as-yet-undefined escape count would answer a question this
repo hasn't decided how to ask yet (see the deferred DORA distinction
above). The dollar-cost-weighted alternative (`$` dispatched per
gate-wait hour) was considered and rejected for the north-star slot: it
is more sensitive to work-order size (S/M/L budget class) than to
throughput, which is not what "autonomy" is meant to track here.

**Baseline: not yet computable.** Per the Context above, real
dispatched-work data does not exist yet — every current substrate row
is either `owner-session:unmetered` (not a dispatch) or a merge-gate
wait with no matching accepted order to divide by. This ADR settles the
formula; it does not, and cannot honestly, report a number. Compute the
actual baseline once the factory has dispatched and merged real work
orders through the assembler pipeline.

## Consequences

- `gate_hours` sums waits across whichever gates have recorded rows —
  today that is `merge` alone, so the metric would currently be
  denominated entirely on merge-gate time. It is expected to widen as
  `prd`/`blueprint` gate-latency rows start accumulating.
- No new code ships with this ADR: both accessors it depends on
  (`cost_ledger.dispatched`, `cost_ledger.gate_wait`) already exist.
  Wiring the actual computation into the weekly report or a dashboard
  field is separate, future work, not blocked by this decision.
- Closes issue #434's formula half. The baseline half stays open until
  real dispatch data exists to compute it from.
