---
stage: ship
run: maintenance:a-rename-the-merge-train-may-not-see
date: 2026-11-03
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1150
assumptions:
  - "Release authorization is prepare-and-stop (autorun-brief.md). The branch is pushed and PR #1150 is open; nothing is merged, tagged or version-bumped."
  - "No launch brief, by Owner decision (autorun-brief.md, 'User-facing surface'), whatever `launch_demo.py config` prints. The command was not run and launch-demo was not loaded."
  - "Ship for a scoped maintenance fix is a single branch merge per the protocol's Run scale section, not a tagged release. `.claude-plugin/plugin.json` is untouched (ADR-0095); the wave's chore(release) bump carries this skill change to consumers."
  - "No ADR was added, so the ADR-number pre-flight item does not apply (review.md, ADR judgement: the protocol's three-leg test fails on the first leg)."
---

# Release: the merge train reads rename sources and non-ASCII gate paths

## What shipped, and how far

Prepared, not released. Branch `fix/a-rename-the-merge-train-may-not-see`
pushed; **PR #1150** is open against `main` with `Closes #1149`, a
`No work order:` line and a `## Merge danger` section. Base is
`origin/main` `397a987`; HEAD at the time of the PR was `068e243`. The
merge is the Owner's.

## Pre-flight

Re-run at `068e243` (`uptime`: load average 11.24, 7.46, 5.64; no
wall-clock failure occurred):

```
$ python3 run_tests.py
tests: 3989 tests across 126 modules in 29.6s on 8 workers, 0 problem(s)
$ python3 lint.py
lint: 0 problem(s) across 35 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

- [x] Verification green: `verification.md`, 16 PASS, 0 FAIL, one FINDING resolved by review as no violation, three unknowns carried (below).
- [x] Review: `review.md` verdict "Ready for Ship"; no critical, no open major.
- [x] No secrets in diff: a grep of `git diff origin/main...HEAD` for added key/secret/token/password assignment forms printed nothing.
- [x] Target configuration: none required. The change is skill text, a profile hook and a stdlib mode.
- [x] Migrations/data: none.
- [x] ADRs: none added; none edited.
- [x] `git diff origin/main...HEAD -- .claude-plugin/plugin.json` is empty (0 bytes).
- [x] `python3 fast_path.py origin/main HEAD` → `fast-path: review (.claude/implement-queue.md)`, exit 1: routed to review.
- [x] `python3 fast_path.py gate origin/main HEAD` → `gate-paths: human (docs/factory/merge-train-routine.md)`, exit 1. The PR touches a gate path (`docs/factory/**`), so it needs a human merge by the train's own rule.
- [x] PR body: `gates.pr_body_problems(body)` returned `[]`.
- [x] Rollback plan below.
- Launch brief: skipped by Owner decision, see assumptions.

## CI on #1150

Observed after the push (`gh pr checks 1150`, 45 s after opening):

```
review            skipping
check             pass   25s
needs-review-label pass   6s
review            pass   7s
merged-label      skipping
check             pass   32s
merged-label      skipping
needs-review-label skipping
```

`OPEN MERGEABLE CLEAN`. The skipping jobs are those that run only on
other events, not failures.

## Rollback plan

Door: two-way. Skill text, a profile hook, one stdlib mode and its tests;
a revert of the merge commit undoes all of it, with no migration, no data
and no published version. (The PR body's `## Merge danger` makes the same
call.)

Blast radius: every repo that runs the implement-queue train, once the
wave's version bump ships this skill. A wrong source or count check fails
closed to a human merge, so the visible symptom is held PRs, never a
silent merge. Nobody notices before that bump.

```
# before merge: close PR #1150 unmerged; nothing has moved
gh pr close 1150
# after merge: revert the merge commit on main (take its SHA from the PR)
git revert -m 1 <merge-sha>
python3 run_tests.py && python3 gates.py
```

No external state to unwind: no deploy, no published package, no tag, no
issue edits (#1149 closes only when the PR merges).

## Owner's release steps

1. Review and merge PR #1150. It touches a gate path
   (`docs/factory/merge-train-routine.md`), so it is a human merge by the
   train's own rule.
2. The wave's `chore(release)` bump, per ADR-0095, which this skill
   change is payload for. This run does not touch `plugin.json`.
3. Write-back: the next pass at Ship reads the PR
   (`gh pr view 1150 --json state,mergedAt`), rewrites `outcome: released`,
   adds `released-at:`, keeps `pending-merge:`, and commits. Operate's
   minimum signal is "Ship written back as released".

## Release log

1. `git push -u origin fix/a-rename-the-merge-train-may-not-see` → new branch pushed.
2. `gh pr create --base main --head fix/a-rename-the-merge-train-may-not-see ...` → `https://github.com/mattbutlerengineering/skills/pull/1150`.
3. Launch brief → skipped (Owner decision); nothing written.

## Post-release checks

Not applicable yet: nothing is deployed and the change is not merged.

- Fix run, producing boundary and consumers: the producing boundary
  `changed_paths` (`fast_path.py`) has two callers, the classifier and
  `gate`, both inspected in review. Consumers of the skill text are the
  profile `.claude/implement-queue.md` and the routine doc, both updated
  and pinned by a doc test.
- Related cleanup remaining: backlog line 154 (glob dialect and case
  sensitivity) and line 146 (journal audit) stay out of scope, per the brief.

## Flagged items

- **Open minor, wording** (`review.md`): the count check does not say
  entries versus unique paths; a renaming PR can be spuriously held for a
  human. Fails closed. Recommended one-clause fix at the next touch of the
  skill row and the profile.
- **Deferred minor:** a list of exactly 3000 entries is not named to fail
  closed.
- **Unknowns, not passes:** the GitHub MCP file-list tool's rename
  behavior; the 3000-file case (largest PR tried: 129 files); whether
  `changed_files` is itself capped (docs silent); a live train run
  following the new text; a path with a backslash or control character
  through `gate` (not run).
- **Consumer-visible default:** the `changed-files` default moved from
  `none` to the REST command with a count check, by the Owner's "Ship REST
  default". A consumer's train now reads it.

## Outcome

Prepared and stopped, waiting on PR #1150 (`pending-merge:`). No hiccups:
the suite ran green first time under load average 11.
