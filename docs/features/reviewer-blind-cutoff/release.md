---
stage: ship
run: feature:reviewer-blind-cutoff
date: 2026-11-04
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1159
assumptions:
  - "Interview answers came from autorun-brief.md; its Release authorization is None, so Ship prepared and stopped: pushed the branch, opened the pull request, no merge, tag, version bump or branch deletion."
  - "Tracker: the brief seeds no issue, so Ship filed one plain issue, #1158 (label type:feature, title from the PRD), and the PR body carries `Closes #1158` and a `No work order:` line, as the brief's Tracker section directs."
  - "Verification ran with `python3 run_tests.py -j 3` because five parallel runs share the machine; -j only sets worker count."
  - "ADR-0123 is provisional (unattended run); its number is free on origin/main and may renumber if a sibling run's ADR merges first."
---

# Release: Withhold the pass cutoff from the implement-queue reviewer

## Pre-flight

- [x] Verification green (no unresolved failures): `verification.md` has 14 of 15 criteria PASS, 0 FAIL; criterion 4's fail-first ordering is UNKNOWN (record gap, not a defect). Review: no critical finding; the one major was fixed.
- [x] No secrets in diff; target config present: a pattern scan of the added lines (`ghp_`, `sk-…`, `api_key=`, private-key headers) matched nothing. No configuration is required; this repo's `.claude/implement-queue.md` ships the `verdict` hook in the same change.
- [x] Migrations/data changes have a tested forward path: none; no migration or data change.
- [x] ADR numbered and indexed: ADR-0123 (provisional) is absent from `origin/main` (`git ls-tree origin/main docs/adr/ | grep -c 0123-` → 0) and has a row at `docs/adr/README.md:146`.
- [x] Rollback plan concrete (below)
- [x] Merge conflicts: `git fetch origin` then `git merge-tree --write-tree HEAD origin/main` → tree `002b575edead92deb2b6f50ff6f21b31df3acac1`, exit 0, no conflict.

## Rollback plan

Door: two-way — a revert restores the old contract and verdict path; no data, published version or public interface moves.

Blast radius: the implement-queue reviewer's verdict path, which `factory-merge-train` and `factory-hourly-improvement` merge on; a consumer repo with `merge: auto` and no `verdict` hook stops merging (fails closed, named in ADR-0123).

```
git revert -m 1 <merge commit of PR #1159>   # or: git revert <range> if squash-merged
python3 factory_init.py update-manifest       # only if the revert touches mirrored files
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py
```

## Release log

1. `python3 launch_demo.py config` → `SHIP`, `launch-demo: 0 problem(s)` (no reason lines printed). Loaded the `launch-demo` skill; `probe` → `READY`; wrote `docs/launches/reviewer-blind-cutoff/{launch.md,storyboard.json}`; `render reviewer-blind-cutoff` → `PRODUCED`, `launch.mp4` 37.5 s h264 + aac, 0 problems. Committed as `1e87279`.
2. `git fetch origin`; `git merge-tree --write-tree HEAD origin/main` → clean (exit 0).
3. Battery on HEAD: `python3 run_tests.py -j 3` → `tests: 3999 tests across 127 modules in 58.5s on 3 workers, 0 problem(s)`; `python3 lint.py` → `lint: 0 problem(s) across 35 skills`; `python3 kb.py drift` → `drift: 0 problem(s)`; `python3 gates.py` → `gates: 0 problem(s)`; `python3 gates.py --selftest` → `selftest: ok`.
4. `git push -u origin feat/reviewer-blind-cutoff` → new branch pushed.
5. `gh issue create --label type:feature` → https://github.com/mattbutlerengineering/skills/issues/1158
6. `gates.pr_body_problems(body)` → `[]`; `gh pr create --base main` → https://github.com/mattbutlerengineering/skills/pull/1159

## Post-release checks

- Not applicable until the pull request merges: nothing is deployed. Run once, locally: `python3 reviewer_verdict.py 7` → `reviewer-verdict: pass (score 7/10)`; `6` → `flag (score 6/10)`; `abc` → `error (score is not a number ('abc'))`.
- Not checked: a live implement-queue run with the new hook, and whether the reviewer anchors to the line (unmeasured by design). No paid run was made.
- Fix runs: not a fix run.

## Outcome

Prepared and stopped — waiting on pull request #1159 (https://github.com/mattbutlerengineering/skills/pull/1159) to merge. No merge, tag, version bump or branch deletion; `.claude-plugin/plugin.json` untouched.
