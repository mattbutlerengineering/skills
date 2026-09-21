---
stage: ship
run: maintenance:an-infinite-cap-is-no-cap
date: 2026-08-27
assumptions: ["the autorun brief carries no release authorization, so
  ship prepares and stops"]
---

# Release: an infinite cap is no cap

**Prepared, not executed.** No release authorization exists for this
run. No pull request was opened; nothing merged, tagged or published.

## Pre-flight

- Verification green, five criteria, all PASS.
- No unfixed critical findings; `review.md` carries one deferred minor.
- No secrets in the diff; no configuration added; no network call.
- No migration. The shipped `.github/factory.json` carries no infinite
  amount — had it done so, the battery would have failed.
- `factory_config.py` is mirrored, so `update-manifest` ran and
  `factory/manifest.json` is committed with the change.

## Rollback

```
git revert <sha> && python3 factory_init.py update-manifest
```

Or before merge:

```
git push origin --delete agent/an-infinite-cap-is-no-cap
```

## Note for whoever merges

This branch and `agent/a-config-the-gate-cannot-read` both edit
`factory_config.py`, in different functions — `_positive_number` here,
`load` there. Git merges them without conflict; only
`factory/manifest.json` needs the usual regenerate-don't-hand-edit
treatment.

## Blocking condition

ADR-0036 clause 2: a non-authoring reviewer must re-execute the
verification and record it on the pull request.

## Remaining steps for a human

1. Open a pull request from `agent/an-infinite-cap-is-no-cap`.
2. Non-authoring reviewer re-runs the battery and records it on the PR.
3. Merge; resolve `factory/manifest.json` by re-running update-manifest.

Held out of the 17-PR queue for the same reason as the previous six.
