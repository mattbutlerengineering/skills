---
stage: ship
run: feature:fail-closed-roll-up
date: 2026-10-17
outcome: released
released-at: 2026-10-17
pending-merge: https://github.com/mattbutlerengineering/skills/pull/998
assumptions:
  - "Release authorization is prepare-and-stop (Owner decision 4 in autorun-brief.md): the branch is pushed, one type:feature issue (#997) and one PR (#998) are open; no merge, tag, plugin.json bump, branch deletion or release PR."
  - "Recommended default taken (soft gate): review.md's re-review verdict (0 critical, 0 major, 7 minor, 'Ready for Ship') is the predecessor state; the 7 minors ship deferred and are listed in the PR body and the Outcome below."
  - "Recommended default taken (launch brief): launch_demo.py config printed SHIP, but the orchestrator's stage instruction limits this stage to committing release.md, so the launch-demo skill was not run. The verdict is logged verbatim and the launch brief is flagged for the Owner; the release proceeds, as the hook never blocks a release."
  - "Recommended default taken (post-release): with outcome prepared nothing reached users yet, so the post-release check is the PR's CI on the pushed head; the installed-plugin smoke check belongs to the write-back after merge and the chore(release) PR."
---

# Release: fail-closed roll-up (detector H Summary half, ADR-0107)

## Pre-flight

- [x] Verification green: `verification.md` reads 17 PASS, 0 FAIL, 0
  NOT RUN; review.md's re-review verdict: "Ready for Ship ... 0
  critical, 0 major, 7 minor". Re-run on HEAD `a677f51`:
  ```
  $ python3 run_tests.py 2>&1 | tail -1
  tests: 3308 tests across 106 modules in 18.7s on 8 workers, 0 problem(s)
  $ python3 lint.py | tail -1
  lint: 0 problem(s) across 34 skills
  $ python3 kb.py drift | tail -1
  drift: 0 problem(s)
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- [x] No secrets in diff (`git diff origin/main...HEAD | grep -iE
  "(api[_-]?key|secret|token|password)\s*[:=]"` printed nothing); no
  target configuration needed (docs, templates and a stdlib gate rule).
- [x] Migrations/data changes: none. No shipped artifact is rewritten;
  shipped `verification.md` files dated before 2026-10-17 are
  grandfathered, and the real tree reports `gates: 0 problem(s)`.
- [x] ADR number: ADR-0107 is free on origin/main (`git ls-tree` over
  `docs/adr` at `1290a4e` lists 0105 and 0106 as the highest) and in
  both open PRs (#993 touches only
  `docs/features/pr-body-preflight/release.md`; #996 only
  `docs/kb/gates-scan-every-doc.md`). Its row is in
  `docs/adr/README.md` (status provisional).
- [x] Pairwise hazard (`docs/kb/cross-pr-merge-hazards.md`):
  `git merge-tree --write-tree origin/main HEAD` exited 0 (tree
  `18baaded`); the branch's merge base is origin/main `1290a4e`, with no
  commits on main ahead of it. Chain-simulated with each open PR
  (merge-tree, commit-tree, detached worktree in the session
  scratchpad):
  ```
  == PR 993
  merge-tree rc=0 tree=293edab6393cb6eb369e8e3b8c3231f1a1978c9f
  gates: 0 problem(s)
  drift: 0 problem(s)
  == PR 996
  merge-tree rc=0 tree=596215004edf91edc61c24b54afd4e6ee37087ed
  gates: 0 problem(s)
  drift: 0 problem(s)
  ```
  Both clean. #996's page describes detectors C and I only, not H, so
  this branch does not make it stale. Both worktrees and temp refs were
  removed afterwards.
- [x] Version: `git diff origin/main...HEAD -- .claude-plugin/plugin.json`
  is empty (ADR-0095 rule 1). Skills and the payload changed, so a
  `chore(release)` PR is owed after merge; it is the Owner's.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way — a revert removes the rule, the docs and the templates;
no data, published interface or version moves in this PR.

Blast radius: every stamped repo on its next factory update (gates.py
is mirrored into the payload): a post-cutoff or undated
`verification.md` whose Summary reads as a full pass over a disclosed
NOT RUN criterion now fails `gates.py`. Shipped artifacts with a plain
ISO date before 2026-10-17 are untouched.

(the same call the PR body makes under the protocol's Pull request body
section)

```
# before merge: close the PR, leave the branch
gh pr close 998 --comment "Abandoned: <reason>"

