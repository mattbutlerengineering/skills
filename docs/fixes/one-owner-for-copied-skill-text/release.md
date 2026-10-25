---
stage: ship
run: maintenance:one-owner-for-copied-skill-text
date: 2026-10-25
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1108
---

# Release: one owner each for three copied skill passages

## Pre-flight

- [x] Verification green: 6 PASS, 0 FAIL, 1 NOT RUN (live agent behaviour
      reading the moved text) in verification.md, on HEAD `760aa88`.
      Checks there:
      - `tests: 3912 tests across 123 modules in 33.2s on 8 workers, 0 problem(s)`
      - `lint: 0 problem(s) across 35 skills`
      - `drift: 0 problem(s)`
      - `gates: 0 problem(s)`
      - `selftest: ok`
- [x] Review: no critical, no major. Four minors deferred with reasons.
- [x] No secrets in diff: skill prose, references, one read-only test and
      run docs.
- [x] No migrations or data changes, and no ADR added.
- [x] Base: `git merge-tree --write-tree HEAD origin/main` -> exit 0,
      clean. Wave siblings A (#1106) and B are open, and their chain merge
      is simulated before any merge.
- [x] Protected paths: `.claude-plugin/plugin.json` untouched (ADR-0095).
      Nothing under `factory/templates/` or in `factory_init.MIRRORS`
      changed. `skills/` changed, so the wave's release PR bumps the
      version.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert restores the inline copies.

Blast radius: audit, automate and interactive-architecture-diagram users,
after the wave's release bump. A sibling reference works only when the
plugin installs whole, which it always does today. If the call is wrong,
an agent skips a cited reference and misses the in-flight check or a
palette value.

(The same call the PR body makes under `## Merge danger`.)

```
# Before merge
gh pr close 1108

# After merge
git checkout -b revert/one-owner-for-copied-skill-text origin/main
git revert <merge sha of PR 1108>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/one-owner-for-copied-skill-text
gh pr create --base main --body-file <body>   # "No work order:" + "Closes #N"
```

## Release log

1. Soft gate: review.md, no critical finding -> pass.
2. `python3 launch_demo.py config` -> `SHIP` / `launch-demo: 0 problem(s)`.
   Not run: a text-ownership refactor has nothing on screen to record.
   This follows the Owner's in-session answer for this wave's first
   release ("Skip, log the verdict").
3. `gh issue create --label type:chore` -> #1107 (the PR closes it).
4. `gates.pr_body_problems(body)` -> `[]`.
5. `git push -u origin fix/one-owner-for-copied-skill-text` -> new branch.
6. `gh pr create --base main` ->
   https://github.com/mattbutlerengineering/skills/pull/1108

## Post-release checks

- Nothing is released until the PR merges and the wave's release PR bumps
  the version.
- First live observation: the next `audit` and `automate` runs show recon
  and in-flight output, read from `../audit/references/recon.md`.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names.
