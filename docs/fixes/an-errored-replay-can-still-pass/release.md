---
stage: ship
run: maintenance:an-errored-replay-can-still-pass
date: 2026-08-27
assumptions: []
---

# Release: an errored replay can still pass

**Prepared, not executed.** The brief carries no release authorization,
so ship stops here per the autorun default. Nothing was merged, tagged,
published or deployed.

## Pre-flight

- **Verification is green.** `verification.md` records nine checks, all
  PASS, and names what was not verified. No unresolved failures.
- **No unfixed critical review findings.** `review.md` records none; one
  minor is deferred with its owner named.
- **No secrets in the diff.** The change is one scorer function, one
  report line, and one test class. No credentials, tokens or URLs.
- **No configuration required.** `charter_replay.py` is stdlib-only and
  reads no new environment variable.
- **No migration, no data change.** `evals/results/` is untouched; the
  fix changes what future snapshots can say, and the directory stays
  append-only.
- **No payload mirror.** `charter_replay.py` is not in
  `factory_init.MIRRORS` (verified: the membership test returns False),
  so no `factory/manifest.json` regeneration is needed and none was
  done.
- **No money spent.** No replay was run. Every check is offline.

## Release steps, if a human authorizes them

1. Open a pull request from `agent/an-errored-replay-can-still-pass` to
   `main`.
2. A **non-authoring** reviewer re-executes the battery on the branch and
   records it on the PR — ADR-0036 clause 2. This run cannot satisfy
   that clause for itself, which is why no PR was opened.
3. Squash-merge once CI is green and the review is recorded.

## Rollback plan

The change is one commit touching two files, neither mirrored, with no
state left behind:

```
git revert <commit>          # after merge
git push origin main
```

Before merge, the branch can simply be deleted:

```
git push origin --delete agent/an-errored-replay-can-still-pass
```

Reverting restores the previous scoring behaviour exactly — an errored
replay would again be able to pass — and nothing else in the repo
depends on the new failure string.

## Post-release check

Not applicable: nothing was released. When it is, the check is that
`python3 -m unittest discover tests` reports 1351 on `main` and that
`tests.test_charter_replay.TestAnIncompleteReplayCannotPass` is present
and green.
