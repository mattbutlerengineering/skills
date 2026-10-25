---
stage: ship
run: maintenance:a-spend-row-stalls-the-merge
date: 2026-10-25
outcome: released
released-at: 2026-10-25
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1106
---

# Release: a ship step's spend file no longer stalls the Conductor's merge

## Pre-flight

- [x] Verification green: 5 PASS, 0 FAIL, 1 NOT RUN (criterion 6, a live
      Conductor batch). Review's fixes (`8c13378`) landed after it, and the
      checks re-ran there: `tests: 3911 tests across 122 modules ... 0
      problem(s)`, `lint: 0 problem(s) across 35 skills`, `drift: 0
      problem(s)`, `gates: 0 problem(s)`, `selftest: ok`, `factory-init: 0
      problem(s)`.
- [x] Review: no critical finding. Two majors and two minors fixed in
      `8c13378`; the rewrite limit is recorded.
- [x] No secrets in diff (two payload modules, their tests, run docs). No
      target configuration needed.
- [x] No migrations or data changes.
- [x] No ADR added.
- [x] Base: `git merge-tree --write-tree HEAD origin/main` -> exit 0,
      clean. Two sibling runs of the same wave (B, C) are open. Their
      chain merge is simulated before any merge (Release steps).
- [x] Protected paths: `.claude-plugin/plugin.json` untouched (ADR-0095).
      Payload modules changed, so the wave's release PR bumps the version.
- [x] Rollback plan concrete (below).

## Rollback plan

Door: two-way. A revert restores the old drift check. Nothing migrates.

Blast radius: Conductor batches in every stamped repo once
`factory-init update` pulls the payload. If the call is wrong, a merge turn
stalls when it shouldn't (the old behaviour), or a post-review spend file
merges unreviewed. Its content is shape-checked by detector G in CI.

(The same call the PR body makes under `## Merge danger`.)

```
# Before merge
gh pr close 1106

# After merge: revert the squash commit, regenerate the payload, re-check
git checkout -b revert/a-spend-row-stalls-the-merge origin/main
git revert <merge sha of PR 1106>
python3 factory_init.py update-manifest
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push -u origin revert/a-spend-row-stalls-the-merge
gh pr create --base main --body-file <body>   # "No work order:" + "Closes #N"
```

## Release log

1. Soft gate: review.md Verdict, "No critical finding was raised" -> pass.
2. `python3 launch_demo.py config` -> `SHIP` / `launch-demo: 0 problem(s)`.
   Not run: a merge-check fix in a payload tool has nothing on screen to
   record. This follows the Owner's answer for this session's previous
   release ("Skip, log the verdict").
3. `gh issue create --label type:defect` -> #1105 (the PR closes it).
4. `gates.pr_body_problems(body)` -> `[]`.
5. `git push -u origin fix/a-spend-row-stalls-the-merge` -> new branch.
6. `gh pr create --base main` ->
   https://github.com/mattbutlerengineering/skills/pull/1106
7. Write-back (2026-10-25): the Owner answered "Merge all + release" in session for the consolidation wave. Merged in order #1106, #1110 (after merging main and regenerating the manifest, CI green), #1108. `gh pr merge 1106 --squash` -> `c8d63c0`; `gh pr view 1106 --json state,mergedAt` -> `MERGED`, `2026-10-25T21:56:18Z`. On main afterwards `python3 one_owner.py` -> `one-owner: 0 problem(s)`. The 0.23.2 release PR carries this write-back.

## Post-release checks

- Nothing is released until the PR merges. The wave's release PR then
  bumps the version, and stamped repos pick it up on `factory-init update`.
- First live observation: the next Conductor batch's merge turn passes its
  ship step's spend file.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:` names.
Merge order for the wave: this run, then `tool-duplicates-that-drifted`
(which touches `trace.py` and the manifest too), then
`one-owner-for-copied-skill-text`, then one `chore(release)`.
