# GitHub issues are the single work-order tracker mirror

- Status: superseded in part by ADR-0083 (the beads carve-out)
- Date: 2026-07-12

The work-order rows in `breakdown.md` (ADR-0004: the artifact is the
state) were being mirrored into **two** trackers at once — GitHub issues
(the ADR-0032 dispatch plane) and beads `wo-####`, adopted at mirror time
by the `beads adoption timing` note in `breakdown.md`. Nothing reconciles
them. Closing a work order at an item boundary (ADR-0026 close leg) closes
one copy and silently leaves the other open. Two independently drifting
copies of the same state is exactly the failure ADR-0004 exists to
prevent, and no ADR sanctions the second copy: ADR-0032 names GitHub as
the dispatch plane and mentions beads only as an optional holder of the
dependency graph.

## Decision

**GitHub issues are the one work-order mirror; beads is not a work-order
mirror.** `breakdown.md` remains the state — the tracker is a mirror,
never the state, and orientation never reads tracker state (ADR-0004,
ADR-0026). Of the two mirrors, GitHub is the load-bearing one:

- the assembler dispatches on lifecycle labels (ADR-0032);
- `validator.py` flips `wo:*` labels on merge;
- `sweeps.py` files triaged intake issues there;
- the cost report and gate-queue digest post there.

No factory script reads beads. This **amends ADR-0032**: the dependency
graph is carried on the GitHub issues themselves (blocking edges recorded
at mirror time), not in beads. The `beads adoption timing` note in
`breakdown.md` is superseded by this ADR.

Harness neutrality (ADR-0026) is preserved: no tracker CLI is named in
skill *process* text. GitHub specifics stay in packaging-facing text and
the factory scripts, which are already GitHub-shaped by ADR-0032.

This decision governs the **work-order mirror** only. It does not forbid a
human operator or an agent from using beads (or any tracker) for their own
session task-tracking; it forbids beads from being a second mirror of the
`WO-####` breakdown rows that the pipeline treats as canonical.

## Consequences

- One-way mirror, one direction of drift to check. The reconcile sweep
  (ADR-0032) reports GitHub-vs-breakdown drift; there is no third copy to
  reconcile.
- Work-order dependencies are expressed as GitHub issue relationships and
  as the blocking-edge tokens on the breakdown rows themselves, which the
  offline detectors already resolve.
- If beads (or another graph tracker) later earns a load-bearing role in
  the factory — a script that actually reads it — a future ADR revisits
  this with that need in hand.
