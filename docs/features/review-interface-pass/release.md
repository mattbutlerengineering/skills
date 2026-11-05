---
stage: ship
run: feature:review-interface-pass
date: 2026-11-04
outcome: released
released-at: 2026-11-05
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1155
assumptions:
  - "Release authorization is none (brief): prepare and stop. No merge, tag, version bump or branch deletion."
  - "Tracker: the brief gave no issue seed, so Ship filed exactly one plain issue, #1154 (label type:feature, title from the PRD), for the PR's `Closes #1154`; the PR body carries a `No work order:` line, as the brief's Tracker section directs."
  - "The run added no ADR (architecture.md records why none is owed), so no ADR number or index row needed checking."
---

# Release: An Interface domain pass for review

## Pre-flight

- [x] Verification green (verification.md: 11 PASS, 0 FAIL; battery re-run on HEAD below)
- [x] No secrets in diff; target config present (the diff outside docs matches `token` only as design-token prose and test strings; no credentials; no config needed)
- [x] Migrations/data changes have a tested forward path (none: skill text and a test)
- [x] Rollback plan concrete (commands/steps below)
- [x] review.md: no critical or major finding; two minors deferred
- [x] No ADRs added by the run

## Rollback plan

Door: two-way — body-only skill text, a reference and a pin test; a revert undoes it, no version is published and no data changes.

Blast radius: a reviewer on a UI diff may report a false positive or read one extra file (`*.html` selects docs pages, one quick read); nobody notices until a UI diff is reviewed. Shared files (README credits, docs/backlog.md) may conflict with sibling runs at merge.

```
# before merge: close the PR
gh pr close 1155
# after merge: revert the merge commit on main
git revert -m 1 <merge-sha>
```

## Release log

1. `git fetch origin && git merge-tree --write-tree HEAD origin/main` → exit 0, tree 6ff55023e783ab36c6085495e2943f0cd3f6558b, no conflicts.
2. `python3 launch_demo.py config` → `SHIP`, `launch-demo: 0 problem(s)`. Loaded `launch-demo`, wrote `docs/launches/review-interface-pass/{launch.md,storyboard.json,demo.tape,launch.mp4}` (`render` → `PRODUCED`, duration 24.97s, h264 + aac), committed as `docs(review-interface-pass): launch brief for the Interface review pass`.
3. Battery on HEAD: `run_tests.py` → `tests: 3994 tests across 127 modules in 50.2s on 8 workers, 0 problem(s)`; `lint.py` → `lint: 0 problem(s) across 35 skills`; `kb.py drift` → `drift: 0 problem(s)`; `gates.py` → `gates: 0 problem(s)`; `gates.py --selftest` → `selftest: ok`.
4. `git push -u origin feat/review-interface-pass` → new branch pushed.
5. `gh issue create --label type:feature` → https://github.com/mattbutlerengineering/skills/issues/1154
6. `gates.pr_body_problems(body)` → `[]`; `gh pr create` → https://github.com/mattbutlerengineering/skills/pull/1155

## Post-release checks

- Nothing is deployed: the release is a pull request awaiting the Owner's merge; the post-release smoke check happens after the merge.
- Fix runs: not a fix run.

## Outcome

Prepared and stopped — waiting on https://github.com/mattbutlerengineering/skills/pull/1155 to merge. The run stays at Ship until the merge is written back.
