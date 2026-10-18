---
stage: ship
run: maintenance:a-zero-count-names-nothing
date: 2026-10-18
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1018
assumptions:
  - "Ship's independent re-check stands in for re-running Verify. verification.md (`7e017c6`) predates the fix-loop commits `c2ef6e0` and `779f968`, and until now only their author had checked them. Ship re-ran the four checks on `779f968`, wrote its own probe and mutation scripts (ship_recheck.py, ship_mutate.py in the session scratchpad), and compared the two gates.py copies with `cmp`, all quoted below. verification.md is not rewritten."
  - "Launch brief: `launch_demo.py config` printed the verdict SHIP, which under the skill means running the launch-demo skill. As in prior unattended runs, it is left to the Owner and not produced here. The run has no user-facing surface (brief: User-facing surface: none)."
  - "Rollback default: the protocol's two-way door, undone by `git revert` of the squash commit plus a manifest regen. There is no data, no migration and no published version from this branch."
  - "origin/main moved to `a3d9aca` (two docs/kb commits, #1014 and #1016) and is not an ancestor of HEAD. The branch was not merged with main because merge-tree is clean and the simulated merge passes all four checks. CI runs on the PR's merge ref."
  - "Post-release checks are deferred to the write-back. Under prepare-and-stop nothing reaches users until the Owner merges and cuts the ADR-0095 release PR, so the checks below are the ones the write-back runs."
---

# Release: a zero count names nothing (prepared, not merged)

Release authorization: **prepare and stop** (autorun brief, Owner
decision 3). This pass pushed the branch, filed one `type:defect`
issue, and opened one pull request. It did not merge, tag, bump
`.claude-plugin/plugin.json`, delete a branch, or cut a release PR.

- Issue: https://github.com/mattbutlerengineering/skills/issues/1017
- Pull request: https://github.com/mattbutlerengineering/skills/pull/1018 (opened by `gh pr create`)
- Branch: `fix/a-zero-count-names-nothing`, base `main` (`a3d9aca`)

## Pre-flight

- [x] Verification green: `verification.md` reports 13 of 13 PASS on
      `7e017c6`. The two fix-loop commits after it were independently
      re-checked by Ship on `779f968` (below).
- [x] Review: `review.md` has no critical and no major finding. Minors 1
      and 3 were fixed in `c2ef6e0` (Owner: Fix now). Minors 2, 4 and 5
      are deferred, each with a seed in `docs/backlog.md` tagged
      `(from: maintenance:a-zero-count-names-nothing)`:
      - Minor 2: zero shapes that still name (a hard-wrapped count,
        "NOT RUN: 0", table cells, an en dash, "0 (zero)", "0:", "0x").
        These are also listed as accepted limits in ADR-0108's
        Consequences.
      - Minor 4: `_names_unknown` is quadratic in line length. The seed
        proposes a bounded window before `match.start()`.
      - Minor 5: `skills/verify/SKILL.md` lines 31 to 33 still state
        ADR-0107's rule alone. The seed proposes citing ADR-0108 there.
- [x] No secrets in diff: `git diff origin/main...HEAD | grep -inE
      "api[_-]?key|secret|token|password"` matched only two lines
      holding the regex name `NOT_RUN_TOKEN`, which is not a secret. The
      change needs no configuration in any target, because it is a pure
      function inside `gates.py`.
