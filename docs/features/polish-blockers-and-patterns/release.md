---
stage: ship
run: feature:polish-blockers-and-patterns
date: 2026-11-04
outcome: released
released-at: 2026-11-05
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1157
assumptions:
  - "Release authorization is NONE (brief): prepare and stop. No merge, tag, version bump or branch deletion."
  - "Tracker: the brief's no-interaction answer leaves Detector B's `Closes #N` half owed, so Ship filed one plain `type:feature` issue (#1156) and the PR closes it with a `No work order:` line, as the brief's Tracker section directs."
---

# Release: named blockers and code detection patterns in polish

## Pre-flight

- [x] Verification green (no unresolved failures): `verification.md` has 10 PASS, 1 NOT RUN (the paid kill test), 0 FAIL; `review.md` has no critical or major finding, five minors deferred.
- [x] No secrets in diff; target config present: the diff is skill text, a test module, a README line, ledger rows and run artifacts; no configuration is needed.
- [x] Migrations/data changes have a tested forward path: none exist.
- [x] ADRs: the run added none (`architecture.md`: no decision met the ADR bar), so no number or index row is owed.
- [x] Rollback plan concrete (below)
- [x] Merge-tree against base is clean: `git merge-tree --write-tree HEAD origin/main` after `git fetch origin` printed a tree id (`b523c1f6…`) and exited 0.

## Rollback plan

Door: two-way — skill prose, a test module and a README line; a revert undoes it, with no migration and no published version.

Blast radius: anyone running `polish` sees the longer step 5 and table; nobody else notices.

```
# after the PR merges, from a checkout of main:
git revert -m 1 <merge commit sha>   # or, for a squash merge: git revert <squash sha>
git push origin <revert branch>      # open the revert as a PR
# before it merges: gh pr close 1157
```

## Release log

1. `python3 launch_demo.py config` → `SHIP`, `launch-demo: 0 problem(s)`. Loaded the `launch-demo` skill, ran `probe` → `READY`, wrote `docs/launches/polish-blockers-and-patterns/{launch.md,storyboard.json}`, `render` → `PRODUCED` (`launch.mp4`, h264 + aac, duration 26.23s, 0 problems). The first `render` was cancelled before it finished because the storyboard's first command (`grep -c '^| `…`) counted 5, not the 12 rows its caption names; the command was corrected to `grep -c '^| [`A]'` (12) and the render re-run. Committed as `ea44df3`.
2. Re-ran the battery on HEAD from the worktree → `tests: 3998 tests across 127 modules in 60.3s on 3 workers, 0 problem(s)`; `lint: 0 problem(s) across 35 skills`; `drift: 0 problem(s)`; `gates: 0 problem(s)`; `selftest: ok`.
3. `git push -u origin feat/polish-blockers-and-patterns` → new branch on origin.
4. `gh issue create --label type:feature` → https://github.com/mattbutlerengineering/skills/issues/1156 (body first posted with stray backslashes before backticks; fixed with `gh issue edit`).
5. `gates.pr_body_problems` on the PR body → `[]` (an earlier draft quoted a work-order id in the waiver line and was reworded so the needs-review job reads no claim).
6. `gh pr create` → https://github.com/mattbutlerengineering/skills/pull/1157, body carrying `Closes #1156`, a `No work order:` line and the `## Merge danger` section.

## Post-release checks

- Not applicable before merge: nothing is live. The surface users get is the plugin on `main`; the write-back checks the merged PR.
- Fix runs: not a fix run.
- Not verified: the kill test (does the table make a code-only `polish` find more) is NOT RUN, needs the Owner's paid run (command in `verification.md`).

## Outcome

Prepared and stopped — waiting on the pull request `pending-merge:` names (#1157). Merge, tag and version are the Owner's; the plugin version is untouched (ADR-0095).
