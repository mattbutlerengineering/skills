---
stage: ship
run: feature:svg-mechanical-check
date: 2026-11-04
outcome: released
released-at: 2026-11-05
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1161
assumptions:
  - "Release authorization is none (brief): prepared and stopped. No merge, tag, version bump or branch deletion."
  - "Tracker: the brief seeds no issue, but detector B needs `Closes #N`, so Ship filed one plain issue, #1160 (label type:feature), and the PR carries `Closes #1160` plus a `No work order:` line, as the brief's Tracker section directs."
  - "launch_demo.py config printed SHIP, so the launch-demo skill ran; its output is committed under docs/launches/svg-mechanical-check/."
---

# Release: A mechanical SVG check for the diagram skills

## Pre-flight

- [x] Verification green: verification.md records 16 of 16 PRD criteria pass, no failures; the review's one major finding was fixed in `3be7ab1`.
- [x] No secrets in diff (a grep of the added lines for key/secret/token/password matched only review prose); no target config needed (skill text and a root stdlib script).
- [x] Migrations/data changes: none.
- [x] ADRs: the run added none (`git diff origin/main...HEAD -- docs/adr` is empty), so no number or index row is owed.
- [x] Rollback plan concrete (below).
- [x] Review: review.md has no unfixed critical finding; six minors are deferred with reasons.
- [x] Merge check: after `git fetch origin`, `git merge-tree --write-tree HEAD origin/main` (origin/main 0d4244e) exited 0 with a tree id, no conflicts.
- [x] Battery re-run on HEAD (see log 3).

## Rollback plan

Door: two-way — the change adds one root script, a `factory.py` verb, step-7 text, a one-line scaffold change and run docs; no data, version or public interface moves.

Blast radius: users of the two draft diagram skills; at worst the check wrongly fails a good SVG, and the skill text tells the generator to act on a named defect. Nobody else notices.

```
# before merge: close the PR without merging
gh pr close 1161
# after merge: revert the merge commit on main
git revert -m 1 <merge-commit-sha> && git push origin main
```

## Release log

1. `python3 launch_demo.py config` → `SHIP`, `launch-demo: 0 problem(s)`. Loaded the launch-demo skill; `probe` → `READY`; `render svg-mechanical-check` → `PRODUCED` (launch.mp4, 30.8s, h264 + aac), 0 problems. Committed as `docs(svg-mechanical-check): launch brief — copy, storyboard and narrated demo`.
2. `git fetch origin`; `git merge-tree --write-tree HEAD origin/main` → exit 0, clean.
3. Battery on HEAD: `python3 run_tests.py -j 3` → `tests: 4027 tests across 127 modules in 43.3s on 3 workers, 0 problem(s)`; `python3 lint.py` → `lint: 0 problem(s) across 35 skills`; `python3 kb.py drift` → `drift: 0 problem(s)`; `python3 gates.py` → `gates: 0 problem(s)`; `python3 gates.py --selftest` → `selftest: ok`; `python3 factory_init.py update-manifest` → `factory-init: 0 problem(s)`, tree clean after.
4. `git push -u origin feat/svg-mechanical-check` → new branch pushed.
5. `gh issue create --label type:feature` → https://github.com/mattbutlerengineering/skills/issues/1160
6. PR body checked with `gates.pr_body_problems` → `[]`; `gh pr create` → https://github.com/mattbutlerengineering/skills/pull/1161

## Post-release checks

- Not applicable until merge: nothing has reached users. The check itself ran from this branch: `python3 -I svg_check.py tests/fixtures/svg-check/all-four.svg` exited 1 naming all four defects; `.../clean.svg` exited 0 with `pass — smallest text 8.3px at 830px embed width`.
- Fix runs: not a fix run.
- Not run, by the brief's no-spend rule: `claude plugin eval`, `trigger_eval.py`, `charter_replay.py`. No skill `description` changed, so no routing eval is owed.

## Outcome

Prepared and stopped — waiting on https://github.com/mattbutlerengineering/skills/pull/1161 to merge. The run stays at Ship until the merge is written back.
