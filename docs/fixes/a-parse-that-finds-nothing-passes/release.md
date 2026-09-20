---
stage: ship
run: maintenance:a-parse-that-finds-nothing-passes
date: 2026-08-30
assumptions:
  - "The run stops at 'PR open'. Merge is ADR-0033 gate 3, a human decision, and an agent-authored PR merging itself is exactly what that gate exists to prevent. Nothing here was merged and no issue was closed; #417 closes on merge via the commit trailer."
  - "'production' for this repo is main — the plugin is vended from the repo and the payload is stamped from factory/templates. No deploy step, no version tag. Same reading as prior runs in this directory."
---

# Release: a parse that finds nothing turns its test green

## What shipped

- Branch `agent/a-parse-that-finds-nothing-passes`, commit `66221ed`
- **PR #418**, open against `main`
- Intake **#417**, closed on merge by the `Closes #417` trailer

One file changed: `tests/test_sweeps.py`. No shipped tool, no workflow,
no mirrored payload file — so no `update-manifest` and no detector E
interaction.

## State at hand-off

| | |
| --- | --- |
| Tests | `Ran 1346 tests ... OK` |
| Lint | `lint: 0 problem(s) across 24 skills` |
| Gates | `gates: 0 problem(s)`, `selftest: ok` |
| one_owner | 9 problems, all pre-existing (`tests/` is EXCLUDED) |
| Merge | **not done** — human gate |

## Held deliberately

The PR queue stood at 41 open when this run finished. Consistent with
every prior run in this directory, the run ends at "pushed, PR opened,
merge is the operator's call". Merging is not this run's to take.

## Seeds

- `curl_argv()` in the same class guards at its call site rather than in
  the helper — inconsistent with `commands()` after this change, but
  guarded, so nothing is unpinned. Worth an issue only if it gains a
  second caller. Recorded in review.md §3, not filed.
- The static sweep's other 50 candidate loops are argued safe by the
  empty-collection table, one collection at a time. That table is
  reproducible (`scratchpad/emptycheck.py` shape) but is not committed —
  it is a review pre-pass, not a gate, and it would go stale the moment a
  collection is renamed.
