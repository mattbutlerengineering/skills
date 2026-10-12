# A queue profile may opt in to implement-queue auto-merge

- Status: accepted (Owner, 2026-10-12)
- Date: 2026-10-12

Amends ADR-0033, for merges performed by the `implement-queue` skill in
a consumer repo. The Owner chose this policy on 2026-10-12, in session:
opt-in, off by default. It resolves issue #716.

ADR-0036 lets an agent merge under an independent review, and ADR-0085
and ADR-0086 settle how a Conductor batch records that merge's consent.
Neither covers a consumer that drains its ready issues from a scheduled
routine: there is no Owner in the session and no Conductor batch. The
consumer this skill comes from (mattbutlerengineering/mattbutlerengineering)
has run exactly that unattended merge train for months under its
Owner's standing policy, and moving the skill here must not take it
away, nor hand it to every other consumer unasked.

## Decision

`implement-queue` reads a queue profile, `.claude/implement-queue.md`,
in the consumer repo. Its `merge` key is **`off` by default**: absent,
or anything but `auto`, the skill stops at reviewed, green PRs and the
human merge is ADR-0033's gate 3, unchanged.

With `merge: auto`, the profile is the Owner's standing consent, and
the skill may enqueue a PR for merge with no human answer only when
**all** of ADR-0036's conditions hold, read for a consumer repo:

1. **The required check is present and green.** The profile names it
   (`required_check`). A rollup with no failures but no such check is
   not green.
2. **An independent review passed.** The universal reviewer, and every
   specialist the profile matches to the diff, returned `pass`; no
   reviewer is the PR's author; no reviewer changed the checkout it
   read. A reviewer timeout or error is not a pass.
3. **No gate-path file.** The PR changes nothing the profile's
   `gate_paths` match (default `docs/adr/**`, `docs/design/**`,
   `**/prd.md`, `**/architecture.md`). Those still need a human merge.

And one condition of its own:

4. **No hold label.** Neither the PR nor its issue carries one of the
   profile's `hold_labels` (default `needs-review`).

A merge the session's runtime denies is never retried by another route.

## Consequences

- Every consumer that has not written `merge: auto` keeps ADR-0033 as
  is: the skill merges nothing.
- An agent can merge with no human answer in the loop. The profile is
  changed only by a PR to the consumer repo, so the commit that turned
  it on is the audit record. The same trust limit as ADR-0086 holds:
  this stops a confused agent, not a hostile one that edits the profile.
- ADR-0033's class graduation (≥ 20 merged PRs, ≥ 90% acceptance) is
  advice to the consumer, not a check the skill runs: the Owner's
  written profile is the decision ADR-0033 reserves to a human.
- This ADR is a gate-path change, so the PR that carries it needs a
  human code-owner merge.

## If rejected

Drop the `merge` key: the skill then always stops at reviewed, green
PRs, and a consumer that relied on `merge: auto` sees every PR reported
as awaiting a human merge, never a silent merge.
