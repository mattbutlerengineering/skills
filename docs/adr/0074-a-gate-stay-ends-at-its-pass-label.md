# A gate stay ends at its pass label

- Status: accepted
- Date: 2026-09-28

Amends ADR-0056's definition of a completed stay.

## Context

ADR-0056 gave `human_gates` one definition of a stay: the span from when
a gate's queue label is applied to when it is removed. A stay is
confirmed when the gate's pass label is applied inside its window. That
definition assumes ADR-0032's one-lifecycle-label rule holds at every
flip. It holds for the automated flips (claim, needs-review, merged),
which replace one lifecycle label with another. Nothing enforces it when
a human applies a gate label. `gh issue edit --add-label wo:prd-approved`
leaves `wo:draft` on.

The first live traversal (#536, 2026-09-24) did exactly that. The owner's
gate walk added `wo:prd-approved` and `wo:blueprint-approved` beside
their queue labels, and the assembler's claim stripped both 15-19s
later. The ledger recorded `gate_wait:prd:1399s` and
`gate_wait:blueprint:19s` against true waits of 1380s and 4s
(`docs/features/first-live-dispatch/verification.md`, Gate-latency
reconciliation). The error is small there but structural: a PRD pass
added days before the blueprint pass, with both queue labels stripped
together, folds the whole blueprint wait into the PRD row. ADR-0069's
metric divides by these rows.

## Decision

A confirmed stay ends at the earlier of two moments: its queue label's
removal, or the first pass label applied inside its window. An
unconfirmed stay still ends at the removal. Its window and its
confirmation test are unchanged, so the digest/miner partition
(ADR-0056) is untouched: every completed stay is still confirmed or not,
and only a confirmed stay's end can move earlier.

The fix lives in the walk, not at the source. A workflow that stripped
the queue label on every owner gate-label event would enforce ADR-0032
too, but it would add a job with issue-write scope and still leave
history recorded before it existed mis-measured.

## Consequences

- `human_gates.completed_stays` is the one change. `gate_passages`, and
  through it the gate-digest latency rows, inherit it, and
  `gate_rejections` is unaffected.
- Rows already in `docs/factory/costs.jsonl` stand as recorded; the
  ledger is append-only. #536's two rows are corrected in its run's
  verification, not rewritten.
- The dashboard's open-stay age (`waiting_since`) still counts until the
  queue label is removed. An issue that has been passed but still
  carries its queue label shows as waiting there until the next flip.
  That is left as-is: the dashboard reports what the labels say now,
  and the ledger records what the human spent.
