---
stage: ship
run: maintenance:the-selftest-cannot-see-a-dodge
date: 2026-10-18
outcome: prepared
pending-merge: https://github.com/mattbutlerengineering/skills/pull/1029
assumptions:
  - "Ship's independent re-check stands in for re-running Verify. verification.md (`0cbbdf9`) predates the fix-loop commits `dfae528`, `8a7d334` and `1ce5ba2`, and until now only their author had checked them. Ship re-ran the four checks on `1ce5ba2`, wrote its own mutation script (ship_dodge_mutate.py in the session scratchpad) for R2 and R3, ran it in a detached scratch worktree and in a freshly stamped temp repo, and compared the root and payload gates_selftest.py with `cmp`, all quoted below. verification.md is not rewritten."
  - "Launch brief: `launch_demo.py config` printed the verdict SHIP, which under the skill means running the launch-demo skill. As in prior unattended runs, it is left to the Owner and not produced here. The run has no user-facing surface (brief: User-facing surface: none)."
  - "Rollback default: the protocol's two-way door, undone by `git revert` of the squash commit plus a manifest regen. There is no data, no migration and no published version from this branch."
  - "The run adds no new ADR. It amends ADR-0108 with a dated note under its Consequences, so the ADR-number pre-flight has no number to check."
  - "Post-release checks are deferred to the write-back. Under prepare-and-stop nothing reaches users until the Owner merges and cuts the ADR-0095 release PR, so the checks below are the ones the write-back runs."
---

# Release: the selftest cannot see a dodge (prepared, not merged)

Release authorization: **prepare and stop** (autorun brief, Owner
decision 2). This pass pushed the branch, filed one `type:defect`
issue, and opened one pull request. It did not merge, tag, bump
`.claude-plugin/plugin.json`, delete a branch, or cut a release PR.

- Issue: https://github.com/mattbutlerengineering/skills/issues/1028
- Pull request: https://github.com/mattbutlerengineering/skills/pull/1029 (opened by `gh pr create`)
- Branch: `fix/the-selftest-cannot-see-a-dodge`, base `main` (`f8c16d9`)

## Pre-flight

- [x] Verification green: `verification.md` reports 8 of 8 PASS on
      `aa0d38d`. The three fix-loop commits after it were independently
      re-checked by Ship on `1ce5ba2` (below).
- [x] Review: `review.md` has no critical and no major finding. Its
      three minors were all fixed in the fix loop (Owner: Fix all three
      now): Minors 1 and 2 in `dfae528`, Minor 3 in `8a7d334`. None
      stays deferred.
- [x] No secrets in diff: `git diff origin/main...HEAD | grep -inE
      "api[_-]?key|secret|token|password"` matched nothing. The change
      needs no configuration in any target, because it is offline
      selftest fixtures and unit tests.
- [x] Migrations/data: none. `gates.py` is not in the diff, so no gate
      behaviour changes and no tracked artifact changes outcome
      (`gates: 0 problem(s)` below).
- [x] ADRs: no new ADR. `docs/adr/0108-a-zero-count-names-nothing.md`
      gains a dated amendment (5 lines) and stays provisional.
- [x] Version: `.claude-plugin/plugin.json` is not in `git diff --stat
      origin/main...HEAD` (ADR-0095 rule 1). The payload copy
      `factory/templates/tools/factory/gates_selftest.py` changed, so
      the `chore(release)` PR is the Owner's, after merge.
- [x] Rollback plan concrete (below).

### Independent re-check of the fix loop (HEAD `1ce5ba2`, tree clean)

```
$ python3 run_tests.py
tests: 3327 tests across 106 modules in 14.4s on 8 workers, 0 problem(s)
$ python3 lint.py
lint: 0 problem(s) across 34 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
$ cmp gates_selftest.py factory/templates/tools/factory/gates_selftest.py && echo "cmp: identical"
cmp: identical
```

