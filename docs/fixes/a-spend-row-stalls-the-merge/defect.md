---
stage: capture
run: maintenance:a-spend-row-stalls-the-merge
date: 2026-10-25
re-entry: implement
---

# Defect: a ship step's spend file stalls the Conductor's merge as unreviewed

## Defect (or Condition)

`conductor_merge._drift` checks the item branch against the reviewed head,
so that merged code is reviewed code. `review_drift` allows three kinds of
change after review:

- this run's `review.md` and `release.md`;
- the aggregate cost ledger `docs/factory/costs.jsonl`, appended only;
- nothing else.

Since #954 (2026-10-15), a Worker's spend row is its own file under
`cost_ledger.RUNS_DIR` (`docs/factory/costs/runs/<run-id>.jsonl`),
committed on the item branch by `conductor_spend.record_spend`. The ship
step's run writes one after the reviewed head. `review_drift` still knows
only the aggregate path (`conductor_merge.COSTS`, a second literal of
`cost_ledger.COST_LEDGER`), so a ship step's own spend file reads as
unreviewed.

Expected: a spend file added under `RUNS_DIR` after the review passes,
like an appended aggregate row. A run file changed or deleted after the
review still stalls, like a dropped aggregate row (re-review R4).

Second, smaller item from the same audit: `trace.py` keeps its own
`ISSUE_KEY = #(\d+)`, which accepts `#0` and `#012`. The ledger's own key
(`cost_ledger.ISSUE_KEY`, ADR-0084) refuses a leading zero.

## Reproduction / Evidence

Found in the 2026-10-25 consolidation audit, which sweeps for duplicated
facts. `python3 one_owner.py` names the pair:

```
one-owner: conductor_merge.py:75 COSTS and cost_ledger.py:29 COST_LEDGER state the same value — one fact, one owner
```

The reproduction is a new `TestReviewedTree` case in
`tests/test_conductor_merge.py`. It runs a real-git turn: the item branch
gains `docs/factory/costs/runs/conductor-b1-12-ship-1.jsonl` after the
reviewed head. On `origin/main` (`98b220e`, the code before this fix):

```
FAIL: test_the_ship_steps_own_spend_file_may_follow_the_review
AssertionError: Tuples differ: ([], '#12 changed docs/factory/costs/runs/cond[114 chars]iew') != ([], None)
```

For `trace.py`, `test_unresolvable_keys_are_exact_problem_strings` with
`#0` and `#012` fails on main: both keys resolve as issue numbers.

## Root-cause hypothesis

Finding (reproduced, not a guess): #954 moved spend rows to per-run files
and taught every ledger reader (`cost_ledger.read`,
`conductor_spend.ref_rows`) about `RUNS_DIR`. The merge's drift check held
its own copy of the old path and was not updated with them. The
one-owner pair is the root cause, and the stall is its symptom.

## Blast radius

Every Conductor batch since #954 whose ship step runs as a metered Worker.
The merge turn stalls with "needs a re-review" and asks the Owner to block,
so nothing wrong merges. The cost is a false stall that needs a person to
retry or override. No recorded batch in this repo shows the stall, since no
Conductor batch has merged here since #954. Payload modules, so stamped
repos get the fix on their next `factory-init update`. The `trace.py` item
only affects which keys `trace` accepts.

## Ruled out

- The merge-tree and update paths: they never look at spend paths.
- Allowing every path under `RUNS_DIR`: that would let a run file rewritten
  after review through, which is the R4 case. Only files new since the head
  pass, read with `git diff --diff-filter=A`.

## Work items

- [x] **Reproduce, then allow an added run spend file** — the two
  `TestReviewedTree` cases (added ship file merges; a pre-review run file
  rewritten afterwards stalls) plus a pure `review_drift` case (an added
  path outside `RUNS_DIR` still stalls). `review_drift` takes `added`, and
  `_drift` reads it with `--diff-filter=A`. `COSTS` becomes
  `cost_ledger.COST_LEDGER`.
  - Accept: the ship-file case fails on main and passes after;
    `python3 -m unittest tests.test_conductor_merge` exits 0; `one_owner.py`
    no longer names the COSTS pair.
- [x] **One issue key** — `trace.py` imports `cost_ledger.ISSUE_KEY`.
  - Accept: the `#0` and `#012` cases fail on main and pass after;
    `python3 -m unittest tests.test_trace` exits 0.
- [x] **Payload and checks** — `python3 factory_init.py update-manifest`
  (both modules are mirrored), then the four CI commands.
  - Accept: `factory-init: 0 problem(s)`, and every check prints 0
    problems and `selftest: ok`.

## Notes

- 2026-10-25: Run A of the Owner-approved consolidation wave (plan:
  drifted tool duplicates and this bug, then copied skill text). Runs B
  (`tool-duplicates-that-drifted`) and C (`one-owner-for-copied-skill-text`)
  follow, with one release PR for the wave.
