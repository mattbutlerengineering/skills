---
stage: ship
run: maintenance:a-long-line-stalls-the-gate
date: 2026-10-24
outcome: released
released-at: 2026-10-25
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1079
assumptions:
  - "Verify was not re-run after Review's fix. verification.md measured the 17-wide window at `20ccc5d`. Review widened it to 64 in `dc1570f` and re-ran the four checks, the whole-tree sweep and the timing itself (review.md, Final checks). Ship re-ran the four checks on `4137538` and compared the two gates.py copies with `cmp` (quoted below). That stands in for a Verify pass at 64. verification.md is not rewritten."
  - "Launch brief: `launch_demo.py config` printed the verdict SHIP. As in prior unattended runs, the brief is left to the Owner and not produced here. The run has no user-facing surface (brief: User-facing surface: none)."
  - "Rollback default: the protocol's two-way door, undone by `git revert` of the squash commit plus a manifest regen. There is no data, no migration and no published version from this branch."
  - "Pairwise hazard: each of the three open PRs (#1073, #1074, #1077) shares no file with this branch, and `git merge-tree` is clean for all three. With disjoint file sets, Ship did not chain-simulate the four checks on each pairing. origin/main `ec8159f` is an ancestor of HEAD."
  - "Issue label: type:defect, the fitting label in factory/templates/.github/labels.json (feature, defect, chore, support, sweep). The taxonomy has no perf type, and the brief files this under Defect."
  - "Post-release checks are deferred to the write-back. Under prepare-and-stop nothing reaches users until the Owner merges and cuts the ADR-0095 release PR."
---

# Release: a long line stalls the gate (prepared, not merged)

Release authorization: **none, so prepare and stop** (autorun brief).
This pass pushed the branch, filed one `type:defect` issue, and opened
one pull request. It did not merge, tag, bump
`.claude-plugin/plugin.json`, delete a branch, or cut a release PR.

- Issue: https://github.com/mattbutlerengineering/skills/issues/1078
- Pull request: https://github.com/mattbutlerengineering/skills/pull/1079 (opened by `gh pr create`)
- Branch: `fix/a-long-line-stalls-the-gate`, base `main` (`ec8159f`)

## Pre-flight

- [x] Verification green: `verification.md` reports 8 of 8 PASS on
      `20ccc5d`, at window 17. Review's fix after it (`dc1570f`,
      window 64) was re-checked by Review and again by Ship on
      `4137538` (below; assumption 1).
- [x] Review: `review.md` has no critical finding. Major 1 (the
      17-character window fails open on one-word zero counts such as
      "zero criteria were skipped") is fixed test-first in `dc1570f`.
      The one Minor (a count wider than 64 characters still names) is
      deferred and recorded in ADR-0108's Consequences and in the
      `lean:` marker at `SUMMARY_ZERO_COUNT_WINDOW`.
- [x] No secrets in diff: `git diff origin/main...HEAD | grep -inE
      "api[_-]?key|secret|token|password"` matched only two lines of
      review.md prose about "the last three tokens", which are not
      secrets. The change needs no configuration in any target, because
      it is a constant and a pure function inside `gates.py`.
- [x] Migrations/data: none. Review's whole-tree sweep at 64 found
      `files=1012 lines=132007 differing=0`, so no tracked artifact
      changes verdict, and `gates: 0 problem(s)` below.
- [x] ADRs: the run adds no ADR. It appends one dated Consequences line
      to the existing ADR-0108, so no number to check.
- [x] Version: `.claude-plugin/plugin.json` is not in `git diff --stat
      origin/main...HEAD` (ADR-0095 rule 1). The payload copy
      `factory/templates/tools/factory/gates.py` changed, so the
      `chore(release)` PR is the Owner's, after merge.
- [x] Rollback plan concrete (below).

### Ship's re-check (HEAD `4137538`, tree clean)

```
$ python3 run_tests.py
tests: 3808 tests across 118 modules in 26.3s on 8 workers, 0 problem(s)
$ python3 lint.py
lint: 0 problem(s) across 34 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
$ git status --porcelain
$ cmp gates.py factory/templates/tools/factory/gates.py && echo "cmp: identical"
cmp: identical
```

### Pairwise hazard (`docs/kb/cross-pr-merge-hazards.md`)

`git fetch origin` left origin/main at `ec8159f`, an ancestor of HEAD.
Each open PR head was fetched to `refs/remotes/pr/<n>`:

| PR | files it changes | `git merge-tree --write-tree pr/<n> HEAD` |
|---|---|---|
| #1073 | `docs/fixes/lessons-per-signal-seen/release.md` | rc=0 |
| #1074 | `decompose_lessons.py`, its test, ADR-0116/0117, `docs/adr/README.md`, `docs/fixes/seen-before-partner/*` | rc=0 |
| #1077 | `docs/features/faster-sdlc/*` | rc=0 |

