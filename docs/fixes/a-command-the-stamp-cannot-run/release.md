---
stage: ship
run: maintenance:a-command-the-stamp-cannot-run
date: 2026-08-27
assumptions: []
---

# Release: a command the stamp cannot run

**Prepared, not executed.** The brief carries no release authorization,
so ship stops here per the autorun default. Nothing was merged, tagged,
published or deployed.

## Pre-flight

- **Verification is green.** `verification.md` records eight checks, all
  PASS, and names what was not verified. No unresolved failures.
- **No unfixed critical review findings.** `review.md` records none; two
  majors are accepted with their reasoning and three minors are deferred
  or dismissed with reasons.
- **No secrets in the diff.** One deleted constant, one rewritten
  function, one corrected comment, one new test class.
- **No configuration required.** Stdlib only.
- **No migration, no data change.**
- **No payload mirror, and none needed.** `factory_init.py` is not in
  its own `MIRRORS` — it is the stamping tool, not part of what gets
  stamped. `update-manifest` was run anyway and changed nothing, which
  is the run's central piece of evidence.
- **No money spent.** Every check is offline.

## Release steps, if a human authorizes them

1. Open a pull request from `agent/a-command-the-stamp-cannot-run` to
   `main`.
2. A **non-authoring** reviewer re-executes the battery on the branch and
   records it on the PR — ADR-0036 clause 2. This run cannot satisfy
   that clause for itself, which is why no PR was opened.
3. If PR #320 lands first, rebase and re-check that its hunk in
   `tests/test_factory_init.py` (around line 270) still does not overlap
   the renamed test in `TestProductForm`.
4. Squash-merge once CI is green and the review is recorded.

## Rollback plan

One commit, two files, no generated artefact and no state left behind:

```
git revert <commit>          # after merge
git push origin main
```

No `update-manifest` step in the rollback, unlike the previous run's:
this change produced no payload bytes, so there is nothing for detector
E to be out of step with. Reverting restores `_PRODUCT_TOOLS` and the
seven-tool respelling; the payload Makefile is unaffected in both
directions.

Before merge, the branch can simply be deleted:

```
git push origin --delete agent/a-command-the-stamp-cannot-run
```

## Post-release check

Not applicable: nothing was released. When it is, the check is that
`python3 -m unittest discover tests` reports 1348 on `main`, that
`python3 factory_init.py update-manifest` still leaves
`factory/templates/Makefile` and `factory/manifest.json` unchanged, and
that `tests.test_factory_init.TestTheRespellingHasOneOwner` is present
and green.
