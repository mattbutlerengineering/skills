# Factory dispatch plane

- Status: accepted
- Date: 2026-07-11

The software factory (PRD-0001) needs unattended agents to pick up work.
Artifacts-are-the-state (ADR-0004) says run state is derived from files,
and the tracker bridge (ADR-0026) is a one-way, opt-in mirror the
orientation logic never reads. A dispatch mechanism must not quietly
become a second source of truth that drifts from the artifacts — the
exact failure ADR-0004 exists to prevent.

## Decision

Two planes, with an explicit direction of authority:

- **Knowledge plane** (source of truth): the run artifacts — `prd.md`,
  `architecture.md`, `breakdown.md`, ADRs, `CONTEXT.md`, and the cost
  ledger `docs/factory/costs.jsonl`. Offline CI detectors gate this
  plane; it is the only plane orientation reads. Unchanged from ADR-0004.
- **Dispatch plane** (work queue): GitHub issues carrying work orders,
  mirrored **one-way from breakdown rows** at decompose time — the
  ADR-0026 export leg, extended with lifecycle labels. beads (when
  adopted) carries the dependency graph. Reconciliation between planes is
  an opt-in networked sweep, never a merge gate, and disagreement is
  always resolved in the knowledge plane's favor.

**Typed cross-link IDs** make the link between planes checkable without a
graph database. A PRD gets `id: PRD-####` in its frontmatter (numbering
is global across runs, not per-run). ADRs already carry their number in
the filename. A work order is `WO-####`: a breakdown row token and its
mirrored issue. The offline detectors enforce: every breakdown work-order
row cites a resolving `PRD-#### §section`; every factory PR body cites
its `WO-####`; every typed token in `docs/**` and `CONTEXT.md` resolves;
duplicate IDs fail.

**Work-order lifecycle** is a label state machine on the mirrored issue —
exactly one lifecycle label at a time:

`wo:draft → wo:prd-approved → wo:blueprint-approved → wo:ready-for-agent
→ wo:in-progress → wo:needs-review → wo:merged | wo:failed | wo:blocked`

plus orthogonal families `size:S/M/L`, `risk:low/med/high`,
`type:feature/defect/chore/sweep/support`,
`source:validator/sentry/human/sweep`, and flags (`budget-exhausted`,
`needs-human`, `blueprint-drift`). Only the repo owner may apply
`wo:ready-for-agent`, enforced by an actor check in the dispatch
workflow, not by convention — a label applied by anyone or anything else
is inert. The dispatched agent's prompt substrate is the repo-controlled
breakdown row, never the raw issue body (prompt-injection boundary).

## Consequences

- Issues can be created ahead of a breakdown only as intake
  (ADR-0029/0030); a *work order* issue without a breakdown row is a
  detector finding, so the dispatch plane can never run ahead of the
  knowledge plane.
- The mirror stays one-way: editing an issue changes nothing the pipeline
  trusts; the networked reconcile sweep reports drift instead of merging
  it.
- No graph database. If link-checking measurably stops scaling, a future
  ADR revisits this with that evidence in hand.

## Normative statements

- **adr0032-one-way-mirror** (factory): A work-order issue MUST be created only after its breakdown row exists.
