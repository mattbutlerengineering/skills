---
stage: ship
run: maintenance:gate-row-the-reader-rejects-becomes-spend
date: 2026-08-27
assumptions: ["the autorun brief carries no release authorization, so
  ship prepares and stops"]
---

# Release: a gate row the reader rejects becomes spend

**Prepared, not executed.** No release authorization exists for this
run. No pull request was opened; nothing was merged, tagged or
published.

## Pre-flight

- Verification green, five criteria, no unresolved failures.
- No unfixed critical findings. `review.md` records one major,
  deliberately deferred, with its reason and its collision with PR #347.
- No secrets in the diff; no configuration added; no network call.
- No data migration. `docs/factory/costs.jsonl` is untouched: all 22 of
  its gate rows already satisfy the reader, so nothing needs rewriting
  and nothing was appended.
- `cost_ledger.py` is mirrored, so `python3 factory_init.py
  update-manifest` was run and `factory/manifest.json` is committed with
  the change, per the checksum-pinning convention.

## Rollback

Single commit, no dependants:

```
git revert <sha> && python3 factory_init.py update-manifest
```

Or, before the branch merges:

```
git push origin --delete agent/gate-row-the-reader-rejects-becomes-spend
```

## Blocking condition

ADR-0036 clause 2: a non-authoring reviewer must re-execute the
verification and record it on the pull request.

## Remaining steps for a human

1. Open a pull request from
   `agent/gate-row-the-reader-rejects-becomes-spend`.
2. Have a non-authoring reviewer re-run `python3 -m unittest discover
   tests`, `python3 lint.py`, `python3 gates.py && python3 gates.py
   --selftest`, and record the output on the PR.
3. Merge. `factory/manifest.json` conflicts with other branches are the
   regenerate class: resolve by re-running update-manifest, never by
   hand-editing.

This branch is deliberately not in the 17-PR queue, for the same reason
as the previous four: that queue has not drained since 2026-08-23.
