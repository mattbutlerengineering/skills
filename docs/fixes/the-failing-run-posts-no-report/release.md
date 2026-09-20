---
stage: ship
run: maintenance:the-failing-run-posts-no-report
date: 2026-08-27
assumptions: []
---

# Release: the failing run posts no report

**Prepared, not executed.** The brief carries no release authorization,
so ship stops here per the autorun default. Nothing was merged, tagged,
published or deployed.

## Pre-flight

- **Verification is green.** `verification.md` records eight checks, all
  PASS, and names four things it did not verify — including that GitHub's
  `if:` evaluation itself cannot be exercised offline.
- **No unfixed critical review findings.** `review.md` records none; two
  majors are accepted with their reasoning, three minors deferred or
  recorded with no action.
- **No secrets in the diff.** Four lines of workflow `if:`, one checksum,
  one test helper, one test class. `FACTORY_PAUSE_TOKEN` and
  `GITHUB_TOKEN` are referenced only as `secrets.*` expressions, exactly
  as before.
- **Configuration unchanged.** No new secret, variable or permission. The
  posting step still uses the default `GITHUB_TOKEN` and the job's
  existing `issues: write`.
- **No migration, no data change.**
- **Payload mirror regenerated.** `factory_init.py update-manifest` moved
  exactly one checksum, and the two workflow copies are byte-identical —
  detector E is inside the green `gates: 0`.
- **No money spent.** Every check is offline.

## Release steps, if a human authorizes them

1. Open a pull request from `agent/the-failing-run-posts-no-report` to
   `main`.
2. A **non-authoring** reviewer re-executes the battery on the branch and
   records it on the PR — ADR-0036 clause 2. This run cannot satisfy that
   clause for itself, which is why no PR was opened.
3. Expect a conflict in `factory/manifest.json` against whichever payload
   PR lands first. Resolve it by re-running `python3 factory_init.py
   update-manifest` on the merged tree — never by hand-editing a
   checksum.
4. Squash-merge once CI is green and the review is recorded.

## Rollback plan

One commit; the only production surface is a workflow gate.

```
git revert <commit>          # after merge
python3 factory_init.py update-manifest
git commit -am "chore(factory): regenerate manifest after revert"
git push origin main
```

The `update-manifest` step is required here and was not in the previous
run's rollback: this change *does* move payload bytes, so a revert that
restores the workflow without restoring the checksum leaves detector E
red. Reverting returns the posting step to its implicit `success()` gate
— i.e. reinstates the defect — so it is a step to take only if the gate
itself causes trouble.

Before merge, the branch can simply be deleted:

```
git push origin --delete agent/the-failing-run-posts-no-report
```

## Post-release check

Not applicable: nothing was released. When it is, the check is that
`python3 -m unittest discover tests` reports 1348 on `main`, that
`python3 gates.py` reports 0 (detector E confirming the manifest matches
the payload), and that the next real `cost-report` run still posts its
weekly issue on the ordinary success path. The failing path stays
unproven until a run actually fails — which is the honest state of a
workflow gate that cannot be exercised offline.
