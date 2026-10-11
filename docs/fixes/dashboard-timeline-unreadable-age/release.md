---
stage: ship
run: maintenance:dashboard-timeline-unreadable-age
date: 2026-10-11
released: 2026-10-11 (669e0fe)
assumptions:
  - "Written after the merge, by the Conductor that ran the batch. The batch prepared and stopped at the PR. The owner then answered 'Merge both when green' in-session, and #667 was squash-merged once CI was green. This record is the release stage, written from what happened."
  - "No deploy step: dashboard.py is an operator-run local console (`python3 dashboard.py serve`), not a hosted service and not mirrored into stamped repos (absent from factory_init.MIRRORS). Merging to main is the release."
---

# Release: shipped (PR #667, squash-merged as 669e0fe)

**PR:** #667, `fix(dashboard): an unreadable timeline is not an unknown age`
**Closes:** #665 (anchor issue; no work order)
**Batch:** merged after #666 (retro carriers). The two were merge-tested together first: they share no files, and the combined tree was green.

## Pre-flight

| Check | Result |
|---|---|
| Verification green | `verification.md`: 5 criteria, 5 PASS, 0 FAIL |
| Review | `review.md`: 0 critical, 0 major, 2 minor (both fixed) |
| Mirror | `dashboard.py` is not in `factory_init.MIRRORS`, so no payload twin or manifest change |
| Configuration | none: no env var, credential or new external call |
| CI on the PR | every check passed (`gh pr checks 667`) |
| Pairwise | `git merge-tree` of #666 and #667, then on the combined tree: unittest 2109 OK, lint 0, gates 0, selftest ok |

## Rollback

`git revert 669e0fe`. One commit, and it is dashboard-only. The queue entry loses `aged`, and the page's marker goes because it keys on `aged === false`. No data or ledger is written by this change.

## Release executed

- 2026-10-11T01:51:42Z: #667 squash-merged to main as `669e0fe`, and #665 closed by its `Closes` line.

## Post-release

On main at `669e0fe`:

```
$ python3 -m unittest discover tests
Ran 2109 tests in 29.249s
OK
$ python3 lint.py
lint: 0 problem(s) across 31 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 dashboard.py gather .
...
dashboard: 0 problem(s)
```

The live `gather` returned an empty `queues` list, because no mirrored issue is waiting at a gate today. So the new `aged` field cannot be observed on real data yet. It is covered by the tests in `verification.md`.
