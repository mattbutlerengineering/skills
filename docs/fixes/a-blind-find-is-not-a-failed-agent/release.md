---
stage: ship
run: maintenance:a-blind-find-is-not-a-failed-agent
date: 2026-08-25
assumptions:
  - "No release authorization exists to invoke: this run has no autorun-brief.md, and autorun's default absent an explicit yes is prepare-and-stop. So the branch is pushed and the PR is open, and nothing is merged. ADR-0036 clause 2 independently forbids it — I authored every commit here, so a non-authoring reviewer must re-execute verification and record it on the PR before it can land"
  - "Ship for a maintenance run of this size is a single-commit-range merge per the protocol's Run scale section, not a tagged release. The plugin version is untouched: nothing under skills/ changed"
---

# Release: a blind find-pr is not a failed agent

## What shipped, and how far

Prepared, not released. Branch `agent/blind-find-is-not-a-failed-agent`
pushed; **PR #349** open against `main`, closing intake issue #348.
Seven commits, `7414c4f` through `c81d230`.

The merge is the operator's. This run stops here by design.

## Pre-flight

| Check | Result |
|---|---|
| Verification green | `verification.md`, seven criteria, no unresolved failures |
| Review clean of unfixed criticals | `review.md` — zero criticals; one major deferred with its settling condition named |
| Suite | `Ran 1348 tests in 16.076s / OK` |
| Lint | `lint: 0 problem(s) across 24 skills` |
| Gates | `gates: 0 problem(s)` / `selftest: ok` |
| One-owner pre-pass | `one-owner: 9 problem(s)` — baseline, unchanged |
| Secrets in diff | none — grepped the full range for key/token assignment forms |
| Payload mirror pinned | `factory_init.py update-manifest` re-run after the review's edits; `factory-init: 0 problem(s)` |
| Config required in target env | none — the change reads an existing step output |
| Migration / data change | none |

## CI on #349

Observed after the push, not asserted:

```
check                 pass
review                pass
needs-review-label    pass
merged-label          skipping
```

`OPEN MERGEABLE CLEAN`. `merged-label` skips because that job runs only
on `opened`/`reopened` and on merge — a job that did not re-run, not one
that failed.

## Rollback

Concrete, in order of preference:

1. **Before merge** — close PR #349 unmerged. Nothing has moved.
2. **After merge** — `git revert c81d230..2fd5f5c` on `main`, then
   `python3 -B factory_init.py update-manifest` and commit the manifest
   with the revert. Two files under `factory/templates/` and
   `factory/manifest.json` are regenerated artifacts and must move with
   their roots or detector E reddens `main`.

No external state to unwind: no deploy, no published package, no issue
transitions performed, no labels applied. The workflow change is inert
until the next assembler dispatch.

## Post-release smoke

Not applicable — nothing is deployed. The change's live surface is a
GitHub Actions step condition that fires only on an assembler run, and
the run's one unverifiable assumption (Finding 1 in `review.md`) is
settled by observing the first real blind `find-pr`, not by a smoke
check available now.

## Hiccups, recorded

**I desynced the payload mirror mid-review.** Fixing two docstring
findings meant editing `assembler.py`, which is in `factory_init.MIRRORS`,
after I4 had already pinned the manifest. The suite failed on
`test_every_mirrored_root_file_matches_its_payload_copy (mirror='assembler.py')`.
Re-running `update-manifest` fixed it.

This is worth reading against the **previous run's `release.md`**, which
logged an "intermittent single-test failure" whose identity was lost to
tail-truncated output on both occurrences, with stale bytecode as the
leading hypothesis. This occurrence is neither intermittent nor
bytecode — it is deterministic, and its cause is now named. It does not
close that earlier question (those reportedly cleared on re-run without a
regeneration, which a stale mirror would not do); it removes one guess
and supplies one confirmed cause.

The generalisable fix was procedural: **capture full suite output to a
file rather than reading a truncated tail**, which turned a
three-occurrence mystery into a one-line diagnosis. Worth a seed.

## Handed to the operator

- **Merge or reject #349.** ADR-0036 clause 2 blocks me: a non-authoring
  reviewer must re-execute verification and record it on the PR. The
  `github-actions[bot]` factory review pre-chews linting and does not
  satisfy the clause.
- **Weigh the deferred major first.** `review.md` Finding 1 — the change
  may be a no-op if GitHub discards outputs from a failed step. It cannot
  be worse than the status quo, but a reviewer should decide whether
  shipping an unverifiable improvement is the right call rather than
  discover the caveat after merge.
- **#349 joins a queue of 15.** The merge-order plan (waves, conflict
  matrix, branch-side resolution recipe) is unchanged in shape; this PR
  touches `assembler.py` and `assembler.yml`, which no other open PR
  touches, so it is conflict-free against all of them except for
  `factory/manifest.json`, which must be regenerated after each merge in
  its wave.
