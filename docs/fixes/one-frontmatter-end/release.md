---
stage: ship
run: maintenance:one-frontmatter-end
date: 2026-10-24
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1081
assumptions:
  - "Prepare and stop: the autorun brief's release authorization is none. This pass pushed the branch, filed one type:defect issue (#1080) and opened one pull request (#1081). It did not merge, tag, delete a branch, or touch .claude-plugin/plugin.json's version (ADR-0095)."
  - "Launch brief not produced. `launch_demo.py config` prints SHIP, which under the ship skill means running the launch-demo skill. This stage's brief commits release.md alone and the run has no user-facing surface (brief: User-facing surface: none), so Ship logs the verdict and leaves the launch brief to the Owner, as prior unattended runs did (docs/fixes/a-zero-count-names-nothing/release.md)."
  - "The chain simulation is Review's, not re-run here. Ship re-ran `git merge-tree` for both pairs against the same origin/main (ec8159f, unchanged since Review) and got the same single conflicted path for each, so the simulation's inputs on main's side have not moved. The PR heads of #1079 and #1074 were not compared against the heads Review used, because review.md does not record them."
  - "Rollback default: a two-way door, undone by reverting the squash commit and regenerating the manifest. Nothing is migrated, published or renamed in a public interface."
  - "Post-release checks are deferred to the write-back: nothing reaches users until the Owner merges and cuts the wave's chore(release) PR."
  - "Date is the local date of this pass; review.md and verification.md use the UTC date (2026-10-25)."
  - "Operate is skip (autorun brief), so after the write-back the run stays active with no retro.md."
---

# Release: one owner of where frontmatter ends (prepared, not merged)

Release authorization: **prepare and stop** (autorun brief). Nothing is
merged.

- Issue: https://github.com/mattbutlerengineering/skills/issues/1080 (`type:defect`, no `wo:*` label)
- Pull request: https://github.com/mattbutlerengineering/skills/pull/1081
- Branch: `fix/one-frontmatter-end`, base `main` at `ec8159f`

## Pre-flight

- [x] Verification green: `verification.md` reports 8 criteria, 8 PASS,
      0 FAIL. Its sweep of tracked markdown found 0 changed verdicts.
