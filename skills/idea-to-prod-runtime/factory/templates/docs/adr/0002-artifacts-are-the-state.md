# Artifacts are the state

- Status: accepted
- Date: 2026-08-05

Seeded by `factory-init`.

A pipeline needs to know where work stands. The tempting implementations — a
state file, a database, a field on a tracker issue — all fail the same way:
they can disagree with the repo, and when they do, the repo is right but the
machine believes the state store.

## Decision

Run state is derived entirely from which artifact files exist in the repo.
There is no manifest, no state file, and no status field anywhere that the
pipeline trusts. A run's position is a question answered by `ls`, so it
survives a closed session, a lost machine, and an unreachable network.

Progress inside a run is the same idea one level down: `breakdown.md`
checkboxes are the progress record, and checking one off is what makes the
work item done.

## Consequences

- Resuming work after any interruption needs no reconstruction step.
- Anything that would introduce a second source of truth — a status field the
  pipeline reads, a cached position, a sync daemon — is a decision that must
  supersede this ADR, not an implementation detail.
- Artifacts must be committed. An uncommitted `prd.md` is, to every other
  clone and to CI, a run that does not exist.
