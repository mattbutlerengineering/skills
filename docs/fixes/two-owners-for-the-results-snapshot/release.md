---
stage: ship
run: maintenance:two-owners-for-the-results-snapshot
date: 2026-08-27
assumptions: ["the autorun brief carries no release authorization, so
  ship prepares and stops"]
---

# Release: two owners for the results snapshot

**Prepared, not executed.** No release authorization exists for this
run, so no externally visible action was taken: no pull request was
opened, nothing was merged, tagged, or published.

## Pre-flight

- Verification green, no unresolved failures — `verification.md`, five
  criteria, all PASS.
- No unfixed critical review findings — `review.md` records one deferred
  minor and two observations.
- No secrets in the diff: the change adds no configuration, no
  environment reads, and no external calls.
- No migration and no data change. `evals/results/` is untouched by this
  run; the append-only tree gains nothing and loses nothing.
- No mirrored file edited, so `factory/manifest.json` is unchanged and
  detector E has nothing to diff.

## Rollback

Single commit on a branch with no dependants:

```
git revert <sha>
```

Or, before the branch merges, delete it:

```
git push origin --delete agent/two-owners-for-the-results-snapshot
```

## Blocking condition

ADR-0036 clause 2: a non-authoring reviewer must re-execute the
verification and record it on the pull request. This run authored its
own review, so that clause is unsatisfied by construction.

## Remaining steps for a human

1. Open a pull request from
   `agent/two-owners-for-the-results-snapshot`.
2. Have a non-authoring reviewer re-run: `python3 -m unittest discover
   tests`, `python3 lint.py`, `python3 gates.py && python3 gates.py
   --selftest`, and record the output on the PR.
3. Merge.

This branch is deliberately not in the 17-PR queue: it was held back
because that queue has not drained since 2026-08-23 and every added PR
raises the merge cost. Open it whenever that is no longer true.
