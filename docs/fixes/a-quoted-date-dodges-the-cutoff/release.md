---
stage: ship
run: maintenance:a-quoted-date-dodges-the-cutoff
date: 2026-10-17
outcome: prepared
pending-merge: (set once the pull request is opened)
assumptions:
  - "Launch brief: `launch_demo.py config` printed the verdict SHIP, which by the skill means run the launch-demo skill. The orchestrator's instruction for this unattended pass was not to produce it, so it is flagged for the Owner instead of produced. A gates fix with no user-facing surface (brief: User-facing surface: none) has little to demo."
  - "Rollback default: the protocol's two-way door, undone by `git revert` of the squash commit plus a manifest regen; no data, no migration, no published version from this branch."
  - "Post-release checks are deferred to the write-back: under prepare-and-stop nothing reaches users until the Owner merges and cuts the ADR-0095 release PR, so the checks below are the ones the write-back runs."
---

# Release: a quoted date dodges the cutoff (prepared, not merged)

Release authorization: **prepare and stop** (autorun brief, Owner
decision 3). This pass pushed the branch, filed one `type:defect`
issue, and opened one pull request. It did not merge, tag, bump
`.claude-plugin/plugin.json`, delete a branch, or cut a release PR.

- Issue: https://github.com/mattbutlerengineering/skills/issues/1001
- Branch: `fix/a-quoted-date-dodges-the-cutoff`, base `main` (`461803a`)

## Pre-flight

- [x] Verification green: `verification.md` 11 of 11 PASS, 0 FAIL,
      0 NOT RUN.
- [x] Review: `review.md` has no critical and no major finding; two
      minors deferred with reasons (listed under Outcome).
- [x] No secrets in diff: `git diff origin/main...HEAD | grep -inE
      "api[_-]?key|secret|token|password"` printed nothing. No
      configuration is needed in any target: the change is a pure
      function inside `gates.py`.
- [x] Migrations/data: none. No artifact on main changes outcome
      (Capture's count of 0 dodge shapes over 106 tracked `prd.md` and
      `defect.md` files; `python3 gates.py` -> `gates: 0 problem(s)`).
- [x] ADRs: the run adds no new ADR. It appends dated amendments to
      ADR-0073 and ADR-0107, both already in the index, so no number can
      collide.
- [x] Version: the branch has no `.claude-plugin/plugin.json` change
      (ADR-0095 rule 1; `git diff --stat origin/main...HEAD` does not
      list it). The payload copy `factory/templates/tools/factory/gates.py`
      changed, so installed plugin caches refresh only after a version
      bump: the `chore(release)` PR is the Owner's, after merge.
- [x] Rollback plan concrete (below).

Battery on HEAD `9986f3c` (tree clean):

