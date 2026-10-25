---
stage: verify
run: maintenance:a-spend-row-stalls-the-merge
date: 2026-10-25
---

# Verification: a ship step's spend file stalls the Conductor's merge as unreviewed

## Summary

5 PASS, 0 FAIL, 1 NOT RUN (criterion 6, a live Conductor batch) across 6
criteria. The regression cases fail against `origin/main`'s
`conductor_merge.py` and `trace.py` and pass on HEAD `d3dc079`. Every repo
check is clean. Whether a real metered batch now merges without the false
stall is unknown until a batch runs.

## Criteria & evidence

### 1. Regression cases red on main's code, green on HEAD

- Check: `python3 -m unittest tests.test_conductor_merge tests.test_trace`,
  run twice:
  - in a detached scratchpad worktree at HEAD with `conductor_merge.py` and
    `trace.py` checked out from `origin/main` (`98b220e`), the worktree
    removed after;
  - on HEAD.
- Evidence:
  ```
  # origin/main's conductor_merge.py and trace.py
  ERROR: test_an_added_file_passes_only_under_the_runs_dir (tests.test_conductor_merge.TestReviewDrift...)
  FAIL: test_the_ship_steps_own_spend_file_may_follow_the_review (tests.test_conductor_merge.TestReviewedTree...)
  FAIL: test_unresolvable_keys_are_exact_problem_strings (...) (key='#0')
  FAIL: test_unresolvable_keys_are_exact_problem_strings (...) (key='#012')
  Ran 58 tests in 41.814s
  FAILED (failures=3, errors=1)

  # HEAD d3dc079
  Ran 58 tests in 31.933s
  OK
  ```
  The ERROR is `review_drift` on main refusing the new `added` argument. The
  ship-file FAIL is the reported stall itself: `'#12 changed
  docs/factory/costs/runs/...'` where `None` was expected.
- Result: PASS

### 2. A run file rewritten after the review still stalls

- Check: `test_a_rewritten_spend_file_after_the_review_stalls_the_merge`
  (real git: a build run file present at review, modified after), plus the
  pure case that an added path outside `RUNS_DIR` stalls.
- Evidence:
  ```
  test_a_rewritten_spend_file_after_the_review_stalls_the_merge ... ok
  test_an_added_file_passes_only_under_the_runs_dir ... ok
  test_a_dropped_spend_row_after_the_review_stalls_the_merge ... ok
  ```
  The rewrite case also passes on main, because main stalls on every run
  file. It guards against an over-wide fix and is not part of the red
  evidence.
- Result: PASS

### 3. The COSTS pair has one owner

- Check: `python3 one_owner.py`, counting lines that name `COSTS`.
- Evidence:
  ```
  $ python3 one_owner.py | grep -c COSTS
  0
  ```
  Before this run the pass printed `conductor_merge.py:75 COSTS and
  cost_ledger.py:29 COST_LEDGER state the same value`.
- Result: PASS

### 4. Payload regenerated

- Check: `python3 factory_init.py update-manifest` after the edits, then
  detector E (inside `gates.py`), which gates manifest against payload.
- Evidence:
  ```
  factory-init: 0 problem(s)
  gates: 0 problem(s)
  ```
- Result: PASS

### 5. Repo checks green

- Check: the four CI commands on HEAD `d3dc079`.
- Evidence:
  ```
  tests: 3910 tests across 122 modules in 31.2s on 8 workers, 0 problem(s)
  lint: 0 problem(s) across 35 skills
  drift: 0 problem(s)
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

### 6. A real Conductor batch merges past its ship step's spend file

- Check: none run. It needs a metered Conductor batch (paid Worker runs)
  that reaches its merge turn.
- Evidence: none.
- Result: NOT RUN

## Failures

None.

## Not verified

- Criterion 6: a live batch. The real-git `TestReviewedTree` turn is the
  closest offline equivalent.
