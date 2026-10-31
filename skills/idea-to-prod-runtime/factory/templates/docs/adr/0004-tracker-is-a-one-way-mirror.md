# The issue tracker is a one-way mirror, never the state

- Status: accepted
- Date: 2026-08-05

Seeded by `factory-init`.

Issue trackers are where teams already live, so it is natural to let one drive
the pipeline. But a tracker the pipeline *reads* becomes a second source of
truth (contradicting ADR-0002) and a hard dependency: when it is unreachable,
or an issue is edited by hand, the repo and the tracker disagree and the
machine believes the wrong one.

## Decision

The tracker mirrors work items outward and is never read as state. Sync
happens only at stage boundaries — import when a run is seeded, export at
Decompose, close at each Implement item boundary — and orientation never reads
tracker state at all. A work item mirroring an issue records the reference on
its checkbox line as `(tracker: #123)`; the checkbox remains the state.

## Consequences

- Editing an issue changes nothing the pipeline trusts. Reconciliation reports
  drift for a human to resolve; it never merges the tracker's view back in.
- Work filed in the tracker while no session was open does not start anything
  by itself. Someone has to bring it in.
- On a repo with no tracker configured, nothing changes — the bridge is
  strictly opt-in.
