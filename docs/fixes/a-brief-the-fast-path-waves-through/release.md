---
stage: ship
run: maintenance:a-brief-the-fast-path-waves-through
date: 2026-11-03
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1147
assumptions: ["the brief's Release authorization is prepare and stop (Owner decision 3), so Ship pushes, opens the pull request and stops; no merge, tag or version bump", "launch brief: the brief is silent and `launch_demo.py config` printed SHIP, so the ship skill's default applied: the launch-demo skill ran for this run and its output is committed on the branch, even though the run has no user-facing surface"]
---

# Release: the fast path gates every autorun brief

**Prepared, not merged.** PR #1147 is open against main and waits for a
human merge. Nothing merged, tagged, published or version-bumped.

## Readiness

`review.md` (3572f15): no critical, no open major; two minors deferred
with reasons. `verification.md`: 11 of 11 criteria PASS. The branch is
`fix/a-brief-the-fast-path-waves-through`, based on origin/main
`57db41b` (main had not moved at pre-flight; no other open PR).

## Pre-flight

- [x] Verification green: 11 PASS, 0 FAIL, 0 NOT RUN.
- [x] No secrets in the diff; no configuration added, no network call,
  no migration or data change. The diff is `fast_path.py` (one tuple
  entry and comments), tests, the queue profile, ADR text, backlog and
  run artifacts.
- [x] ADR-0122 has a free number on the base branch (origin/main's
  highest is ADR-0121) and a row in `docs/adr/README.md`; ADR-0121's
  status line points at it.
- [x] `.claude-plugin/plugin.json` untouched:
  `git diff origin/main...HEAD -- .claude-plugin/plugin.json` printed
  nothing.
- [x] Rollback plan concrete (below).

Re-run from the worktree at `3572f15`:

```
$ python3 run_tests.py -j 4
tests: 3978 tests across 126 modules in 34.3s on 4 workers, 0 problem(s)
 14:37:17  up 19 days 17:38,  4 users,  load average: 5.81, 10.79, 14.23
$ python3 lint.py
lint: 0 problem(s) across 35 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

Routing check: `python3 fast_path.py origin/main HEAD` →
`fast-path: review (.claude/implement-queue.md)`, exit 1. The diff also
touches `fast_path.py` and `docs/adr/**`, each of which classifies
`review` on its own, and the run's own `autorun-brief.md` now does too.
So the merge train holds this PR for a human merge.

## Rollback plan

Door: two-way — a revert removes the brief from the gate list; no data,
version or published interface changes, and neither `fast_path.py` nor
`implement-queue.md` is in `factory_init.MIRRORS`, so no manifest
regeneration is needed on the way back.

Blast radius: the repo's own merge train and its reviewers only. If the
gate is wrong, a brief-only PR needs a human merge it did not need
before, or (on revert) loses one.

```
# before merge
git push origin --delete fix/a-brief-the-fast-path-waves-through   # and close PR #1147
# after merge
git revert <squash-merge-sha>      # restores fast_path.py, the profile, ADR-0121's status line, the backlog line
```

Reverting leaves ADR-0122 out of the tree with the code; the revert
removes the ADR file and README row in the same commit.

## Release log

1. `python3 run_tests.py -j 4`, `lint.py`, `kb.py drift`, `gates.py`,
   `gates.py --selftest` → all clean (above). The suite ran at load
   average 5.8 and needed no re-run; the earlier wall-clock failures in
   `defect.md` Notes did not recur.
2. `python3 fast_path.py origin/main HEAD` → `review`, exit 1 (above).
3. PR body written outside the repo; `gates.pr_body_problems` → `[]`.
4. `git push -u origin fix/a-brief-the-fast-path-waves-through` → new
   branch on origin.
5. `gh pr create --base main --head fix/a-brief-the-fast-path-waves-through`
   (first command of its own call, body file from an earlier call) →
   `https://github.com/mattbutlerengineering/skills/pull/1147`.
6. Launch brief: `python3 launch_demo.py config` →
   `SHIP` / `launch-demo: 0 problem(s)`; `probe` → `READY`. Ran the
   `launch-demo` skill for this run: `render
   a-brief-the-fast-path-waves-through` → `wrote
   docs/launches/a-brief-the-fast-path-waves-through/demo.tape`, `wrote
   .../launch.mp4`, `duration=27.733333`, `PRODUCED`,
   `launch-demo: 0 problem(s)`. Committed on the branch as `1013dc4`
   (`launch.md`, `storyboard.json`, `demo.tape`, `launch.mp4`, 300 KB).
   The commit landed after the PR was opened, so it is part of PR #1147
   by the push below.
7. Launch brief dropped on the Owner's decision (2026-11-03, "Revert
   video, then merge"): `1013dc4` reverted on the branch as `8808499`,
   removing `docs/launches/a-brief-the-fast-path-waves-through/`. The
   fix has no user-facing surface, so no launch brief ships with it.

## Post-release checks

None yet; nothing is released. After the merge, confirm on main that
`python3 fast_path.py` on a brief-only diff prints
`fast-path: review (<path>)`.
- Fix runs: producing boundary `fast_path.is_gate_path` and its
  consumers (`classify`, `gate_globs`, the profile pin test) inspected in
  Review. Related cleanup remaining: the implement-queue skill's
  GitHub-side `gate_paths` matcher (backlog line 144's seed), which
  ADR-0122 names as out of reach.

## Release steps for the Owner

1. Review and merge PR #1147 by hand (the train will not merge it).
   It carries `Closes #1146`, so the merge closes the issue; if it does
   not, close #1146 with a comment naming
   `docs/fixes/a-brief-the-fast-path-waves-through/`.
2. The wave's `chore(release)` version bump follows per ADR-0095. It is
   not on this branch, and this run did not touch
   `.claude-plugin/plugin.json`.
3. Write-back: next touch of the run (`next` or `ship`) reads
   `gh pr view 1147 --json state,mergedAt` and, on merge, rewrites
   `outcome: released`, adds `released-at:` and commits. Operate's
   `minimum-signal` is exactly this write-back.

## Flagged

- A PR that edits only an `autorun-brief.md` now needs a human merge (the
  intended cost).
- ADR-0122 is provisional.
- Deferred minors from review: the root-level glob dialect for
  `**/autorun-brief.md` (inert today; the GitHub-side matcher seed owns
  it) and the case-sensitive basename match (same as `prd.md` and
  `architecture.md`).
- The suite's wall-clock tests failed once each in three loaded runs
  during Implement (`defect.md` Notes); clean at load 12.6 in Verify and
  at 5.8 here.
- The launch brief (`1013dc4`, with a 300 KB `launch.mp4`) was added
  because the repo's config says SHIP. The Owner dropped it before merge,
  and it was reverted as `8808499` (Release log entry 7).

## Outcome

Prepared and stopped — waiting on PR #1147 (`pending-merge:`).
