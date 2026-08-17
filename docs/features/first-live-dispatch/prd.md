---
stage: prd
run: feature:first-live-dispatch
date: 2026-08-17
id: PRD-0003
ux: not-applicable
ux-reason: operator's surface is the existing tracker, labels, and PRs — nothing new is built for humans to look at
---

# PRD: First live dispatch

## Problem statement

The factory's dispatch plane has never processed real work. Every
work order to date was executed in owner-driven sessions; the
assembler's only history is skipped and cancelled runs; the first two
gates have never passed anything; the budget breaker has no token to
act with. v1's verification carries three FAILs and two PARTIALs with
this single cause, and every dispatch-path behavior is proven only at
the unit seam. The operator's working hours still cap throughput —
the exact cap the factory was built to break.

## Solution

When this ships, the factory has done its job once, for real, under
supervision: both operating secrets exist; one small, real,
review-found work order (the gates.py detector-J roster fix) has
traversed the full label chain through dispatch to an owner-merged,
validator-checked PR; the ledger holds the run's true spend; and the
circuit breaker has paused dispatch once by itself and been cleared.
v1's criteria 1–4 graduate from FAIL/PARTIAL on the evidence this run
produces — no criterion is reworded to pass.

## Actors

- **Matt (owner-operator)** — mints secrets, approves at gates 1 and 2,
  supervises the dispatch, reviews and merges at gate 3.
- **The dispatched agent** — the SWE-chartered model run the assembler
  launches; executes the work order, delivers the traceable PR.
- **The factory's automation** — assembler, validator (via
  workflow_dispatch hand-off), reviewer job, cost-report/breaker;
  already shipped, exercised live for the first time here.

## User stories

1. As Matt, I want to hand a ready-labeled work order to the factory
   and get back a validated PR to review, so that execution stops
   requiring my keyboard time and my attention goes to the gates.
2. As Matt, I want the first paid dispatch to run with the breaker
   armed and mechanically stoppable, so that a runaway first contact
   costs a bounded amount, never an open-ended one.
3. As the dispatched agent, I want the order's substrate (row, Accept
   criterion, orientation pack) to be sufficient to do the work without
   asking anyone, so that the delivery is judged at the gates rather
   than coached mid-run.
4. As Matt, I want every claim this run graduates to be backed by the
   same evidence classes v1's verification demanded (run conclusions,
   label history, ledger rows), so that the factory's first success is
   as honest as its recorded failures.

## Success criteria

- [ ] Both secrets exist in Actions (`ANTHROPIC_API_KEY`,
      `FACTORY_PAUSE_TOKEN`) — names visible in `gh secret list`,
      values console-set and never in the repo.
- [ ] The payload order's mirror issue carries the full gate history:
      `wo:prd-approved` and `wo:blueprint-approved` applied by Matt,
      then `wo:ready-for-agent` — the first order ever to traverse
      gates 1 and 2 as labels.
- [ ] An assembler run concludes `success` (not skipped, not
      cancelled) and the dispatched agent's PR closes the mirror issue
      via the `Closes #N` grammar.
- [ ] The validator hand-off fires live: a `workflow_dispatch`
      validator run for that PR executes check + review + label jobs,
      and the order flips to `wo:needs-review` untouched by hands.
- [ ] Matt merges the PR manually (v1 merge policy unchanged) and the
      order reaches `wo:merged` with detector G green.
- [ ] The ledger carries the dispatched run's spend row with real
      nonzero token counts, committed by the workflow, not by hand.
- [ ] The breaker fires once for real: the cost-report workflow sets
      `FACTORY_PAUSED=true` itself via `FACTORY_PAUSE_TOKEN`, and a
      subsequent ready-label is demonstrably inert until Matt clears
      the flag. Staging mechanism is Architect's call — but the pause
      must be set by automation, never a hand.
- [ ] Total run spend (dispatch + retries + breaker test) ≤ $10,
      readable from the ledger.
- [ ] The J-roster fix itself lands correct: gates.py's docstring and
      DETECTORS table agree that J is claimed, pinned by the existing
      battery staying green.

## Out of scope

- Unattended merges — every merge stays human (v1 rule; graduation is
  a later run on this run's evidence).
- Gate-label wiring from owner sessions (separate backlog seed) — this
  run flips gate labels by hand at the gates, which is the point of
  supervision.
- The ADR-0055 deferrals (token-budget hook, payload charters) and the
  validator dispatch-arm hardening bundle (its own seed).
- Any second dispatch beyond what retries and the breaker test
  require; scaling throughput is v2's story.
- A pinned calendar window — completion is the bar, scheduling is
  Matt's (the WO-0035 window expired; this PRD doesn't stake a date to
  go stale).

## Open questions

- How to stage the breaker firing honestly within the $10 ceiling —
  lower the cap temporarily by PR? A dedicated test path? Constraint:
  no fabricated ledger rows, ever (eval-honesty) — Architect decides.
- Which routing band/model the J-fix's type label resolves to, and
  whether that's the right first-contact model — Architect, from
  factory.json's table.
- Whether the breaker test runs before or after the dispatch (armed
  breaker before first paid run is the safer order; the pause blocks
  dispatch while set) — Architect sequences it.
