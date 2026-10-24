---
stage: ship
run: maintenance:seen-before-partner
date: 2026-10-24
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1074
assumptions:
  - "Release authorization was not granted, so this pass prepares and stops: branch pushed, PR 1074 opened, nothing merged, deployed, tagged or published. Not an Owner answer."
  - "No wave release PR is owed: git diff origin/main..HEAD touches nothing under skills/, and .claude-plugin/plugin.json's version is untouched (ADR-0095)."
  - "The Owner accepted architecture.md's deviation from the brief's literal fold-on-use rule in session (AskUserQuestion): seen stays equal to measured and fold passes pairs only the hit runs that already had their chance. Review's open confirmation is closed."
  - "The Owner deferred review's two Minors in session and asked for no new issues: m5 (no test pins which clean run pairs uses as the exemplar, a gap already on main) and three lines over 79 columns already on main."
  - "Release.md is committed after the PR was opened, so the PR already contains the branch head it was opened from; this one commit lands on the branch afterwards."
---

# Release: a hit run seen before its clean partner still pairs (PR 1074)

## Pre-flight

- [x] Verification green: verification.md records its criteria as passing.
- [x] No secrets in diff; no target configuration needed (a root-only stdlib tool).
- [x] Migrations/data changes: none. The on-disk shape and header are unchanged (ADR-0117), so existing lessons files load as before.
- [x] ADR numbering: ADR-0117 is free on origin/main and has its row in docs/adr/README.md; ADR-0116 is marked superseded in part (its pairing-skip sentence only).
- [x] Review: no unfixed critical or major. Two Minors, both closed in this PR at the Owner's request after Review: m5 (a test now pins the first clean run in record order as the exemplar `pairs` picks) and the three over-79-column lines (rewrapped, no behaviour change).
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way - a revert restores the previous code, and the file shape is unchanged so no lessons file is left in a new format.

Blast radius: decompose_lessons.py only, a root-only tool; no skills/ or plugin payload change, so no stamped repo or installed plugin cache is affected. After a revert, a hit run seen before its partner would again fail to pair; lessons already written stay valid.

```
# before merge: close PR 1074 without merging
gh pr close 1074
# after merge: revert the squash commit on main via a new PR
git revert <squash-sha> && git push   # on a branch, then open a PR
```

## Release log

1. Local CI before push: python3 run_tests.py -> 3814 tests across 118 modules, 0 problem(s); python3 lint.py -> lint: 0 problem(s) across 34 skills; python3 kb.py drift -> drift: 0 problem(s); python3 gates.py -> gates: 0 problem(s); python3 gates.py --selftest -> selftest: ok.
2. Launch brief: not run; this pass prepares only, and the fix touches no user-facing surface.
3. git push -u origin fix/seen-before-partner -> new branch pushed.
4. gh pr create -> https://github.com/mattbutlerengineering/skills/pull/1074 (carries a No work order line and Closes #1069).
5. Merge, deploy, tag, publish -> not executed (no release authorization).
6. Follow-up commits after Review: test(decompose-lessons) pins the first clean run (m5 killed in a scratch mutation); refactor(decompose-lessons) rewraps three long lines; module 110 tests OK, no line over 79 columns.

## Post-release checks

- Nothing to smoke-check yet: the change is unmerged. After merge, run python3 run_tests.py on main and confirm #1069 closed by the PR.
- Documented decisions that stay: a later clean run that sorts earlier in record order does not re-open a made pair; a hit run and partner already folded unpaired under ADR-0116 stay stranded, and recovery is to delete the lessons file and re-run update.
- PR 1073 (docs write-back for the prior run) is separate and open; it is not part of this release.

## Outcome

Prepared and stopped, waiting on PR 1074. Owner steps:

1. Review PR 1074 and its CI checks (it now includes the m5 exemplar test and the rewrap).
2. Merge it (squash) once green: gh pr merge 1074 --squash.
3. No version bump and no release PR: skills/ is unchanged (ADR-0095).
4. Confirm #1069 closed.
5. Re-run the Ship stage so its Release step records outcome: released and released-at.
