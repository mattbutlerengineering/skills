---
stage: ship
run: maintenance:idea-reseed-duplicates
date: 2026-10-25
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1119
---

# Release: a re-run of Idea seeds nothing twice

## Pre-flight

- [x] Verification green: 2 PASS, 0 FAIL, 1 NOT RUN (criterion 3, a live
      re-run). The review fix `c4f477b` landed after it; the checks
      re-ran there, all 0 problems.
- [x] Review: no critical finding; one major fixed, one minor deferred.
- [x] No secrets in the diff (skill prose, one test, two eval records,
      run docs). No target configuration needed.
- [x] No migrations or data changes.
- [x] No ADR added.
- [x] Protected paths: `.claude-plugin/plugin.json` untouched (ADR-0095).
      `skills/` changed, so a release PR bumps the version.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert removes one sentence of skill prose and the
eval records. Nothing migrates.

Blast radius: Idea runs in repos on the next plugin version. If the call is
wrong, a re-run skips a seed it should have written. That is advisory
noise in the backlog, not state.

```
git checkout -b revert/idea-reseed-duplicates origin/main
git revert <merge sha of the PR>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/idea-reseed-duplicates
gh pr create --base main --body-file <body>   # "No work order:" + "Closes #N"
```

## Release log

1. Soft gate: review.md Verdict, "No critical finding" -> pass.
2. Launch demo: not run. A seed-dedupe sentence has nothing on screen
   (the Owner's standing answer this session, "Skip, log the verdict").
3. The same branch carries #1064's first paid eval runs, which the Owner
   authorized in session ($15 cap each).
   - The first attempt, against the working checkout, was refused before
     any model call ($0.00) because the plugin directory held more than
     20,000 entries: 122 stale agent worktrees under `.claude/worktrees/`.
   - The runs then went against a `git archive` export of main with
     `--trust-plugin`:
     - `idea`: with 0.90, without 0.30, delta +0.60, $1.86.
     - `decompose`: with 0.94, without 0.67, delta +0.28, $1.43.
   - The two `aggregate-result.json` files are copied unedited to
     `plugin-evals/records/2026-10-26.json` and `-2.json` (UTC start
     date).
4. The idea suite's one with-plugin miss, `keeps-users-words` (3 of 3),
   got a candidate skill rule (`ef2b107`). A single-arm re-run ($1.37)
   still failed 3 of 3, so the rule was reverted (`5f73cbc`) and filed
   as #1118. That re-run tested a variant that does not ship, so its
   record is not committed. Total spend: $4.66.

## Post-release checks

- Nothing is released until the PR merges and a release PR bumps the
  version.
- First live observation: an Idea re-run on a seeded run appends no
  duplicate.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names.