Mutations (`ship_dodge_mutate.py`, written fresh for this pass). R2
makes `_grandfathered` strip quotes but drop the ISO match (the two
lines `iso = FRONTMATTER_ISO_DATE.match(value)` / `return bool(iso) and
iso.group(1) < cutoff` become `return value < cutoff`). R3 narrows
`SUMMARY_ZERO_COUNT`'s `(?:0|zero|no|none|nothing)` to `(?:0)`. The
script asserts the old text occurs once, applies each mutation alone,
checks it landed, runs the selftest, and restores the file's bytes
before the next one and in a `finally` block. In a detached scratch
worktree at `1ce5ba2`, `python3 gates.py --selftest`:

```
--- baseline
selftest: ok
exit=0
=== R2_strip_quotes_no_iso (landed: True)
--- R2_strip_quotes_no_iso
M empty date: expected a problem containing "docs/fixes/demo/defect.md missing required section 'Root-cause hypothesis'", got []
H empty date: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got []
O empty date: expected a problem containing 'docs/features/demo/prd.md:12 PRD-0001 §Actors is cited by no breakdown row', got []
selftest: FAIL
exit=1
=== R3_zero_digit_only (landed: True)
--- R3_zero_digit_only
H none skipped: expected a problem containing 'docs/features/rollup/verification.md:7 summary "Summary" neither counts nor names', got []
selftest: FAIL
exit=1
restored: True
```

`git status --porcelain` in the worktree was empty afterwards. Each
mutation fails only the rows the fix loop added for it, and no other
row.

A freshly stamped temp repo (`git init`, then stamped from this
branch), on the unmutated code:

```
$ python3 factory_init.py stamp <tmp>
factory-init: 0 problem(s)
stamp exit=0
$ cmp <tmp>/tools/factory/gates_selftest.py gates_selftest.py && echo "cmp: stamped copy == branch root copy"
cmp: stamped copy == branch root copy
$ python3 tools/factory/gates.py --selftest      # from <tmp>
selftest: ok
exit=0
```

The same script, run against the stamped `tools/factory/gates.py`,
printed output identical to the worktree run above (baseline `ok`, R2
failing the three empty-date rows, R3 failing `H none skipped`,
`restored: True`). The scratch worktree and the temp repo were then
removed (`git worktree remove`, `rm -rf`).

Verify's criteria 2 and 3 already cover the four original reversions
on `aa0d38d` (O, M and H's date compares at their call sites, and a
zero-blind `_names_unknown`). The fix loop added rows and did not edit
the four original ones, and the two `TestSelftest` pins that patch
those reversions pass inside `run_tests.py` above.

### Pairwise hazard (`docs/kb/cross-pr-merge-hazards.md`)

```
$ git fetch origin
$ git rev-parse --short origin/main
f8c16d9
$ git merge-base --is-ancestor origin/main HEAD && echo "origin/main is ancestor of HEAD"
origin/main is ancestor of HEAD
$ git merge-tree --write-tree origin/main HEAD
8b41100daa6c7b375861f1573b60dab6db49ae08        (rc=0, no conflict)
$ gh pr list --state open --json number,title
[]
```

origin/main has not moved since Verify, and no other PR is open, so
there is no pair to simulate.

## Rollback plan

Door: two-way. Reverting one squash commit removes the selftest rows,
the fixture parameters, the `TestSelftest` pins and the ADR-0108
amendment. Nothing is migrated, published or renamed in a public
interface, and `gates.py` is unchanged.

Blast radius: if the call is wrong, a stamped repo's `gates.py
--selftest` goes red on a correct payload, or stays green on a
regression it should catch. Today the rows pass on the shipped
`gates.py`, both in this repo and in a freshly stamped one. Stamped
repos get the rows on their next payload update, after the Owner's
release PR.

```
# before merge: close the pull request; nothing reached main
gh pr close 1029

