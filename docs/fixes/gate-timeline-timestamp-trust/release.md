---
stage: ship
run: maintenance:gate-timeline-timestamp-trust
date: 2026-08-23
authorization: none — prepare and stop
assumptions:
  - "Prepare-and-stop, per autorun-brief.md's Release authorization section: branch, commit, push, issue and PR are how this repo records work; merge and tag are not authorized. ADR-0036 clause 2 reserves merge to a non-authoring reviewer regardless of what the brief said, so this artifact could not end any other way."
  - "Scale: a scoped fix, so the pre-flight is the four checks below rather than a full release rehearsal (the protocol's Run scale section). The rollback plan is present anyway — the protocol requires it even when the release is small."
---

# Release: prepared, not executed — PR #326

## Pre-flight

- [x] **Verification green.** `verification.md` records six criteria, all
      PASS, on its second pass — re-run against `c16a84e` after Review
      reopened A1, not reused from the first.
- [x] **No secrets in diff; target config present.** `git diff main..HEAD`
      grepped for `token|secret|password|api[_-]key`: four hits, all prose
      in artifacts and the backlog (ADR-0034's "token-budget hook", the
      note that `feature:first-live-dispatch` is blocked on
      operator-minted secrets, and review.md's own "No secrets" line). No
      credential material, and the change needs no configuration that does
      not already exist.
- [x] **Migrations/data changes have a tested forward path.** None exist.
      The change is one pure function's admission rule; nothing is stored,
      versioned or migrated. `factory/manifest.json` moved by two
      checksums across the run's two edits, which is a regenerated
      artifact rather than data.
- [x] **Rollback plan concrete.** Below.

## Rollback plan

The change is three commits on one branch and is not merged, so rollback
before merge is closing the PR. After a merge, either of:

```
# 1. Revert the merge commit on main (preferred — keeps the history legible)
git revert -m 1 <merge-sha>
python3 factory_init.py update-manifest   # the payload copy travels with it
python3 -m unittest discover tests && python3 lint.py && python3 gates.py

# 2. Revert only the guard, keeping the tests as a red pin
git revert c16a84e b4dd17a
python3 factory_init.py update-manifest
```

Nothing outside the repo changes on merge — no deploy, no publish, no
package version. `.claude-plugin/plugin.json`'s version is untouched by
this run, so no installed plugin cache is affected either.

## Release log

1. `gh issue create` → https://github.com/mattbutlerengineering/skills/issues/325
2. `git branch -m agent/issue-325-gate-timeline-timestamp-trust` → renamed
   to match the repo's `agent/issue-NNN-<slug>` convention once the issue
   number existed
3. `git push -u origin agent/issue-325-gate-timeline-timestamp-trust` →
   `* [new branch]`
4. `gh pr create` → https://github.com/mattbutlerengineering/skills/pull/326
5. `gh pr checks 326` → all green:
   ```
   check	pass	22s
   needs-review-label	pass	7s
   review	pass	24s
   merged-label	skipping	0
   ```
6. **Merge: not executed.** Not authorized by the brief, and ADR-0036
   clause 2 reserves it to a non-authoring reviewer.

## Post-release checks

Not applicable — nothing was released. What can be checked at this point,
and was:

- `gh pr view 326` → `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`.
- Detector B (PR traceability) is satisfied by the body: the waiver
  `No work order: a maintenance run driven from a backlog seed` plus
  `Closes #325`. It cannot be pre-flighted locally — `gates.py` skips it
  without a PR event payload — so the green `check` job above is the
  evidence.

## Outcome

**Prepared and stopped, cleanly.** PR #326 is open, green, MERGEABLE, and
waiting on a human reviewer who did not write it.

One hiccup worth recording rather than smoothing over: the branch was
created before the issue existed, so it was named
`agent/gate-timeline-timestamp-trust` and renamed at step 2. The three
commits made before the rename are unaffected — but the ordering that
avoids this is issue first, branch second, which the three preceding runs
on this repo all did and this one did not.

Next stage is Operate, which owes two backlog seeds: review.md's F2 (a
dropped event removes a stay silently) and F3 (`dashboard._age_seconds` is
a second reader of GitHub timestamps).
