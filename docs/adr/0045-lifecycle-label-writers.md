# Every lifecycle label has a named writer, and wo:blocked's is a human

- Status: accepted
- Date: 2026-08-05

ADR-0032 defined the work-order lifecycle as a label state machine —
`wo:draft → … → wo:in-progress → wo:needs-review → wo:merged | wo:failed
| wo:blocked` — but named no writer for the two terminal branches off the
happy path. In practice nothing wrote either: an agent run that died left
its order on `wo:in-progress` forever, where `gate_digest.py` and the
daily improvement routine (ADR-0044) both read it as work still in
flight. A queue state nothing can leave is worse than no queue state, and
it fails silently — the order simply never appears in any report again.

## Decision

**`wo:failed` is machine-written.** The assembler flips the order it
claimed on any dispatch failure (`.github/workflows/assembler.yml`, via
`make wo-failed` → `validator.run_outcome`). The step is gated on the
claim's own `transitioned` verdict, not on `failure()` alone: only an
order *this* run took out of ready may be flipped, so a run that died
before claiming leaves the order exactly as it found it. The leg writes
no verdict of its own — nothing runs after a failed job to read one.

**`wo:blocked` is human- or Planner-applied, by design.** It means an
unmet dependency, and that graph lives in the issue tracker, not in CI.
Mechanizing it would put the dispatch plane in the business of deciding
what blocks what, which is a planning judgment, not an observation of a
run. Its absence from the workflows is now a recorded decision rather
than a hole, and the taxonomy's other writers are stated where the
machine is defined (`validator.py`'s module docstring).

**Cross-plane disagreement is reported, never gated.** The reconcile
check ADR-0032 promised ships as `sweeps.py reconcile`: a scheduled sweep
comparing breakdown rows to live `wo:` labels, filing one intake issue.
It is not a merge gate, because it is a *network* read and the planes
disagree for ordinary reasons — an issue hand-edited, a row merged while
the tracker was unreachable — none of which should redden a build. It
reports drift by breakdown path and issue number, never by WO id, so the
sweeps invariant that no sweep may mint a work-order id needs no
exception carved out for it. Resolution stays the knowledge plane's, as
ADR-0032 requires.

## Consequences

- A dispatched order now always reaches a terminal state on its own, so
  the gate digest's merge-queue count and the improvement routine's
  `wo:failed` query are both truthful without human tending.
- `wo:blocked` will only ever be as accurate as the human applying it.
  That is the accepted cost of not inventing a dependency oracle in CI.
- The reconcile sweep can report drift it cannot fix, indefinitely. That
  is the point: ADR-0032 forbids the mirror healing itself.
