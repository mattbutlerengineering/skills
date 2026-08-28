---
stage: ship
run: maintenance:an-unresolvable-cap-plans-a-full-batch
date: 2026-08-27
assumptions: ["the autorun brief carries no release authorization, so
  ship prepares and stops"]
---

# Release: an unresolvable cap plans a full batch

**Prepared, not executed.** No release authorization exists for this
run. No pull request was opened; nothing merged, tagged or published.

## Pre-flight

- Verification green, five criteria, all PASS.
- No unfixed critical findings; `review.md` carries one deferred minor
  and one recorded pre-existing pattern.
- No secrets in the diff; no configuration added; no network call.
- No migration. The shipped `.github/factory.json` names a cap, so no
  live config takes the new path — had one not, the battery would have
  surfaced it.
- `work_queue.py` is mirrored, so `update-manifest` ran and
  `factory/manifest.json` is committed with the change.

## Rollback

```
git revert <sha> && python3 factory_init.py update-manifest
```

Or before merge:

```
git push origin --delete agent/an-unresolvable-cap-plans-a-full-batch
```

## Note for whoever merges

No open PR touches `work_queue.py` or `tests/test_work_queue.py`, so the
code hunks are uncontended. `factory/manifest.json` is the usual shared
file: resolve it by re-running `python3 factory_init.py update-manifest`
after the merge rather than by hand-picking hunks.

## Blocking condition

ADR-0036 clause 2: a non-authoring reviewer must re-execute the
verification and record it on the pull request.

## Remaining steps for a human

1. Open a pull request from `agent/an-unresolvable-cap-plans-a-full-batch`.
2. Non-authoring reviewer re-runs the battery and records it on the PR.
3. Merge; resolve `factory/manifest.json` by re-running update-manifest.

Held out of the 17-PR queue for the same reason as the previous eight.