# after merge (squash): revert the squash commit on a branch and PR it
git fetch origin main && git switch -c revert/fail-closed-roll-up origin/main
git revert --no-edit <squash sha of #998>
python3 factory_init.py update-manifest   # payload gates.py reverts with the root
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/fail-closed-roll-up
gh pr create --base main --title "revert: fail-closed roll-up" --body-file <body with No work order: line>
# if a release PR already bumped the version, the revert ships in the next chore(release) PR
```

## Release log

1. `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
   `python3 gates.py && python3 gates.py --selftest` on `a677f51` →
   all clean (quoted under Pre-flight).
2. `git fetch origin main` → origin/main `1290a4e`;
   `git merge-tree --write-tree origin/main HEAD` → rc 0, tree
   `18baaded264871c0ba0f5f4d2935e1f2316f9157`.
3. `gh pr list --state open` → #996 (docs(kb): re-verify
   gates-scan-every-doc against gates.py) and #993 (docs(pr-body-preflight):
   ship — released by #991); neither touches `docs/adr/0107*`.
4. Chain-simulation with #993 and #996 → both clean (quoted under
   Pre-flight); worktrees removed with `git worktree remove`.
5. `python3 <plugin>/launch_demo.py config` → exit 0, output verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   The launch-demo skill was not run in this stage (see assumptions);
   the launch brief is flagged for the Owner.
6. `gh issue list --state all --search ...` → no existing issue for the
   run; `gh issue create --label type:feature` →
   https://github.com/mattbutlerengineering/skills/issues/997
7. `git push -u origin feat/fail-closed-roll-up` → `* [new branch]
   feat/fail-closed-roll-up -> feat/fail-closed-roll-up`.
8. `gh pr create --base main --head feat/fail-closed-roll-up --title
   "feat(gates): a verification Summary never rolls NOT RUN up into a
   pass" --body-file <scratchpad>/pr-body.md` (first command of its own
   Bash call; the PreToolUse `pr_body_preflight.py` hook passed it) →
   https://github.com/mattbutlerengineering/skills/pull/998
9. `gh pr checks 998 --watch --interval 15` → all green:
   ```
   check	pass	27s
   check	pass	24s
   needs-review-label	pass	6s
   review	pass	8s
   merged-label	skipping
   ```
10. Stopped here: prepare-and-stop. No merge, tag, version bump or
    branch deletion.

## Post-release checks

- PR #998's CI on the pushed head `a677f51` → `check` pass (both
  workflow runs), `needs-review-label` pass, `review` pass; detector B
  accepted the body's `No work order:` and `Closes #997` lines.
- Nothing reached users yet (outcome prepared). After merge and the
  `chore(release)` PR, the write-back confirms an installed plugin
  carries the new `gates.py` (the payload copy is byte-identical to the
  root and its manifest entry matches, per review.md).

## Release steps for the Owner

1. Review and merge #998 (squash). `Closes #997` closes the issue.
2. Cut the ADR-0095 `chore(release)` PR bumping
   `.claude-plugin/plugin.json` (skills and the payload changed), after
   the wave lands.
3. Write back per the protocol's "The Ship outcome":
   `gh pr view 998 --json state,mergedAt` (or
   `gh api repos/mattbutlerengineering/skills/pulls/998 --jq
   '{merged,merged_at}'` in a cloud session); when merged, rewrite
   `outcome: released`, add `released-at:` (the merge date), keep
   `pending-merge:`, and commit this file as
   `docs(fail-closed-roll-up): ship — ...`. Closed unmerged: leave
   `prepared`.

## Outcome

Released. The Owner answered "Merge now" in the autorun session on
2026-10-17, and #998 was squash-merged as `461803a` at
2026-10-17T15:59:17Z (`gh pr view 998 --json state,mergeCommit,mergedAt`
→ `MERGED`). #997 closed with it. The operate minimum-signal, the
`chore(release)` PR and the launch brief are still open. The flags
below were raised when the release was prepared, and they still stand:

- **ADR-0107 is provisional** (written unattended); accept or amend it.
- **7 deferred minors** (review.md, re-review verdict): invisible and
  incidental words satisfy the rule; heading variants other than a
  rename escape it; the disclosure heads are stated twice in
  `gates.py`; no test pins that a Summary's own labelled disclosure is
  not a trigger; the fix loop widened what incidental prose satisfies
  (`n't run` behaviour descriptions, hyphenated compounds); "couldn't
  be run" and "1 not-applicable" still false-positive; the
  trailing-comment `date:` behaviour is unpinned.
- **Launch brief**: `launch_demo.py config` said `SHIP`; the brief was
  not produced in this stage. Run the `launch-demo` skill for this run
  if wanted.
- **Version bump**: the ADR-0095 `chore(release)` PR after merge.
- **Operate minimum-signal** (autorun-brief.md): the first
  `verification.md` written after #998 merges that the new H rule
  judges (it passes or it is refused), counted from the repo, never
  from the brief.
