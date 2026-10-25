---
stage: ship
run: maintenance:tool-duplicates-that-drifted
date: 2026-10-25
outcome: released
released-at: 2026-10-25
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1110
---

# Release: one owner each for drifted duplicate facts in the root tools

## Pre-flight

- [x] Verification green: 8 PASS, 0 FAIL, 1 NOT RUN (the live scheduled
      digest and miner). Review's fixes (`1493538`) landed after it, and
      the checks re-ran there:
      - `tests: 3926 tests across 123 modules in 31.7s on 8 workers, 0 problem(s)`
      - `lint: 0 problem(s) across 35 skills`
      - `gates: 0 problem(s)`
      - `selftest: ok`
      - `factory-init: 0 problem(s)`
- [x] Review: no critical finding. One major and four minors fixed or
      recorded in `1493538`.
- [x] No secrets in diff (root and payload tools, tests, backlog, run docs).
      No target configuration needed.
- [x] No migrations or data changes, and no ADR added.
- [x] Wave merge simulation: `origin/main` plus #1106, then this branch
      (manifest regenerated), then #1108, in a detached worktree:
      - `tests: 3934 tests across 124 modules in 57.1s on 8 workers, 0 problem(s)`
      - `lint: 0 problem(s) across 35 skills`
      - `drift: 0 problem(s)`
      - `gates: 0 problem(s)`
      - `selftest: ok`
      - `one-owner: 0 problem(s)`

      The one conflict is `factory/manifest.json`, which is regenerated and
      never hand-merged.
- [x] Protected paths: `.claude-plugin/plugin.json` untouched (ADR-0095).
      Payload modules changed, so the wave's release PR bumps the version.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert restores the copies, and nothing migrates.

Blast radius: payload tools in stamped repos after `factory-init update`,
and root-only kb_drift, md_claims, dashboard and board. If the call is
wrong, a scheduled digest or miner posts differently. Their exact-string
suites are unchanged, and the live runs are NOT RUN.

(The same call the PR body makes under `## Merge danger`.)

```
# Before merge
gh pr close 1110

# After merge: revert the squash commit, regenerate the payload, re-check
git checkout -b revert/tool-duplicates-that-drifted origin/main
git revert <merge sha of PR 1110>
python3 factory_init.py update-manifest
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/tool-duplicates-that-drifted
gh pr create --base main --body-file <body>   # "No work order:" + "Closes #N"
```

## Release log

1. Soft gate: review.md Verdict, "No critical finding was raised" -> pass.
2. `python3 launch_demo.py config` -> `SHIP` / `launch-demo: 0 problem(s)`.
   Not run: a tool consolidation has nothing on screen to record. This
   follows the Owner's in-session answer for this wave's first release
   ("Skip, log the verdict").
3. `gh issue create --label type:chore` -> #1109 (the PR closes it).
4. `gates.pr_body_problems(body)` -> `[]`.
5. `git push -u origin fix/tool-duplicates-that-drifted` -> new branch.
6. `gh pr create --base main` ->
   https://github.com/mattbutlerengineering/skills/pull/1110
7. Write-back (2026-10-25): the Owner answered "Merge all + release" in session for the consolidation wave. Merged in order #1106, #1110 (after merging main and regenerating the manifest, CI green), #1108. `gh pr merge 1110 --squash` -> `b4f055d`; `gh pr view 1110 --json state,mergedAt` -> `MERGED`, `2026-10-25T21:59:33Z`. On main afterwards `python3 one_owner.py` -> `one-owner: 0 problem(s)`. The 0.23.2 release PR carries this write-back.

## Post-release checks

- Merge order: #1106 first. This branch then merges main and regenerates
  the manifest before its own merge, and #1108 follows.
- After the merge: `python3 one_owner.py` on main prints `one-owner: 0
  problem(s)`. The next scheduled gate-digest and rejection-mining runs post
  as before.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names.
