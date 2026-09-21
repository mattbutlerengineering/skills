---
stage: ship
run: maintenance:a-manifest-that-is-not-an-object
date: 2026-08-27
assumptions: ["the autorun brief carries no release authorization, so
  ship prepares and stops"]
---

# Release: a manifest that is not an object

**Prepared, not executed.** No release authorization exists for this
run. No pull request was opened; nothing merged, tagged or published.

## Pre-flight

- Verification green, five criteria, all PASS.
- No unfixed critical findings. `review.md` carries one major accepted
  with its cost and one open finding with its owner named.
- No secrets in the diff; no configuration added; no network call.
- No migration. Both live manifests are objects, so no shipped file
  takes the new path — had one not been, CI would already be red.
- `lint.py` is not mirrored into the stamped payload, so nothing under
  `factory/templates/**` changed and `factory/manifest.json` is
  untouched.

## Rollback

```
git revert <sha>
```

No manifest regeneration on the way back, for the same reason none was
needed on the way out. Or before merge:

```
git push origin --delete agent/a-manifest-that-is-not-an-object
```

## Notes for whoever merges

**Two open PRs also edit `lint.py`, and neither overlaps.** #324 ("hold
the plugin description to the utility taxonomy") changes the import
block and inserts a new checker between `check_manifest` and
`check_pi_package`; #345 ("ask what is already in flight before a run
starts") works at lines 170-240. This branch adds a helper above
`check_manifest` and three lines inside each of the two readers. #324's
insertion point is adjacent to this one, so expect git to want a look
even though the changed lines do not overlap; both sides are additive
and the resolution is to keep both.

**A duplicate becomes real if one other branch lands.**
`agent/eval-validators-raise-on-non-object-files` is pushed with five
commits and no pull request. It adds `eval_schema.object_problems` with
the identical rule. If it is merged, collapse the two: keep
`eval_schema`'s (it owns what a validator may assume), and change
`lint.py`'s two call sites to `eval_schema.object_problems` — `lint.py`
already imports the module. That branch also fixes
`check_output_evals`'s raise, which this run left open.

## Blocking condition

ADR-0036 clause 2: a non-authoring reviewer must re-execute the
verification and record it on the pull request.

## Remaining steps for a human

1. Open a pull request from `agent/a-manifest-that-is-not-an-object`.
2. Non-authoring reviewer re-runs the battery and records it on the PR.
3. Merge.

Held out of the 17-PR queue for the same reason as the previous nine.
