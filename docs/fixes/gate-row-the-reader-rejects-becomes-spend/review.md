---
stage: review
run: maintenance:gate-row-the-reader-rejects-becomes-spend
date: 2026-08-27
assumptions: []
---

# Review: a gate row the reader rejects becomes spend

Scope: `cost_ledger.py` (+11/-3), its payload mirror,
`factory/manifest.json` (regenerated), `tests/test_cost_ledger.py`
(+49).

Written by the same agent that wrote the change, so ADR-0036 clause 2
is unsatisfied: a non-authoring reviewer must re-execute the
verification and record it on the pull request.

## Correctness

**Major, accepted deliberately — the refusal is a traceback, not a
problem string.** `gate_digest._capture_latency` calls `gate_entry` in
a loop, and `run_daily` catches only `CLI_FAILURES`. A future gate
whose ledger name the reader refuses would therefore fail the daily
digest with an unhandled `ValueError` rather than a diagnosed problem.

That is the intended direction — a loud failure beats a spend figure
that is quietly wrong against ADR-0034's cap — but it is a real
behaviour change and it is recorded rather than hidden. It is not fixed
here for two reasons: the condition is unreachable with the three
shipped gates, and `gate_digest.py`'s error handling is exactly what
PR #347 is changing. Widening `run_daily`'s catch from this branch
would collide with that PR and would also be a second opinion about a
question that PR is already answering.

**Checked, not a finding — `int(waited_seconds)` still raises on a
non-numeric wait.** `TypeError` for `None`, unchanged from before this
run in both kind and placement. This run neither widened nor narrowed
it.

**Checked, not a finding — no existing row changes meaning.** All 22
gate rows in the shipped ledger already satisfy the reader, so the
guard partitions no existing data differently.

## Design

The guard validates the composed string against `GATE_OUTCOME` rather
than restating the constraint in the writer. That matters: the defect
was a grammar with two statements, and a hand-written second constraint
would have reproduced it one line lower. The regex stays the single
authority; the writer now defers to it.

`cost_ledger.py` is mirrored into the payload, so stamped product repos
receive the same guard. That is the correct blast radius — the defect
was in the seam, not in this repo's use of it.

## Security

No new input surface: `gate` and `waited_seconds` reach this function
from repo-controlled constants and computed deltas, never from an issue
body or GitHub event. No secrets, no subprocess, no network. The change
only narrows what may be written.

## Verdict

No critical findings. One major recorded and deliberately deferred with
its reason and its collision risk named. The blocking condition on
shipping is ADR-0036 clause 2.
