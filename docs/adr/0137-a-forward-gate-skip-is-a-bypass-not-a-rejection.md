# A forward gate skip is a bypass, not a rejection

- Status: accepted (by the Owner, 2026-11-24, option 1 on #2309)
- Date: 2026-11-24

Amends ADR-0056's stay partition.

## Context

ADR-0056 made the digest/miner split executable: `completed_stays`
returned `(start, end, confirmed)`, the digest kept the confirmed stays
and `rejection_mining` kept the rest, so every completed stay was a
passage or a rejection. ADR-0074 moved a confirmed stay's end and left
that split alone.

The 2026-11-20 scheduled-tools audit (#2309) ran the miner on live data.
It found 36 candidate work orders and 36 corrections, every one a "prd
gate rejection", and none of them was a rejection. Grouped by the label
added when the stay ended: `wo:needs-review` ×16, `wo:merged` ×12,
`wo:in-progress` ×3, nothing ×5, and zero `wo:failed` or `wo:blocked`.
#113, for example, had `wo:draft` removed and `wo:merged` added in the
same second. The order skipped forward past the gate. The human neither
approved the PRD gate nor rejected it. The miner's own docstring defined
a rejection as "a flip to wo:failed / wo:blocked". Its seam's complement
rule disagreed, and on live data the seam's rule won every time.

## Decision

**A completed stay has one of three outcomes**, the value
`completed_stays` now returns in place of the `confirmed` bool:

- `PASSED`: the gate's pass label was applied inside the stay's window.
  The window test and ADR-0074's end rule are unchanged.
- `REJECTED`: the stay was sent back. It left for `wo:failed` or
  `wo:blocked`, or for a gate label earlier than its own queue in
  `GATES` order (for example `wo:needs-review` back to
  `wo:prd-approved`).
- `BYPASSED`: anything else. The stay left forward without the pass
  label, either to a later gate label or to a lifecycle label outside
  the gates (`wo:in-progress`), or its queue label came off with no
  lifecycle label to follow.

The labels a stay "left for" are the `wo:` labels added from its start
through its end, so a `wo:blocked` added beside the queue label counts.
When there are none, it is the first `wo:` label added after the end
and before the gate's next re-entry, which covers a removal and a new
label applied as two edits.

`gate_passages` keeps `PASSED`, `gate_rejections` keeps `REJECTED`, and
the new `gate_bypasses` returns `BYPASSED` in the same `(gate, ended
at)` shape. The digest's passages and the miner's rejections are still
disjoint slices of one list, but they no longer cover it.

Options #2309 weighed and did not take:

- Treat a forward skip as a passage of the gates it skipped. That writes
  latency rows for waits no human spent, and ADR-0069's metric divides
  by them.
- Filter by end label inside `rejection_mining`. That leaves the seam
  wrong for any other reader, which is the divergence ADR-0056 exists
  to prevent.

## Consequences

- `rejection_mining` changes output: forward skips drop out of the
  toolsmith queue, so the 36 live false corrections disappear on its
  next weekly run. Its code is unchanged and only its docstring moves.
- `gate_digest` is unchanged. `gate_passages` returns what it returned
  before, so no latency row is added or lost. `dashboard`, `trace`,
  `work_queue` and detector J do not read the partition.
- Nobody renders bypasses yet. Reporting them is left to whichever
  caller first has a use for them, and `gate_bypasses` exists so that
  caller does not re-derive the class.
- A move from `wo:needs-review` to `wo:in-progress` counts as a bypass,
  because `wo:in-progress` is not a gate label. No machinery makes that
  flip today (`validator.run_claim` claims only from
  `wo:ready-for-agent`). If a send-back-to-work flow is added, it must
  extend `REJECTION_LABELS` or the order this ADR reads.
- `human_gates.py` and `rejection_mining.py` are identity mirrors, so
  the payload and the template manifest change in the same commit.
