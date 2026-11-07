# Work orders dispatch from breakdown rows, never from issue bodies

- Status: accepted
- Date: 2026-08-05

Seeded by `factory-init`.

Dispatching an agent means handing it a prompt. If that prompt comes from an
issue body, then anyone who can file or edit an issue can write instructions
for an agent holding write credentials. Separately, a queue that can hold work
the repo has never heard of drifts ahead of the repo (contradicting ADR-0002).

## Decision

The prompt substrate is the repo-controlled `breakdown.md` row, never the raw
issue body — a prompt-injection boundary, not a convenience. A work order
`WO-####` exists only once its breakdown row exists; the mirrored issue comes
after, never before.

The order's queue position is a lifecycle label on the mirrored issue, exactly
one at a time, and the writers are machinery rather than memory: the assembler
claims (`wo:in-progress`) and reports its own failures (`wo:failed`); the
validator records the merge queue (`wo:needs-review`) and its exit
(`wo:merged`). The three gate labels are applied by the humans who pass the
gates, and `wo:blocked` is applied by a human — it means an unmet dependency,
and that graph is a planning judgment, not an observation of a run.

Only the repo owner may apply `wo:ready-for-agent`, enforced by an actor check
in the dispatch workflow. A label applied by anyone or anything else is inert.

## Consequences

- An issue carrying a lifecycle label with no breakdown row behind it is a
  finding, not a work item.
- Editing an issue body cannot change what an agent is told to do.
- With no API key configured, dispatch skips gracefully: nothing is
  dispatched, nothing is labelled, and nothing is faked.
