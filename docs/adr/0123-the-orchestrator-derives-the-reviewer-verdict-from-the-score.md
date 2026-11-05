# The orchestrator derives the reviewer verdict from the score

- Status: provisional
- Date: 2026-11-04

Recorded by the `reviewer-blind-cutoff` feature run
(`docs/features/reviewer-blind-cutoff/architecture.md`), unattended, so
it is provisional. Builds on [ADR-0087](0087-a-queue-profile-may-opt-in-to-implement-queue-auto-merge.md)
and [ADR-0096](0096-this-repo-opts-in-to-implement-queue-auto-merge-with-a-docs-fast-path.md),
which let the reviewer's pass merge pull requests unattended. It
changes where the pass or flag decision is made, not the threshold.

## Context

The universal reviewer at implement-queue's gate is told the pass line
("7 or more passes, 6 or less flags") and returns its own `verdict`
beside its `score`. The score is never posted. A judge that can see the
line can score toward it, and with no score on the record nobody can
check whether it does. No such incident is on record; this is
prevention plus making the question answerable.

## Decision

1. **The reviewer returns a score, never a verdict.** The reviewer
   contract names no pass threshold; a `verdict` field a reviewer still
   returns is ignored.
2. **One root-only module owns the threshold and the comment line.**
   `reviewer_verdict.py` holds the one constant (7) and one function
   that turns a score into `pass`, `flag` or `error`, and renders the
   verdict comment's first line, which carries the score. The queue
   profile's `verdict` hook runs it; the orchestrator posts that line
   unedited.
3. **No hook, no verdict.** With no `verdict` hook the orchestrator
   cannot derive one and records `error`: under `merge: auto` no merge,
   and a hold for a human, the existing rule for an error.

## Rejected alternatives

- **The cutoff stated in `SKILL.md` for the orchestrator to read.**
  Skill text cannot be called with scores 0 to 10, and a second copy in
  a checker is two owners.
- **A profile key such as `pass_score`.** It makes the threshold
  configurable, a change the brief puts out of scope.

## Consequences

- A repo that vends the skill with `merge: auto` but has no `verdict`
  hook stops merging on reviewer verdicts until it adds one. This
  repo's profile adds it in the same change.
- Every verdict comment from now on carries `score N/10`, so a later
  check can read scores off PRs. That check is not built here.
- The comment line is a reader-visible contract: a change to its shape
  breaks any later parser, so it moves by a new ADR.

## If rejected

The reviewer contract states the cutoff again and returns a `verdict`,
and `reviewer_verdict.py` is deleted. Comments already posted keep
their score line.
