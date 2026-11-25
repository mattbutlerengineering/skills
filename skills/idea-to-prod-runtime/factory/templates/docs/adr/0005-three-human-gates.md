# Three human gates

- Status: accepted
- Date: 2026-08-05

Seeded by `factory-init`.

Unattended agents can produce a great deal of work quickly. The question is
not whether to review it but *where* review is cheap: catching a wrong
direction after a merged PR costs far more than catching it before the work
started.

## Decision

Three points require a human, and they are placed where reversal is cheapest:

1. **PRD approval** — is this the right problem, scoped this way?
2. **Blueprint approval** — are the ADRs and the design right? (This
   directory is that blueprint.)
3. **Merge** — is this change correct? Enforced by required code-owner
   review, so the merged PR *is* the approval record; no separate sign-off
   artifact exists to fall out of date.

No agent merges its own work: verification comes from an identity that is not
the authoring one.

## Consequences

- `.github/CODEOWNERS` is load-bearing. If its handle is not a collaborator on
  this repo, GitHub ignores the entry and gate 3 silently goes inert —
  substitute the stamped placeholder before trusting the gate.
- Throughput is bounded by how fast a human clears the three queues, which is
  the intended trade.
- Auto-merge for a class of change is a decision that supersedes this one, and
  should be argued from data about that class.
