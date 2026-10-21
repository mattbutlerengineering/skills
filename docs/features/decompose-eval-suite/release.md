---
stage: ship
run: feature:decompose-eval-suite
date: 2026-10-20
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1051
assumptions:
  - "Release authorization is the brief's default, prepare and stop. Ship pushes the branch, opens one PR and stops. It does not merge, tag, bump the version or delete a branch, and ran no `claude plugin eval` or model call."
  - "No plugin.json bump and no chore(release) PR: `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/` prints nothing, and the tool is root-only (ADR-0114). The Owner's pending wave release PR for the Decompose skill change from the decompose-lessons run is a separate follow-up."
  - "Issue #989 seeds the run and the PR closes it. No work order is mirrored, so the PR body carries a `No work order:` line."
  - "origin/main (5179e5c) equals the merge base: it did not move, and there are no open PRs to simulate. So the five checks ran on HEAD fc31bb6, with no merge of main into the branch."
  - "Launch brief not produced. `launch_demo.py config` prints SHIP, but this stage's brief commits release.md only, so Ship logs the verdict and leaves the launch brief to the Owner (on demand: /idea-to-prod:launch-demo on the PR)."
---

# Release: A scored, offline-gradable eval suite for Decompose

## Pre-flight

- [x] Verification green. verification.md: 11 of 11 PRD criteria PASS. Review fixes landed after it, so Ship re-ran the five checks on HEAD `fc31bb6`:
      - `python3 run_tests.py` -> `tests: 3632 tests across 111 modules in 25.3s on 8 workers, 0 problem(s)`
      - `python3 lint.py` -> `lint: 0 problem(s) across 34 skills`
      - `python3 kb.py drift` -> `drift: 0 problem(s)`
      - `python3 gates.py` -> `gates: 0 problem(s)`; `python3 gates.py --selftest` -> `selftest: ok`
- [x] Review: no critical finding open, confirmed against review.md (0 critical; 1 major fixed in cb18259; minors fixed, 2 deferred, 1 noted).
- [x] No secrets in the diff: a root-only offline grader, its tests, a fixture suite, a `factory.py` row, `tests/test_dual_membership.py`, CLAUDE.md, ADR-0114 with its index row, run docs. The tool reads local files only.
- [x] No migrations or data changes.
- [x] ADR-0114 is free on origin/main (highest there is 0113), has its row in `docs/adr/README.md`, and is `provisional`.
- [x] Pairwise hazard (docs/kb/cross-pr-merge-hazards.md). `git fetch origin` -> origin/main `5179e5c` equals the merge base; `gh pr list --state open` -> `[]`; `git merge-tree --write-tree origin/main HEAD` -> `74e22b8acc936af7c2fa6b872603e719787ccd06`, exit 0.
- [x] Protected paths: `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/` -> empty.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert removes a new root-only tool, its tests, a fixture suite and docs. Nothing is written at runtime.

Blast radius: this repo only. A broken tool turns `make check` red here; no installed plugin or stamped repo carries it.

```
# Before merge: close the PR; nothing reached main
gh pr close 1051

# After merge: revert the squash-merge commit
git checkout -b revert/decompose-eval-suite origin/main
git revert <merge sha of the PR>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/decompose-eval-suite
gh pr create --body-file <body>   # needs a No work order: line and a Closes #N line
```

## Release log

1. Five checks on HEAD `fc31bb6` -> all clean (strings above).
2. `git fetch origin`; origin/main equals the merge base; no open PRs; merge-tree clean.
3. Protected-path diff -> empty. No version bump here.
4. `python3 launch_demo.py config` -> verdict and reason line verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   The launch-demo skill was not run (see the assumptions).
5. `git push -u origin feat/decompose-eval-suite` -> new branch on origin.
6. Body judged first (`gates.pr_body_problems` -> `[]`), then `gh pr create --base main --head feat/decompose-eval-suite` -> https://github.com/mattbutlerengineering/skills/pull/1051

## Post-release checks

- Nothing is released until the Owner merges. The checks that apply are the pre-merge CI on the PR and the pre-flight above.

## Release steps for the Owner

1. Review the PR and merge it (squash). This is gate 3; Ship did not merge.
2. Confirm or amend provisional ADR-0114.
3. Decide whether to run the first paid `claude plugin eval . --tag decompose`. It costs money and needs the Owner's say-so; LEDGER stays unchanged until a real run.
4. Do not delete `feat/decompose-eval-suite` until the PR shows `MERGED`.
5. Write-back: `gh pr view 1051 --json state,mergedAt`. When merged, set `outcome: released`, add `released-at: <merge date>`, keep `pending-merge:`, and commit as `docs(decompose-eval-suite): ship - <one line>`. If it closed unmerged, leave `outcome: prepared`.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names. Follow-ups for the Owner:

- Not verified: the suite has never run, the four llm graders are unexercised, and a first paid run needs the Owner's say-so. LEDGER unchanged.
- A 1.000 grade means only "no defect the grader knows". The CLI summary carries no caveat because its strings are PRD-fixed; a footer is the Owner's call.
- No input size cap; edge resolution is quadratic (about 2.5 s at 1.2 MB).
- `plugin-evals/decompose/fixtures/` has no case.yaml; harness behaviour is unknown until a first paid run.
- Confirm or amend provisional ADR-0114.
- Separate: the pending wave release PR for the Decompose skill change from the decompose-lessons run.
- Launch brief not produced (`launch_demo.py config` says SHIP).
