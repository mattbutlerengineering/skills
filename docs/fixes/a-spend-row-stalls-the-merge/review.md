---
stage: review
run: maintenance:a-spend-row-stalls-the-merge
date: 2026-10-25
---

# Review: a ship step's spend file stalls the Conductor's merge as unreviewed

## Scope

`git diff origin/main...fix/a-spend-row-stalls-the-merge` at `343f97c`:
`conductor_merge.py`, `trace.py`, their payload mirrors,
`factory/manifest.json`, `tests/test_conductor_merge.py`,
`tests/test_trace.py` and the run's `defect.md` and `verification.md`.

A fresh general-purpose subagent was given the diff and the context files,
not the author's conclusions. It reproduced each probe in a scratch repo.
The fixes landed in `8c13378`. On that commit the full checks printed:

- `tests: 3911 tests across 122 modules in 29.6s on 8 workers, 0 problem(s)`
- `lint: 0 problem(s) across 35 skills`
- `drift: 0 problem(s)`
- `gates: 0 problem(s)`
- `selftest: ok`
- `factory-init: 0 problem(s)`

## Findings

### Major: any file added under RUNS_DIR merged unreviewed

- Scenario: the first fix allowed every added path starting with
  `docs/factory/costs/runs/`. `cost_ledger.read`, which detector G uses,
  lists only RUNS_DIR's top level and skips non-`.jsonl` files. So after
  the review head a Worker commits `docs/factory/costs/runs/sub/evil.py`.
  It appears in both diffs, the drift check passes, CI never reads the
  file, and code nobody reviewed reaches main. The reviewer reproduced
  this in a scratch repo.
- Standard: none
- Decision: fixed in `8c13378`. `run_spend_file` accepts only the path
  `cost_ledger.run_ledger_path` writes. Cases for a nested file, a `.py`
  file and a dotfile are pinned.

### Major: a rename onto an allowed path hid the deletion it carries

- Scenario: `git diff --name-only` detects renames by default and prints
  only the new path. A post-review `git mv src/core.py
  docs/features/x/release.md` listed only `release.md`, which is allowed,
  so the deletion of `src/core.py` would merge unreviewed. This predates
  the run, but the new allowance made it reachable for spend files too.
- Standard: none
- Decision: fixed in `8c13378`. Both drift diffs run `--no-renames`, and a
  real-git case with a rename onto `release.md` now stalls, naming
  `src.txt`.

### Minor: a spend file added after the review and then rewritten still passes

- Scenario: `--diff-filter=A` compares trees, so a file absent at the head
  and present on the branch is A however many commits touched it. The
  first docstring said "never rewritten", which the check cannot see.
- Standard: none
- Decision: fixed in wording in `8c13378` ("absent at the head"). Not
  enforced. Every post-review spend row is unreviewed content, just as an
  appended aggregate row was before #954. Detector G checks a row's shape
  in CI, and no gate checks its values. That was equally true before this
  run, so it is not a regression. It is recorded here as a known limit.

### Minor: a second name for one fact

- Scenario: `COSTS = COST_LEDGER` kept two names for the same value.
- Standard: none
- Decision: fixed in `8c13378`. `COSTS` is gone.

## Passes with no findings

- Correctness: `review_drift`'s only caller is `_drift`, and the `added=()`
  default keeps the old call shape. The reviewer confirmed that a file
  deleted and re-added classifies correctly: a tree diff shows M or
  nothing, never A. In `trace.py`, `fullmatch` against `#[1-9][0-9]*`
  makes `int(key[1:])` safe, and Unicode digits that `\d` matched are now
  refused.
- Security: the two majors above were the security-relevant surface, and
  both are fixed. No secrets, and no new input boundary.
- Complexity: one small pure helper (`run_spend_file`), and no `lean:`
  marker.
- ADR compliance: ADR-0034 (cost ledger shape) and ADR-0084 (issue key)
  hold, and the payload is regenerated. No new ADR is owed: the fix
  restores the existing "merged code is reviewed code" contract.
- Domain passes: none selected (no payment, migration or dependency path).
- Standards: no matching factory statement.

## Verdict

Ready to ship. No critical finding was raised. Both majors and two minors
are fixed in `8c13378`, and the rewrite limit is recorded rather than
enforced. One check stays unknown: a live Conductor batch merging past its
ship step's spend file (verification.md criterion 6, NOT RUN).
