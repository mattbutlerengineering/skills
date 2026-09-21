---
stage: ship
run: maintenance:a-filter-rebuilds-the-redacted-id
date: 2026-08-27
assumptions: ["the autorun brief carries no release authorization, so
  ship prepares and stops"]
---

# Release: a filter rebuilds the redacted id

**Prepared, not executed.** No release authorization exists for this
run. No pull request was opened; nothing merged, tagged or published.

## Pre-flight

- Verification green, five criteria, all PASS.
- No unfixed critical findings. `review.md` carries one major, accepted
  with its cost, and one pre-existing limitation left to its owner.
- No secrets in the diff; no configuration added; no network call. Every
  test in the file injects a fake `gh` runner.
- No migration in the schema sense. There is a data consequence: a
  malformed shortId keys differently than before, so an intake filed
  under an old key would be filed once more. Bounded to shortIds with a
  character outside `[A-Za-z0-9_.:-]`; well-formed ones are unaffected
  and pinned by test.
- `sweeps.py` is not mirrored into the stamped payload, so nothing under
  `factory/templates/**` changed and `factory/manifest.json` is
  untouched.

## Rollback

```
git revert <sha>
```

No manifest regeneration is needed on the way back, for the same reason
none was needed on the way out. Or before merge:

```
git push origin --delete agent/a-filter-rebuilds-the-redacted-id
```

## Note for whoever merges

Open PR #339 also edits `sweeps.py` and `tests/test_sweeps.py`. The
hunks do not overlap: #339 changes `known_keys` and `screen` (module
lines 114-124 and 329+) and adds tests inside `TestFileIssues`
(lines 459 and 490), while this branch changes `UNSAFE_KEY`'s
neighbourhood (line 103) and `sentry_intakes` (line 157) and adds a
class beside `TestUntrustedInputBoundary` (line 213). Git merges them
without conflict in either order.

## Blocking condition

ADR-0036 clause 2: a non-authoring reviewer must re-execute the
verification and record it on the pull request.

## Remaining steps for a human

1. Open a pull request from `agent/a-filter-rebuilds-the-redacted-id`.
2. Non-authoring reviewer re-runs the battery and records it on the PR.
3. Merge.

Held out of the 17-PR queue for the same reason as the previous seven.