- [x] Review: `review.md` has 0 critical and 0 major findings. Its three
      minors (empty-block messages in kb and the skill check, the count
      pin's false positives and blind spots, a BOM-prefixed opener) are
      deferred with reasons recorded there. Verdict: ready to ship.
- [x] No secrets in diff: `git diff origin/main...HEAD | grep -inE
      "api[_-]?key|secret|token|password|private[_-]?key"` matched only
      the `PRD_TOKEN`, `ADR_TOKEN` and `CLOSES_TOKEN` regex names and a
      backlog line about claim tokens. None is a secret. No
      configuration is needed in any target: the change is pure
      functions over strings.
- [x] Migrations/data: none. No tracked file changes verdict.
- [x] ADRs: the run adds ADR-0118. On origin/main `docs/adr/` ends at
      0116, and open PR #1074 takes 0117, so 0118 is free in either
      merge order. `docs/adr/README.md` has its row (status
      provisional).
- [x] Version: `.claude-plugin/plugin.json` is not in the diff
      (ADR-0095).
- [x] Rollback plan concrete (below).

Battery on HEAD `e322057`, tree clean:

```
$ python3 run_tests.py
tests: 3816 tests across 118 modules in 78.4s on 8 workers, 0 problem(s)
$ python3 lint.py
lint: 0 problem(s) across 34 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
$ git status --porcelain
$ for f in protocol.py gates.py knowledge_plane.py; do cmp $f factory/templates/tools/factory/$f && echo "cmp $f: 0"; done
cmp protocol.py: 0
cmp gates.py: 0
cmp knowledge_plane.py: 0
```

### Pairwise hazard (`docs/kb/cross-pr-merge-hazards.md`)

`git fetch origin` left origin/main at `ec8159f`, the branch's merge
base, so `git merge-base --is-ancestor origin/main HEAD` holds and main
has not moved since Review.

```
$ git merge-tree --write-tree --name-only HEAD origin/fix/a-long-line-stalls-the-gate   # #1079
CONFLICT (content): Merge conflict in factory/manifest.json
(gates.py, its twin and docs/backlog.md auto-merge)
$ git merge-tree --write-tree --name-only HEAD origin/fix/seen-before-partner          # #1074
CONFLICT (content): Merge conflict in docs/adr/README.md
```

Review's chain simulation (#1079, then this branch with the manifest
regenerated, then #1074 with both index rows kept) was green on all
four checks: `tests: 3827 tests across 118 modules ... 0 problem(s)`,
`lint: 0`, `drift: 0`, `gates: 0`, `selftest: ok`.

## Rollback plan

Door: two-way. One squash commit reverts it. Nothing is migrated,
published or renamed in a public interface: no existing signature
changes, and `protocol.frontmatter_end` is new.

Blast radius: frontmatter readers in this repo and, after the next
payload update, in every stamped repo (detectors H and M, kb pages,
skill frontmatter checks, the ADR status fallback). If the rule is
wrong, a file with a trailing-space fence, an empty block or a closer
at end of file is read differently. Today that is nobody: 0 tracked
files change verdict. These are the same words as the PR body's
*Merge danger* section.

```
# before merge: close the pull request; nothing reached main
gh pr close 1081

# after merge, if the change must come out:
git checkout main && git pull
git revert --no-edit <squash sha>
rm -f $(git ls-files --others --exclude-standard | grep -E '\.(orig|rej)$')
python3 factory_init.py update-manifest     # repin the restored payload twins
python3 run_tests.py && python3 lint.py && python3 kb.py drift && python3 gates.py && python3 gates.py --selftest
git push origin HEAD:revert/one-frontmatter-end && gh pr create --base main   # land the revert as a PR
```

A revert of ADR-0118's file goes with it; if the ADR is kept as a
record, mark it superseded with a new ADR instead.

## Release log

1. Battery, `git status --porcelain` and the three `cmp` checks on
   `e322057`: all clean (quoted above).
2. `git fetch origin` -> origin/main `ec8159f`, an ancestor of HEAD.
   `merge-tree` against #1079 and #1074 reproduced Review's single
   conflicted path for each.
3. `python3 launch_demo.py config` (rc=0) printed, verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   No reason line. The launch-demo skill was not run (assumptions).
4. `gh issue list --state all --search "frontmatter ends in:title"`
   -> `[]`; `--search "_skip_frontmatter"` -> only the two queue-groomer
   journals. Then `gh issue create --label type:defect --body-file
   <scratchpad>/issue-body.md` ->
   https://github.com/mattbutlerengineering/skills/issues/1080
5. `gates.pr_body_problems` on the drafted PR body -> `[]`.
6. `git push -u origin fix/one-frontmatter-end` -> new branch.
7. `gh pr create --base main --head fix/one-frontmatter-end
   --body-file <scratchpad>/pr-body.md` ->
   https://github.com/mattbutlerengineering/skills/pull/1081. The body
   carries a `No work order:` line, `Closes #1080`, the ADR-0118
   provisional note, the `tests/test_eval_trends.py` note and a
   `## Merge danger` section.
8. `gh pr checks 1081 --watch` on `e322057` -> `check` pass (22s and
   29s, two workflow runs), `review` pass, `needs-review-label` pass;
   `merged-label` skipped (open PR). rc=0.
9. Committed this `release.md` alone and pushed it; CI re-runs on that
   head.

## Post-release checks

Nothing has reached users: the pull request is open. The write-back
runs these once it merges:

- `gh pr view 1081 --json state,mergedAt` -> merged, with its date.
- On main at the squash commit: the four checks, and `cmp` for each
  payload twin.
- Issue #1080 closed by `Closes #1080`.
- Fix runs: the producing boundary (`protocol.frontmatter_end`) and its
  four consumers were inspected by Verify and Review. Related cleanup
  remaining: review.md's three deferred minors, the BOM-prefixed opener
  being the one a later run would own (a reading-boundary question for
  `cli.read_file` and `read_frontmatter`).

## Release steps for the Owner

1. **Accept ADR-0118** (or supersede it): flip `- Status: provisional`
   to accepted in `docs/adr/0118-protocol-owns-where-frontmatter-ends.md`
   and its row in `docs/adr/README.md`.
2. **Merge order and conflicts.** Re-run `git merge-tree` against
   whatever has merged first. Whichever of #1079, #1074 and #1081 lands
   second against a conflicting partner resolves it this way:
   - with #1079: conflict in `factory/manifest.json` only. Take either
     side, then run `python3 factory_init.py update-manifest` on the
     merged tree (delete any `.orig`/`.rej` first); never hand-merge
     hashes.
   - with #1074: conflict in `docs/adr/README.md` only. Keep both: #1074's
     0116 status change and 0117 row, then the 0118 row.
   Then run the four checks, push, and wait for CI before merging.
3. Squash-merge #1081 once CI is green.
4. Cut the wave's `chore(release)` PR bumping
   `.claude-plugin/plugin.json` (ADR-0095): the payload twins changed.
   This branch never touches the version.
5. **Write back** (protocol, "The Ship outcome"): run `next`, or `ship`
   on this run. It reads `gh pr view 1081 --json state,mergedAt`, and on
   a merge rewrites `outcome: released`, adds `released-at:` with the
   merge date, keeps `pending-merge:`, and commits. A PR closed
   unmerged leaves the outcome `prepared`.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:`
names (#1081). CI is green on `e322057`. Operate is skip (autorun
brief), so after the write-back the run stays active with no retro.
Flags for the Owner: ADR-0118 is provisional; the merge-order conflicts
with #1079 and #1074 above; the launch brief was not produced; the
version bump belongs to the wave's release PR.
