---
stage: ship
run: maintenance:row-done-guard
date: 2026-08-23
authorization: none — prepare and stop
assumptions:
  - "Prepare-and-stop, per autorun-brief.md's Release authorization section. ADR-0036 clause 2 reserves merge to a non-authoring reviewer regardless of what the brief said, so this artifact could not end any other way."
  - "Scale: a scoped fix, so the pre-flight is the four checks below rather than a full release rehearsal (the protocol's Run scale section). The rollback plan is present anyway — the protocol requires it even when the release is small."
---

# Release: prepared, not executed — PR #328

## Pre-flight

- [x] **Verification green.** `verification.md` records five criteria, all
      PASS, run once against `4520083` — no stage re-run was needed this
      time.
- [x] **No secrets in diff; target config present.** The diff is one
      accessor, its tests, the mirrored payload copy, the manifest and the
      run's artifacts. No credential material, and the change needs no
      configuration that does not already exist.
- [x] **Migrations/data changes have a tested forward path.** None exist.
      Nothing is stored, versioned or migrated; `factory/manifest.json`
      moved by one checksum, which is a regenerated artifact rather than
      data.
- [x] **Rollback plan concrete.** Below.

## Rollback plan

Two commits on one branch, unmerged, so rollback before merge is closing
the PR. After a merge:

```
git revert -m 1 <merge-sha>
python3 factory_init.py update-manifest   # the payload copy travels with it
python3 -m unittest discover tests && python3 lint.py && python3 gates.py
```

Nothing outside the repo changes on merge — no deploy, no publish, no
package version. `.claude-plugin/plugin.json`'s version is untouched, so
no installed plugin cache is affected.

## Release log

1. `gh issue create` → https://github.com/mattbutlerengineering/skills/issues/327
   — **before** the branch this time, which is the ordering the previous
   run's release record said to use.
2. `git checkout -b agent/issue-327-row-done-guard` → branch named from
   the issue at creation, no rename needed.
3. `git push -u origin agent/issue-327-row-done-guard` → new branch.
4. `gh pr create` → https://github.com/mattbutlerengineering/skills/pull/328
5. `gh pr checks 328` → **`needs-review-label` failed:**
   ```
   V: none of the work orders this PR cites (WO-00xx) is mirrored to an issue it closes (#327) — a PR implements the work order whose breakdown row it closes
   ```
   The PR body quoted the malformed row it describes, live four-digit
   token and all, and the validator read that as the work order the PR
   implements. This is `docs/backlog.md:38` reproducing in the wild for
   the second time (after PR #306) — the seed is unclaimed, this run does
   not claim it, and the observation is recorded for whoever does.
6. `gh api repos/.../pulls/328 -X PATCH -F body=@…` → body re-read to
   confirm the redaction took. **Not `gh pr edit`**, which fails on this
   repo with a Projects-classic GraphQL error while reporting success and
   leaving the body unchanged.
7. `gh pr checks 328` → green; `needs-review-label` now skips, which is
   ADR-0057's correct behaviour for a PR that implements no work order.
   `gh pr view 328` → `MERGEABLE` / `CLEAN`.
8. **Merge: not executed.** Not authorized by the brief, and ADR-0036
   clause 2 reserves it to a non-authoring reviewer.

## Post-release checks

Not applicable — nothing was released. What can be checked now, and was:

- `gh pr view 328` → `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`.
- Detector B (PR traceability) is satisfied by the body: the waiver
  `No work order: a maintenance run driven from a backlog seed` plus
  `Closes #327`. It cannot be pre-flighted locally — `gates.py` skips it
  without a PR event payload — so the green `check` job is the evidence.

## Outcome

**Prepared and stopped, cleanly, with one hiccup that is itself a
finding.** PR #328 is open, green, MERGEABLE, and waiting on a human
reviewer who did not write it.

The hiccup is worth the ink: three times in this run, writing *about* a
malformed breakdown row tripped a tool that reads breakdown rows —
detector A on the acceptance criterion, detector A again on the note
quoting detector A, and the validator's lifecycle leg on the PR body. All
three are the same shape, and none of them is the defect this run fixed.
The repo has a redaction convention for it (`WO-00xx`, `docs/backlog.md:38`)
and this run used it, but nothing warns an author in advance.

Next stage is Operate, which owes three backlog seeds: review.md's two
deferred findings (the `protocol._CHECKBOX` alignment caveat's scope, and
detector G reading the raw line where an accessor exists), plus the
quoting collision above.
