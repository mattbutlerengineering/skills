---
stage: ship
run: maintenance:eval-trends-honest-output
date: 2026-10-22
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1066
assumptions:
  - "Release authorization is the brief's default, prepare and stop. This pass pushed the branch and opened one pull request. It did not merge, tag, bump the version, delete a branch, or touch .claude-plugin/plugin.json."
  - "Launch brief: `launch_demo.py config` printed the verdict SHIP. As in prior unattended runs it is left to the Owner and not produced here. The run has no user-facing surface."
  - "Rollback default: the protocol's two-way door, a revert of the squash commit. There is no data, no migration and no published version from this branch."
  - "No chore(release) PR is needed. `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/` is empty, and eval_trends.py is root-only (ADR-0115)."
  - "Review's two minors stay open by decision: the size refusal does not name where to change MAX_RECORD_BYTES, and one assertNotIn in the render test is vacuous. Future-dated records and first-day-vs-last-day without multiple-comparison correction stay as documented decisions."
  - "Post-release checks are deferred to the write-back. Nothing reaches users until the Owner merges."
---

# Release: eval-trends honest output (prepared, not merged)

Pull request: https://github.com/mattbutlerengineering/skills/pull/1066, branch `fix/eval-trends-honest-output`, base `main` (`8bf52f5`). It closes #1062. #1063 and #1061 are separate and untouched.

## Pre-flight

- [x] Verification green: `verification.md` shows each defect reproducing on main and fixed, with 7 mutants all killed.
- [x] Review: `review.md` has no open critical finding. Its one major (a crash on a non-regular file named like a record) is fixed and tested; the two minors are deferred (assumptions).
- [x] No secrets in diff: the only grep hits for secret/token/password are the word "secrets" in review.md prose. No configuration is needed in any target.
- [x] Migrations/data: none.
- [x] ADRs: the run adds none, so there is no number to check.
- [x] Version: `git diff --stat origin/main...HEAD -- skills/ .claude-plugin/ factory/` prints nothing (ADR-0095).
- [x] Rollback plan concrete (below).

### Pairwise hazard (`docs/kb/cross-pr-merge-hazards.md`)

```
$ git fetch origin
$ git rev-parse origin/main; git merge-base HEAD origin/main
8bf52f5288fbf04a5b65c94469ad31f56ee29814
8bf52f5288fbf04a5b65c94469ad31f56ee29814
$ git merge-tree --write-tree origin/main HEAD
c891970e1f7b1db39d6c69bcb9d6d1814f3679e8        (clean)
$ gh pr list --state open --json number,title
[]
```

origin/main has not moved past the merge base and no other PR was open, so there was no pair to simulate. The checks ran on HEAD `3c8fe96`.

```
tests: 3784 tests across 118 modules in 26.3s on 8 workers, 0 problem(s)
lint: 0 problem(s) across 34 skills
drift: 0 problem(s)
gates: 0 problem(s)
selftest: ok
```

## Rollback plan

Door: two-way. Reverting one squash commit restores the old output. Nothing is migrated, published or renamed.

Blast radius: `eval_trends.py`, two test files and one architecture line. Only someone reading the tool's output notices a wrong call.

```
# before merge: close the pull request; nothing reached main
gh pr close 1066

# after merge, if the change must come out:
git checkout main && git pull
git revert --no-edit <squash sha>
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push   # via a PR
```

## Release log

1. `git fetch origin`; origin/main equals the merge base `8bf52f5`; `git merge-tree --write-tree origin/main HEAD` clean; no open PRs (above).
2. Whole-repo checks on HEAD, all green (above).
3. `python3 launch_demo.py config` (rc=0) printed, verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   It printed no reason line. The brief was not produced in this unattended pass and is left to the Owner.
4. `gates.pr_body_problems` on the body printed `[]`.
5. `git push -u origin fix/eval-trends-honest-output` -> new branch.
6. `gh pr create --base main --body-file <tmp>` -> https://github.com/mattbutlerengineering/skills/pull/1066. The body has a `No work order:` line, `Closes #1062` and a Merge danger section.

## Post-release checks

Nothing has reached users, because the pull request is open and unmerged. The write-back runs these once it merges:

- `gh pr view 1066 --json state,mergedAt` -> merged, with its date.
- On main at the squash commit: `python3 run_tests.py`, `python3 gates.py && python3 gates.py --selftest`.
- Issue #1062 is closed by the merge.
- Fix runs: the producing boundary is the record reader, and its consumers (the render path and the trend line) were inspected in review. The remaining cleanup is the two deferred minors, left open by decision.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names. The Owner merges it (squash). No version bump or release PR is needed, since this branch changes no payload. Run `next` or `ship` afterwards to write the merge back.
