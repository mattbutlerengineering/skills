---
stage: ship
run: maintenance:a-rename-the-merge-train-may-not-see
date: 2026-11-03
outcome: released
released-at: 2026-11-04
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1150
assumptions:
  - "Release authorization was prepare-and-stop (autorun-brief.md). The branch was pushed and PR #1150 opened; the Owner then answered 'Merge now' in session (2026-11-04) and the PR was squash-merged. Nothing is tagged or version-bumped."
  - "No launch brief, by Owner decision (autorun-brief.md, 'User-facing surface'), whatever `launch_demo.py config` prints. The command was not run and launch-demo was not loaded."
  - "Ship for a scoped maintenance fix is a single branch merge per the protocol's Run scale section, not a tagged release. `.claude-plugin/plugin.json` is untouched (ADR-0095); the wave's chore(release) bump carries this skill change to consumers."
  - "No ADR was added, so the ADR-number pre-flight item does not apply (review.md, ADR judgement: the protocol's three-leg test fails on the first leg)."
---

# Release: the merge train reads rename sources and non-ASCII gate paths

## What shipped, and how far

Released 2026-11-04. Branch `fix/a-rename-the-merge-train-may-not-see`
was pushed and **PR #1150** opened against `main` with `Closes #1149`, a
`No work order:` line and a `## Merge danger` section. Base was
`origin/main` `397a987`; HEAD at the time of the PR was `068e243`. The
PR was squash-merged as `038dc0f` (see Write-back).

## Write-back, 2026-11-04

```
$ gh pr view 1150 --json state,mergedAt,mergeCommit
{"mergeCommit":{"oid":"038dc0f81ffc6dbb7928d2b96afb9f0e218e9c61"},"mergedAt":"2026-11-04T19:54:21Z","state":"MERGED"}
$ gh issue view 1149 --json state,closedAt
{"closedAt":"2026-11-04T19:54:23Z","state":"CLOSED"}
```

- Squash commit `038dc0f81ffc6dbb7928d2b96afb9f0e218e9c61`, merged
  2026-11-04T19:54:21Z.
- The merge was made by the orchestrator on the Owner's explicit
  in-session answer ("Merge now", 2026-11-04). The PR touches a gate path,
  so it needed that human decision.
- #1149 closed at 2026-11-04T19:54:23Z.
- Outstanding: the `chore(release)` version bump (ADR-0095), now covering
  three merged fixes. Not done by this run.

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

1. ~~Review and merge PR #1150.~~ Done 2026-11-04, see Write-back.
2. The `chore(release)` bump, per ADR-0095, is outstanding. It now covers
   three merged fixes, this one among them. This run does not touch
   `plugin.json`.
3. ~~Write-back.~~ Done 2026-11-04, see Write-back.

## Release log

1. `git push -u origin fix/a-rename-the-merge-train-may-not-see` → new branch pushed.
2. `gh pr create --base main --head fix/a-rename-the-merge-train-may-not-see ...` → `https://github.com/mattbutlerengineering/skills/pull/1150`.
3. Launch brief → skipped (Owner decision); nothing written.

## Post-release checks

Nothing is deployed by this merge itself: the change reaches consumers
only with the outstanding `chore(release)` bump. The checks below were
written before the merge and still describe what to watch.

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

Released. PR #1150 merged 2026-11-04T19:54:21Z; #1149 closed. The
`chore(release)` bump (ADR-0095) is outstanding. The pre-merge run had no
hiccups: the suite ran green first time under load average 11.