```
$ python3 run_tests.py
tests: 3312 tests across 106 modules in 14.0s on 8 workers, 0 problem(s)
$ python3 lint.py
lint: 0 problem(s) across 34 skills
$ python3 kb.py drift
drift: 0 problem(s)
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

Pairwise hazard (`docs/kb/cross-pr-merge-hazards.md`). `git fetch origin
main` left `origin/main` at `461803a`, an ancestor of HEAD:

```
$ git merge-tree --write-tree origin/main HEAD
d085dfa454d5d2c252ad60c4694f62ff3a9bcd9f        (rc=0, no conflict)
```

Each open PR chain-simulated with this branch (merge-tree, commit-tree
with both parents, a detached worktree in the session scratchpad, the
two checks run there, then the worktree removed and the temporary ref
deleted; `git worktree list` shows no pairwise worktree left):

| PR | Head | merge-tree | `python3 gates.py` | `python3 kb.py drift` |
|---|---|---|---|---|
| #993 (pr-body-preflight release.md write-back) | `94f78e3` | rc=0 | `gates: 0 problem(s)` | `drift: 0 problem(s)` |
| #1000 (fail-closed-roll-up release.md write-back) | `41511e1` | rc=0 | `gates: 0 problem(s)` | `drift: 0 problem(s)` |
| #996 (`docs/kb/gates-scan-every-doc.md`) | `6720134` | rc=0 | `gates: 0 problem(s)` | `drift: 0 problem(s)` |

## Rollback plan

Door: two-way — a revert of one squash commit restores the raw-string
compare in both copies; nothing is migrated, published or renamed in a
public interface (`_grandfathered` and `FRONTMATTER_ISO_DATE` are
private to `gates.py`).

Blast radius: if the call is wrong, detectors H, O or M flag (or stop
flagging) a `prd.md`, `defect.md` or `verification.md` by its `date:`
spelling. On this repo that is nobody today (0 dodge shapes on main).
Every stamped repo gets the new behaviour on its next payload update,
after the Owner's release PR; one that hand-wrote a quoted or non-ISO
post-cutoff date would see new, actionable O or M problem strings.

```
# after merge, if the fix must come out:
git checkout main && git pull
git revert --no-edit <squash sha>
rm -f $(git ls-files --others --exclude-standard | grep -E '\.(orig|rej)$')
python3 factory_init.py update-manifest     # repin the payload gates.py
python3 run_tests.py && python3 gates.py && python3 gates.py --selftest
git commit -am "revert: restore O/M date compare" && git push   # via a PR
# before merge: close the pull request; nothing reached main
```

## Release log

1. `git fetch origin main`; `git merge-base --is-ancestor origin/main
   HEAD` -> ancestor (origin/main `461803a`); `git merge-tree
   --write-tree origin/main HEAD` -> `d085dfa…`, rc=0.
2. Pre-flight battery on `9986f3c` -> all green (quoted above).
3. Pairwise chain-simulation of #993, #1000, #996 -> all clean (table
   above).
4. `python3 <ship skill dir>/../../launch_demo.py config` -> printed,
   verbatim:
   ```
   SHIP
   launch-demo: 0 problem(s)
   ```
   No reason line was printed. Verdict SHIP: the launch brief was not
   produced in this unattended pass (orchestrator instruction); flagged
   under Outcome.
5. Appended the review's deferred Minor 2 (selftest dodge-shape rows) to
   `docs/backlog.md` as one seed `(from: session:2026-10-17)`; `python3
   lint.py` -> `lint: 0 problem(s) across 34 skills`, `python3 gates.py`
   -> `gates: 0 problem(s)`.
6. `gh issue list --search "quoted date cutoff in:title" --state all`
   and `--search "grandfather" --state all` -> `[]` both; `gh issue
   create --label type:defect` -> https://github.com/mattbutlerengineering/skills/issues/1001
7. Committed this `release.md` and the backlog seed, pushed the branch,
   and opened the pull request (`Closes #1001`, `No work order:` line).

## Post-release checks

Nothing has reached users: the pull request is open and unmerged. The
write-back runs these once it merges:

- `gh pr view <n> --json state,mergedAt` -> merged, with its date.
- On main at the squash commit: `python3 run_tests.py`, `python3
  gates.py && python3 gates.py --selftest`, and `cmp gates.py
  factory/templates/tools/factory/gates.py`.
- After the Owner's release PR: a plugin cache refresh shows the new
  version, and a stamped repo's `gates.py --selftest` stays `ok` after
  its payload update.
- Issue #1001 closed by the merge (`Closes #1001`).

## Release steps for the Owner

1. Merge the pull request (squash) once CI is green. Before merging,
   re-run the pairwise check against whatever else merged first.
2. Cut the ADR-0095 `chore(release)` PR bumping
   `.claude-plugin/plugin.json`, because the payload `gates.py` changed
   (one per wave; this branch never touches the version).
3. Write back (protocol, "The Ship outcome"): run `next`, or `ship`
   on this run; it reads the PR with `gh pr view <n> --json
   state,mergedAt`, rewrites `outcome: released`, adds `released-at:`
   with the merge date, and drops `pending-merge:`.

## Outcome

Prepared and stopped, waiting on the pull request `pending-merge:`
names. Flagged for the Owner:

- **Deferred Minor 1**: `check_capture_completeness` docstring line at
  `gates.py:1706` (and the payload copy) not reflowed, 105 characters.
  Cosmetic; any later edit to `gates.py` should reflow it.
- **Deferred Minor 2**: no dodge-shape row in `gates.py --selftest`, so
  stamped repos cannot see a regression. Filed as a seed in
  `docs/backlog.md` by this pass.
- **Launch brief**: `launch_demo.py config` verdict SHIP; not produced
  in this unattended pass. Run the `launch-demo` skill for this run if
  wanted.
- **Version bump**: not done here (ADR-0095); the Owner's
  `chore(release)` PR after merge.
- **Operate**: skipped by Owner decision 4 (autorun brief); the run
  stays active at Ship until the merge is written back.
