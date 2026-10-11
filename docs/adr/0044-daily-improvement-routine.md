# A daily routine drives the factory's improvement loop

- Status: superseded in part by ADR-0083 (the queue is read from GitHub issues, not the beads export)
- Date: 2026-07-30

## Context

ADR-0033 named the reflect loop — the correction stream turned into
charter rules — and nothing was ever built to run it. The factory
reports on a cadence (daily gate digest, weekly sweeps and cost report)
but improves only when a human opens an interactive session: the ready
queue waits, corrections go unmined, LEDGER maturity sits still. Any
daily improver must honor two standing rules: real model runs never run
in CI (CLAUDE.md), and an agent-authored PR merges only under a human
or an independent non-authoring reviewer (ADR-0033, ADR-0036).

## Decision

A scheduled cloud routine, `factory-daily-improvement`, runs daily
under the owner's account and operates the toolsmith charter on a
cadence. Being a harness schedule rather than a workflow keeps model
runs out of CI entirely.

Its complete protocol is a versioned playbook in the knowledge plane —
`docs/factory/improvement-routine.md` — so the routine is tuned by PR,
never by editing the schedule; the schedule prompt is a thin pointer
plus a few duplicated hard limits. Bounds: at most one S-sized PR
(ADR-0034's class) and one issue per run; never merges; never runs paid
evals; never edits the playbook — an agent cannot widen its own
authority, ADR-0036's reasoning applied to the routine's constitution.
State and reporting live in one pinned journal issue found by body
marker, the gate digest's idiom; reflect candidates graduate to PRs
only at two or more distinct correction events.

The beads JSONL export (`.beads/issues.jsonl`) is enabled and committed
so the cloud environment — which runs neither `bd` nor dolt — can read
the queue. It stays a passive export the routine never edits.

Routine spend is reported in the journal, not `docs/factory/costs.jsonl`:
ledger rows are work-order-keyed and detector-validated (ADR-0034,
ADR-0041, ADR-0043), and an unkeyed routine row would be drift.

## Consequences

- The reflect loop is live: corrections quoted with permalinks, rules
  built at two or more recurrences, gate/scope/graduation implications
  always escalated (ADR-0033 keeps those human-only).
- Routine spend sits outside the cost ledger; folding it in needs an
  ADR-0041-style amendment defining a keyed row shape.
- "The routine never merges" is a norm held by prompt and playbook, not
  branch protection (unavailable on the repo's current plan); routine
  PRs stay auditable via the `routine/` branch prefix and body marker.
- The playbook self-edit ban is normative in v1; a detector could pin
  it later if it is ever violated.