None of them shares a file with this branch, which changes `gates.py`
and its payload copy, `factory/manifest.json`, `tests/test_gates.py`,
ADR-0108, `docs/backlog.md` and this run's directory. There is no merge
order to record.

## Rollback plan

Door: two-way. Reverting one squash commit restores the whole-prefix
read in both copies. Nothing is migrated or published, and no public
interface is renamed: `SUMMARY_ZERO_COUNT_WINDOW` and `_names_unknown`
are private to `gates.py`.

Blast radius: every stamped repo's detector H, on its next payload
update after the Owner's release PR. If the width is wrong, H passes (or
refuses) a stale verification Summary written in an unusually wide zero
count. In this repo that affects nobody today (0 of 132007 tracked lines
differ). This is the same call the PR body makes under Merge danger.

```
# before merge: close the pull request; nothing reached main
gh pr close 1079

# after merge, if the fix must come out:
git checkout main && git pull
git revert --no-edit <squash sha>
rm -f $(git ls-files --others --exclude-standard | grep -E '\.(orig|rej)$')
python3 factory_init.py update-manifest     # repin the payload gates.py
python3 run_tests.py && python3 gates.py && python3 gates.py --selftest
git commit -am "revert: the zero-count read spans the whole prefix again" && git push   # via a PR
```

## Release log

1. `git fetch origin`: origin/main `ec8159f`, an ancestor of HEAD
   `4137538`.
2. Pre-flight on `4137538`: all four checks green, `git status
   --porcelain` empty, `cmp` identical (quoted above).
3. `python3 launch_demo.py config` (rc=0) printed, verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   It printed no reason line. The verdict is SHIP, but the launch brief
   was not produced in this unattended pass. It is left to the Owner
   (flagged under Outcome).
4. Pairwise merge-tree against #1073, #1074 and #1077: all rc=0, with
   disjoint files (table above).
5. Searched for an existing issue with `gh issue list --state all
   --search "long line in:title"` and `--search
   "SUMMARY_ZERO_COUNT_WINDOW"`. Both returned `[]`. Then `gh issue
   create --label type:defect --body-file <scratchpad>/ship-issue-long-line.md`
   -> https://github.com/mattbutlerengineering/skills/issues/1078
6. `git push -u origin fix/a-long-line-stalls-the-gate` -> new branch.
7. `gh pr create --base main --head fix/a-long-line-stalls-the-gate
   --body-file <scratchpad>/ship-pr-long-line.md` ->
   https://github.com/mattbutlerengineering/skills/pull/1079. The body
   has a `No work order:` line, `Closes #1078`, a Merge danger section,
   and a note that Review widened the window from 17 (the width Verify
   measured) to 64 because 17 failed open.
8. Committed this `release.md`, pushed it, and watched CI on the pushed
   head (see Outcome).

## Post-release checks

Nothing has reached users, because the pull request is open and
unmerged. The write-back runs these checks once it merges:

- `gh pr view 1079 --json state,mergedAt` -> merged, with its date.
- On main at the squash commit: `python3 run_tests.py`, `python3
  gates.py && python3 gates.py --selftest`, and `cmp gates.py
  factory/templates/tools/factory/gates.py`.
- After the Owner's release PR: a plugin cache refresh shows the new
  version, and a stamped repo's `gates.py --selftest` stays `ok` after
  its payload update.
- Issue #1078 is closed by the merge (`Closes #1078`).
- Fix runs: the producing boundary is `_names_unknown`, and its one
  consumer is `verification_sections` (detector H). Review inspected
  both. The related cleanup that remains is the exact reverse-read
  linear rewrite. It is not built, per the brief, and is named in the
  `lean:` marker and ADR-0108.

## Release steps for the Owner

1. Re-run the pairwise check against anything that merged to main
   after `ec8159f`, then merge #1079 (squash) once CI is green.
2. Cut the ADR-0095 `chore(release)` PR bumping
   `.claude-plugin/plugin.json`, because the payload `gates.py` changed.
   There is one such PR per wave, and this branch never touches the
   version.
3. Write back (protocol, "The Ship outcome"): run `next`, or `ship`
   on this run. It reads the PR with `gh pr view 1079 --json
   state,mergedAt`, rewrites `outcome: released`, adds `released-at:`
   with the merge date, keeps `pending-merge:`, and commits. If the PR
   closes unmerged, the outcome stays `prepared`.

## Outcome

Released. The Owner said "merge all prs if they are ready" in session on 2026-10-25, and #1079 was squash-merged as `bff792c` at 2026-10-25T05:02:05Z (`gh pr view 1079 --json state,mergeCommit,mergedAt` -> `MERGED`). #1078 closed with it. Merged onto main after #1073, #1077 and #1074; the merged tree was checked first in a detached worktree (3817 tests, lint, drift, gates, selftest all clean). The window width is 64, as Review set it. The deferred Minor (a zero count wider than 64 characters) still stands. The version bump belongs to the wave's `chore(release)` PR (ADR-0095). Operate is skip per the brief, so the run stays active.
