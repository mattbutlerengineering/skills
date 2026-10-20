---
stage: ship
run: feature:size-band-calibration
date: 2026-10-20
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1047
assumptions:
  - "Release authorization is Owner decision 3 in autorun-brief.md, prepare and stop. Ship pushes the branch, opens one PR and stops. It does not merge, tag, bump the version or delete a branch."
  - "No plugin.json bump on this branch (ADR-0095 rule 1). `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/` prints nothing. The tool is root-only (ADR-0112), so ADR-0095 rule 2's payload-only release PR does not apply; no chore(release) PR is needed."
  - "Issue #987 seeds the run and the PR closes it. No work order is mirrored, so the PR body carries a `No work order:` line."
  - "origin/main (27626c1) is the branch point: it did not move past it, and no other PR is open, so there is no chain to simulate. The merge test and the five checks ran on the branch tree, which is the merged tree."
  - "Launch brief not produced. `launch_demo.py config` prints SHIP, but this stage's brief commits release.md only, so Ship logs the verdict and leaves the launch brief to the Owner (on demand: /idea-to-prod:launch-demo on the PR), as the model release does."
---

# Release: Calibrate S/M/L size bands from past error

## Pre-flight

- [x] Verification green. verification.md: 9 of 9 PRD criteria PASS. Ship
      re-ran the five checks on HEAD `31db418`:
      - `python3 run_tests.py` -> `tests: 3472 tests across 108 modules in 25.8s on 8 workers, 0 problem(s)`
      - `python3 lint.py` -> `lint: 0 problem(s) across 34 skills`
      - `python3 kb.py drift` -> `drift: 0 problem(s)`
      - `python3 gates.py` -> `gates: 0 problem(s)`; `python3 gates.py --selftest` -> `selftest: ok`
- [x] Review: no critical finding open, confirmed against review.md
      (0 critical; the one major, a non-finite cost printed as a figure, is
      fixed in b4e181b). Deferred items are listed under Outcome.
- [x] No secrets in the diff: 15 files (the module, its tests, a
      `factory.py` row, `tests/test_dual_membership.py`, CLAUDE.md,
      CONTEXT.md, ADR-0112 and its index row, run docs). The tool reads
      local files and git refs only.
- [x] No migrations or data changes; nothing under `evals/results/`.
- [x] ADR-0112 is free on origin/main `27626c1`, has its row in
      `docs/adr/README.md`, and is `provisional`.
- [x] Pairwise hazard (docs/kb/cross-pr-merge-hazards.md). `git fetch
      origin main` -> `27626c1`, equal to the merge base. `gh pr list
      --state open` -> none. `git merge-tree --write-tree origin/main
      HEAD` -> `4496c92`, exit 0. With no other open PR there is no chain
      link to test.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert removes a new root-only read-only tool, its
`factory.py` verb, its tests and docs. It writes nothing and no record
depends on it.

Blast radius: this repo only. Nothing ships in the plugin payload or to
stamped repos. A wrong call shows as wrong numbers in
`python3 size_band_calibration.py` output, read only by the Owner and the
later Decompose loops; a broken tool turns `make check` red here only.

```
# Before merge: close the PR; nothing reached main
gh pr close 1047

# After merge: revert the squash-merge commit
git checkout -b revert/size-band-calibration origin/main
git revert <merge sha of the PR>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/size-band-calibration
gh pr create --body-file <body>   # needs a No work order: line and a Closes #N line
```

## Release log

1. Five checks on HEAD `31db418` -> all clean (strings above).
2. `git fetch origin main`; origin/main `27626c1` is the merge base;
   merge-tree clean; no open PRs.
3. `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/`
   -> empty. No version bump, no release PR.
4. `python3 launch_demo.py config` -> verdict and reason line verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   The launch-demo skill was not run (see the assumptions).
5. `git push -u origin feat/size-band-calibration` -> new branch on origin.
6. Body judged first (`gates.pr_body_problems` -> `[]`), then
   `gh pr create --base main --head feat/size-band-calibration` ->
   https://github.com/mattbutlerengineering/skills/pull/1047

## Post-release checks

- Nothing is released until the Owner merges. The checks that apply are the
  pre-merge CI on the PR and the pre-flight above.

## Release steps for the Owner

1. Review the PR and merge it (squash). This is gate 3; Ship did not merge.
2. Confirm or amend provisional ADR-0112.
3. Version: none (no `skills/`, `.claude-plugin/` or `factory/` change).
4. Do not delete `feat/size-band-calibration` until the PR shows `MERGED`.
5. Write-back: `gh pr view 1047 --json state,mergedAt`. When merged, set
   `outcome: released`, add `released-at: <merge date>`, keep
   `pending-merge:`, and commit as `docs(size-band-calibration): ship - <one line>`.
   If it closed unmerged, leave `outcome: prepared`.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names.
Flags that stand:

- ADR-0112 is provisional.
- Deferred review items: reject non-finite `cost` in
  `cost_ledger.line_problems` (root cause of the fixed major; mirrored seam
  and manifest regen); whether a work-order token seen in two runs is
  ambiguous even at one size; minors left as is (unreachable `else 0.0` in
  `cost_mean`, unpinned scope of the non-finite guard).
- Launch brief not produced (`launch_demo.py config` says SHIP).