- [x] Migrations/data: none. No tracked artifact changes outcome
      (review's sweep `files=93 refused_main=0 refused_head=0
      outcome_changes=0`, and `gates: 0 problem(s)` below).
- [x] ADRs: the run adds ADR-0108. `git fetch origin` left origin/main
      at `a3d9aca`, whose `docs/adr/` ends at 0107
      (`0107-a-summary-never-rolls-unknown-up-to-pass.md`), and the one
      open PR (#1012) adds no 0108. The number is free. Line 131 of
      `docs/adr/README.md` holds its row ("A zero count in a
      verification Summary names nothing", status provisional).
- [x] Version: `.claude-plugin/plugin.json` is not in `git diff --stat
      origin/main...HEAD` (ADR-0095 rule 1). The payload copy
      `factory/templates/tools/factory/gates.py` changed, so the
      `chore(release)` PR is the Owner's, after merge.
- [x] Rollback plan concrete (below).

### Independent re-check of the fix loop (HEAD `779f968`, tree clean)

```
$ python3 run_tests.py
tests: 3321 tests across 106 modules in 14.3s on 8 workers, 0 problem(s)
$ python3 lint.py
lint: 0 problem(s) across 34 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
$ cmp gates.py factory/templates/tools/factory/gates.py && echo "cmp: identical"
cmp: identical
```

Probe through H's public function `gates.evidence_problems`
(`ship_recheck.py`, written fresh for this pass). First the retro's
probe: criterion 9 of the tracked
`docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md` is flipped
in memory to `- Result: NOT RUN — probe`, with its Summary unchanged.
Then three one-line Summaries over a fixture with one evidenced PASS and
one `- Result: NOT RUN — needs a second account.`:

```
criterion 9 result line 278 ; summary line 15 '11 criteria: 11 PASS, 0 FAIL, 0 NOT RUN. On HEAD `8745052`, every'
retro probe (Summary '0 NOT RUN', crit 9 NOT RUN) -> [(13, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "9. The backlog claim is in place", line 278); unknown never rolls up to pass')]
'3 PASS, 0 FAIL NOT RUN: criterion 9.' -> []
'3 PASS, 0 FAIL - NOT RUN: criterion 9.' -> []
'1 PASS, 0 FAIL, 0 NOT RUN.' -> [(8, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "2. Live dispatch", line 23); unknown never rolls up to pass')]
```

So the retro probe is refused, both Minor 1 shapes pass, and "0 NOT
RUN" over a disclosure is refused. (The fixture's first draft had a PASS
criterion with no fenced evidence block. H flagged that on its own
per-section rule, so Ship fixed the fixture and re-ran. The output above
is from that re-run.)

Mutation of the `(?!pass|fail)` exclusion (`ship_mutate.py`). The
script asserts that the old text occurs once, removes the lookahead from
the root `gates.py`, runs `python3 -m unittest tests.test_gates`, and
restores the file's bytes in a `finally` block:

```
landed: True
rc 1
FAIL: test_named_summary_after_a_zero_count_label_passes (tests.test_gates.TestEvidenceRollUp.test_named_summary_after_a_zero_count_label_passes) (summary='3 PASS, 0 FAIL NOT RUN: criterion 9.')
FAIL: test_named_summary_after_a_zero_count_label_passes (tests.test_gates.TestEvidenceRollUp.test_named_summary_after_a_zero_count_label_passes) (summary='3 PASS, 0 FAILED NOT RUN: criterion 9.')
FAIL: test_named_summary_after_a_zero_count_label_passes (tests.test_gates.TestEvidenceRollUp.test_named_summary_after_a_zero_count_label_passes) (summary='0 passed NOT RUN: criterion 9.')
Ran 290 tests in 4.142s
FAILED (failures=3)
restored: True
```

After the mutation, `git status --porcelain` was empty and `cmp`
reported the two copies identical.

### Pairwise hazard (`docs/kb/cross-pr-merge-hazards.md`)

`git fetch origin` -> origin/main `a3d9aca`, not an ancestor of HEAD.
Main is ahead by #1014 and #1016, which each change one line in
`docs/kb/`.

```
$ git merge-tree --write-tree origin/main HEAD
713970be4290e5811c27c48de42a367ea25e226f        (rc=0, no conflict)
```

Each pairing was chain-simulated in a detached worktree in the session
scratchpad. The four checks ran there, and the worktree was then
removed:

| Pair | merge-tree | resolution | `run_tests.py` | `lint.py` | `kb.py drift` | `gates.py` / `--selftest` |
|---|---|---|---|---|---|---|
| origin/main `a3d9aca` + HEAD (sim commit `794b29a`) | rc=0 | none needed | `3321 tests ... 0 problem(s)` | `0 problem(s)` | `0 problem(s)` | `0 problem(s)` / `ok` |
| #1012 `36c0a7b` + HEAD, then origin/main | rc=1, `CONFLICT (content): Merge conflict in docs/backlog.md` | keep both sides | `3323 tests ... 0 problem(s)` | `0 problem(s)` | `0 problem(s)` | `0 problem(s)` / `ok` |

The #1012 conflict happens because both branches append seed lines at
the end of `docs/backlog.md`. #1012 adds the doctor-tool seed, and this
branch adds the three deferred-minor seeds. The two sets are
independent, so keeping both sides is the whole resolution. It is
recorded as a merge-order step below and was not resolved on this
branch.

## Rollback plan

Door: two-way. Reverting one squash commit restores the old
word-presence test in both copies. Nothing is migrated, published or
renamed in a public interface: `SUMMARY_ZERO_COUNT` and
`_names_unknown` are private to `gates.py`.

Blast radius: if the call is wrong, detector H refuses (or stops
refusing) a dated `verification.md` because of how its Summary is
worded. In this repo that is nobody today (0 outcome changes across 93
tracked files). Each stamped repo gets the new behaviour on its next
payload update, after the Owner's release PR. A repo that wrote a
zero-count Summary over a disclosed criterion would then see an
actionable H problem string.

```
# before merge: close the pull request; nothing reached main
gh pr close 1018

# after merge, if the fix must come out:
git checkout main && git pull
git revert --no-edit <squash sha>
rm -f $(git ls-files --others --exclude-standard | grep -E '\.(orig|rej)$')
python3 factory_init.py update-manifest     # repin the payload gates.py
python3 run_tests.py && python3 gates.py && python3 gates.py --selftest
git commit -am "revert: a zero count names again" && git push   # via a PR
```

## Release log

1. Independent re-check of the fix loop on `779f968`: all four checks
   green, probes and mutation as expected, `cmp` identical (quoted
   above).
2. `git fetch origin` -> origin/main `a3d9aca`. ADR-0108 is free on
   it. `git merge-tree --write-tree origin/main HEAD` -> `713970b…`,
   rc=0.
3. Pairwise chain-simulation against origin/main and #1012. Main is
   clean. #1012 conflicts on `docs/backlog.md`, and keeping both sides
   resolves it with all checks green (table above).
4. `python3 /Users/mbutler/.claude/plugins/cache/skills/idea-to-prod/0.20.0/launch_demo.py config`
   (rc=0) printed, verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   It printed no reason line. The verdict is SHIP, but the launch brief
   was not produced in this unattended pass. It is left to the Owner
   (flagged under Outcome).
5. Searched for an existing issue with `gh issue list --state all
   --search "zero count in:title"` and `--search "names_unknown"`. Both
   returned `[]`. `--search "0 NOT RUN"` returned only release issues.
   Then `gh issue create --label type:defect` ->
   https://github.com/mattbutlerengineering/skills/issues/1017
6. `git push -u origin fix/a-zero-count-names-nothing` -> new branch.
7. `gh pr create --base main --head fix/a-zero-count-names-nothing
   --body-file <scratchpad>/ship-pr-zero.md` ran as the first command of
   its own Bash call ->
   https://github.com/mattbutlerengineering/skills/pull/1018. The body
   has a `No work order:` line and `Closes #1017`.
8. `gh pr checks 1018 --watch` on `779f968` -> `check` pass (26s and
   27s, two workflow runs), `review` pass, and `needs-review-label`
   pass. `merged-label` was skipped, as expected for an open PR. rc=0.
9. Committed this `release.md`, pushed it, and confirmed CI on the
   pushed head (see Outcome).

## Post-release checks

Nothing has reached users, because the pull request is open and
unmerged. The write-back runs these checks once it merges:

- `gh pr view 1018 --json state,mergedAt` -> merged, with its date.
- On main at the squash commit: `python3 run_tests.py`, `python3
  gates.py && python3 gates.py --selftest`, and `cmp gates.py
  factory/templates/tools/factory/gates.py`.
- After the Owner's release PR: a plugin cache refresh shows the new
  version, and a stamped repo's `gates.py --selftest` stays `ok` after
  its payload update.
- Issue #1017 is closed by the merge (`Closes #1017`).

## Release steps for the Owner

1. **Merge order with #1012.** Both PRs append to the end of
   `docs/backlog.md`, so whichever merges second will conflict there.
   Merge the first one. For the second, run `git merge origin/main`
   on its branch, keep both sets of backlog lines, re-run `python3
   run_tests.py`, `python3 lint.py`, `python3 kb.py drift`, and
   `python3 gates.py && python3 gates.py --selftest`, then push and wait
   for CI before merging. A simulation of that resolution passed all
   four checks.
2. Merge #1018 (squash) once CI is green. Before merging, re-run the
   pairwise check against whatever else merged first.
3. Cut the ADR-0095 `chore(release)` PR bumping
   `.claude-plugin/plugin.json`, because the payload `gates.py` changed.
   There is one such PR per wave, and this branch never touches the
   version.
4. Write back (protocol, "The Ship outcome"): run `next`, or `ship`
   on this run. It reads the PR with `gh pr view 1018 --json
   state,mergedAt`, rewrites `outcome: released`, adds `released-at:`
   with the merge date, keeps `pending-merge:`, and commits. If the PR
   closes unmerged, the outcome stays `prepared`.

## Outcome

Prepared and stopped. The run is waiting on the pull request that
`pending-merge:` names (#1018, CI green). Ship stays pending until the
merge is written back. Flags for the Owner:

- **Merge-order conflict with #1012** on `docs/backlog.md`. Keep both
  sides (step 1 above).
- **Deferred Minors 2, 4 and 5** are seeded in `docs/backlog.md`.
  Minor 2 is also an accepted limit in ADR-0108.
- **Launch brief**: `launch_demo.py config` returned the verdict SHIP,
  but the brief was not produced in this unattended pass. Run the
  `launch-demo` skill for this run if wanted.
- **Version bump**: not done here (ADR-0095). It belongs to the Owner's
  `chore(release)` PR after merge.
- **Operate**: skipped by Owner decision 4 (autorun brief).
- **Verify was not re-run** after the fix loop. Ship's independent
  re-check above stands in for it (assumption 1).
