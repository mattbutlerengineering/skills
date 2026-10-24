---
stage: ship
run: maintenance:lessons-per-signal-seen
date: 2026-10-22
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1070
assumptions:
  - "Release authorization was not granted, so this pass prepares and stops: branch pushed, PR #1070 opened, nothing merged, deployed, tagged or published. Not an Owner answer."
  - "No wave release PR is owed: git diff origin/main..HEAD touches nothing under skills/, and .claude-plugin/plugin.json's version is untouched (ADR-0095)."
  - "The Owner deferred review's Major finding 1 in session (AskUserQuestion) and authorised one plain issue; it is #1069 (type:chore, no wo label), referenced from the PR and not closed by it."
  - "Release.md is committed after the PR was opened, so the PR already contains the branch head it was opened from; this one commit lands on the branch afterwards."
---

# Release: decompose_lessons keeps a signal that matures later (PR 1070)

## Pre-flight

- [x] Verification green: verification.md records 26 of 26 criteria PASS.
- [x] No secrets in diff; no target configuration needed (a root-only stdlib tool).
- [x] Migrations/data changes: the on-disk shape of the lessons file changes (ADR-0116). No lessons file is committed on main, so nothing to migrate; load refuses the old per-run shape with a message. Forward path is covered by tests.
- [x] ADR numbering: ADR-0116 is free on origin/main (it ends at 0115) and has its row in docs/adr/README.md; ADR-0113 is marked superseded in part.
- [x] Review: no unfixed critical. One Major (hit run seen before its clean partner exists never pairs) is pre-existing on main and deferred by the Owner to #1069. Minors deferred: three lines over 79 columns in decompose_lessons.py and the _ballot docstring.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way - a revert restores the previous code, and no lessons file exists on main to be left in the new shape.

Blast radius: decompose_lessons.py only, a root-only tool; no skills/ or plugin payload change, so no stamped repo or installed plugin cache is affected. If a lessons file was already written in the new shape by then, it would fail to load under the old code and be regenerated.

```
# before merge: close PR 1070 without merging
gh pr close 1070
# after merge: revert the squash commit on main via a new PR
git revert <squash-sha> && git push   # on a branch, then open a PR
```

## Release log

1. Local CI before push: python3 run_tests.py -> 3806 tests across 118 modules, 0 problem(s); python3 lint.py -> lint: 0 problem(s) across 34 skills; python3 kb.py drift -> drift: 0 problem(s); python3 gates.py -> gates: 0 problem(s); python3 gates.py --selftest -> selftest: ok.
2. Launch brief: not run; this pass prepares only, and the fix touches no user-facing surface.
3. gh issue create (type:chore, no wo label) -> https://github.com/mattbutlerengineering/skills/issues/1069 (the deferred Major).
4. git push -u origin fix/lessons-per-signal-seen -> new branch pushed.
5. gh pr create -> https://github.com/mattbutlerengineering/skills/pull/1070 (carries a No work order line and Closes #1061).
6. Merge, deploy, tag, publish -> not executed (no release authorization).

## Post-release checks

- Nothing to smoke-check yet: the change is unmerged. After merge, run python3 run_tests.py on main and confirm #1061 closed by the PR.
- Fix runs: producing boundary decompose_lessons.fold/_measured and its consumers (pairs, votes, serialize, load) were inspected in Review; the related pre-existing pairing gap is #1069 and stays open by decision. Minor cleanups remaining: three lines over 79 columns and the _ballot docstring, deferred as no gate enforces a column limit.

## Outcome

Prepared and stopped, waiting on PR 1070. Owner steps:

1. Review PR 1070 and its CI checks.
2. Merge it (squash) once green: gh pr merge 1070 --squash.
3. No version bump and no release PR: skills/ is unchanged (ADR-0095).
4. Confirm #1061 closed and #1069 still open.
5. Re-run the Ship stage so its Release step records outcome: released and released-at.