# after merge, if the rows must come out:
git checkout main && git pull
git revert --no-edit <squash sha>
rm -f $(git ls-files --others --exclude-standard | grep -E '\.(orig|rej)$')
python3 factory_init.py update-manifest     # repin the payload gates_selftest.py
python3 run_tests.py && python3 gates.py && python3 gates.py --selftest
git commit -am "revert: drop the selftest dodge rows" && git push   # via a PR
```

## Release log

1. Independent re-check of the fix loop on `1ce5ba2`: all four checks
   green, R2 and R3 each fail only their own rows in a scratch worktree
   and in a stamped temp repo, the stamped repo reads `selftest: ok`
   unmutated, and `cmp` is identical (quoted above).
2. `review.md`: no critical or major finding, and all three minors are
   fixed.
3. `git fetch origin` -> origin/main `f8c16d9`, an ancestor of HEAD.
   `git merge-tree --write-tree origin/main HEAD` -> `8b41100…`, rc=0.
   `gh pr list --state open` -> `[]`.
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
   --search` for "selftest in:title", "dodge", "gates_selftest",
   "selftest dodge" and "zero-count row". The hits were closed and
   unrelated (#784, #859, #1001, #1003, #1017) or the open journal
   #181. Then `gh issue create --label type:defect` ->
   https://github.com/mattbutlerengineering/skills/issues/1028
6. `git push -u origin fix/the-selftest-cannot-see-a-dodge` -> new
   branch.
7. `gh pr create --base main --head fix/the-selftest-cannot-see-a-dodge
   --body-file <scratchpad>/ship-pr-dodge.md` ran as the first command
   of its own Bash call ->
   https://github.com/mattbutlerengineering/skills/pull/1029. The body
   has a `No work order:` line and `Closes #1028`.
8. `gh pr checks 1029 --watch` on `1ce5ba2` -> `check` pass (19s on the
   push run, 28s on the pull-request run), `needs-review-label` pass,
   `review` pass. `merged-label` was skipped, as expected for an open
   PR. rc=0.
9. Committed this `release.md`, pushed it, and confirmed CI on the
   pushed head (see Outcome).

## Post-release checks

Nothing has reached users, because the pull request is open and
unmerged. The write-back runs these checks once it merges:

- `gh pr view 1029 --json state,mergedAt` -> merged, with its date.
- On main at the squash commit: `python3 run_tests.py`, `python3
  gates.py && python3 gates.py --selftest`, and `cmp gates_selftest.py
  factory/templates/tools/factory/gates_selftest.py`.
- After the Owner's release PR: a plugin cache refresh shows the new
  version, and a stamped repo's `tools/factory/gates.py --selftest`
  stays `ok` after its payload update.
- Issue #1028 is closed by the merge (`Closes #1028`).

## Release steps for the Owner

1. Merge #1029 (squash) once CI is green. Before merging, re-run the
   pairwise check (`git merge-tree --write-tree origin/main
   origin/fix/the-selftest-cannot-see-a-dodge`) against anything that
   merged after `f8c16d9`.
2. Cut the ADR-0095 `chore(release)` PR bumping
   `.claude-plugin/plugin.json`, because the payload
   `gates_selftest.py` changed. There is one such PR per wave, and this
   branch never touches the version.
3. Write back (protocol, "The Ship outcome"): run `next`, or `ship`
   on this run. It reads the PR with `gh pr view 1029 --json
   state,mergedAt`, rewrites `outcome: released`, adds `released-at:`
   with the merge date, keeps `pending-merge:`, and commits. If the PR
   closes unmerged, the outcome stays `prepared`.

## Outcome

Prepared and stopped. The run waits on the pull request
`pending-merge:` names (#1029), and stays at Ship until the merge is
written back. For the Owner:

- **Merge** #1029 (step 1 above). No other PR is open, so there is no
  merge-order conflict today.
- **Version bump**: not done here (ADR-0095). It belongs to the Owner's
  `chore(release)` PR after merge (step 2).
- **Launch brief**: `launch_demo.py config` returned the verdict SHIP,
  but the brief was not produced in this unattended pass. Run the
  `launch-demo` skill for this run if wanted.
- **Operate**: skipped by Owner decision 3 (autorun brief).
- **Verify was not re-run** after the fix loop. Ship's independent
  re-check above stands in for it (assumption 1).
