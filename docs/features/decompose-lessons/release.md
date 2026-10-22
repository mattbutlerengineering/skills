---
stage: ship
run: feature:decompose-lessons
date: 2026-10-20
outcome: released
released-at: 2026-10-20
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1050
assumptions:
  - "Release authorization is the brief's default, prepare and stop. Ship pushes the branch, opens one PR and stops. It does not merge, tag, bump the version or delete a branch."
  - "No plugin.json bump on this branch (ADR-0095). `git diff --stat origin/main...HEAD -- .claude-plugin/ factory/` prints nothing, and the only skills/ change is skills/decompose/SKILL.md. That skill change needs a wave chore(release) PR that bumps plugin.json once after the wave lands. It is a follow-up for the Owner; this run neither opened nor wrote it."
  - "Issue #988 seeds the run and the PR closes it. No work order is mirrored, so the PR body carries a `No work order:` line."
  - "origin/main (c89a989) is the merge base: it did not move. Open PR #1049 (docs-only, release.md of two other runs) is disjoint from this branch; the chain simulation (merge-tree of main plus #1049, then this branch) is clean. So the five checks ran on HEAD 94a53ee, which is the merged tree up to those docs."
  - "Launch brief not produced. `launch_demo.py config` prints SHIP, but this stage's brief commits release.md only, so Ship logs the verdict and leaves the launch brief to the Owner (on demand: /idea-to-prod:launch-demo on the PR)."
  - "The lessons file (docs/factory/decompose-lessons.jsonl) was NOT committed by this run, and `update` was not run against this repo."
---

# Release: A ranked lessons file for Decompose

## Pre-flight

- [x] Verification green. verification.md: 13 of 13 PRD criteria PASS (on cb1151b; review fixes landed after, so Ship re-ran the five checks on HEAD `94a53ee`):
      - `python3 run_tests.py` -> `tests: 3551 tests across 109 modules in 25.5s on 8 workers, 0 problem(s)`
      - `python3 lint.py` -> `lint: 0 problem(s) across 34 skills`
      - `python3 kb.py drift` -> `drift: 0 problem(s)`
      - `python3 gates.py` -> `gates: 0 problem(s)`; `python3 gates.py --selftest` -> `selftest: ok`
- [x] Review: no critical finding open, confirmed against review.md (0 critical; 4 major, 3 fixed, 1 deferred with a mitigation; 6 minor, 2 fixed, 4 deferred).
- [x] No secrets in the diff: the tool, its tests, a `factory.py` row, `tests/test_dual_membership.py`, CLAUDE.md, CONTEXT.md, ADR-0113 with its index row, `skills/decompose/SKILL.md`, run docs. The tool reads local files and git refs only.
- [x] No migrations or data changes; no lessons file committed.
- [x] ADR-0113 is free on origin/main, has its row in `docs/adr/README.md`, and is `provisional`.
- [x] Pairwise hazard (docs/kb/cross-pr-merge-hazards.md). `git fetch origin` -> origin/main `c89a989` equals the merge base. `git merge-tree --write-tree origin/main HEAD` -> `6af84d4`, exit 0. Open PR #1049 touches only two other runs' release.md files; chain simulation main+#1049 then HEAD -> `20a07b9`, exit 0.
- [x] Protected paths: `git diff --stat origin/main...HEAD -- .claude-plugin/ factory/` -> empty; `git diff --name-only origin/main...HEAD -- skills/` -> `skills/decompose/SKILL.md` only.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert removes a new root-only tool, its tests, docs and one skill step. It writes nothing and no lessons file exists.

Blast radius: this repo, and once the plugin ships, Decompose drafts in installed plugins (the skill step does nothing without a lessons file). A broken tool turns `make check` red here only.

```
# Before merge: close the PR; nothing reached main
gh pr close 1050

# After merge: revert the squash-merge commit
git checkout -b revert/decompose-lessons origin/main
git revert <merge sha of the PR>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/decompose-lessons
gh pr create --body-file <body>   # needs a No work order: line and a Closes #N line
```

## Release log

1. Five checks on HEAD `94a53ee` -> all clean (strings above).
2. `git fetch origin`; origin/main `c89a989` is the merge base; merge-tree clean; PR #1049 chain simulation clean.
3. `git diff --stat origin/main...HEAD -- .claude-plugin/ factory/` -> empty; skills/ change is only `skills/decompose/SKILL.md`. No version bump here.
4. `python3 launch_demo.py config` -> verdict and reason line verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   The launch-demo skill was not run (see the assumptions).
5. `git push -u origin feat/decompose-lessons` -> new branch on origin.
6. Body judged first (`gates.pr_body_problems` -> `[]`), then `gh pr create --base main --head feat/decompose-lessons` -> https://github.com/mattbutlerengineering/skills/pull/1050

## Post-release checks

- Nothing is released until the Owner merges. The checks that apply are the pre-merge CI on the PR and the pre-flight above.

## Release steps for the Owner

1. Review the PR and merge it (squash). This is gate 3; Ship did not merge.
2. Open the wave `chore(release)` PR that bumps `.claude-plugin/plugin.json` once (ADR-0095), because `skills/decompose/SKILL.md` changed. Ship did not open or write it.
3. After the release PR lands and the plugin cache refreshes, commit the first lessons file. Do not commit it earlier (early exposure: runs between the file and the cache refresh would count as treated though no draft could read it). Run `update` only after Ship, never mid-run.
4. Confirm or amend provisional ADR-0113.
5. Do not delete `feat/decompose-lessons` until the PR shows `MERGED`.
6. Write-back: `gh pr view 1050 --json state,mergedAt`. When merged, set `outcome: released`, add `released-at: <merge date>`, keep `pending-merge:`, and commit as `docs(decompose-lessons): ship - <one line>`. If it closed unmerged, leave `outcome: prepared`.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names. Flags that stand:

- Wave `chore(release)` PR for the skills/decompose/SKILL.md change (Owner).
- Early exposure of the first lessons file; `update` only after Ship.
- ADR-0113 is provisional.
- Deferred review items: per-signal `seen` (changes ADR-0113's on-disk shape; needs a superseding ADR and migration); vote-order semantics; zero-item treated pool reads "not higher"; no file size cap; the S9 no-hand-written-seed gap (a well-formed, sourced, fabricated lesson still loads; the PR diff is the control); architecture.md's stale 26/4/145 pair counts (shipped rule gives 18).
- Launch brief not produced (`launch_demo.py config` says SHIP).
