---
stage: verify
run: maintenance:a-parse-that-finds-nothing-passes
date: 2026-08-30
assumptions:
  - "Criteria come from defect.md's three work items and the standing triad, since this run is re-entry: implement and has no prd.md/breakdown.md pair."
  - "`python3 one_owner.py` is reported as unchanged-by-construction rather than diffed against a main run. one_owner.py sets EXCLUDED = ('factory/', 'tests/') and this run's only source diff is tests/test_sweeps.py, so its 9 pre-existing problems cannot have moved. That is a derivation, not a measurement, and it is labelled as one."
  - "The RED state was established before the fix and is quoted from that run, not reconstructed afterwards."
---

# Verification: a parse that finds nothing turns its test green

## RED before the fix

Both new tests were written and run before `commands()` changed:

```
test_a_workflow_it_cannot_parse_is_a_failure_not_a_pass ... FAIL
test_an_unparsed_workflow_with_no_ensure_labels_still_goes_red ... FAIL
Ran 84 tests in 0.048s
FAILED (failures=2)
```

A first draft of the second test passed while still RED on the first —
it stripped `ensure-labels` without also breaking the parse, so the loop
test failed for the ordinary reason and the assertion was satisfied for
the wrong cause. It was rewritten to compound both failures, which is
the actual defect, and only then went red. Recorded because a test that
passes in the RED state is a test that pins nothing, which is the very
thing this run exists to fix.

## Criteria

| # | Criterion | Result |
| --- | --- | --- |
| 1 | An unrecognised `jobs:` line raises `failureException`, not `{}` | **pass** — `test_a_workflow_it_cannot_parse_is_a_failure_not_a_pass` |
| 2 | The compounded failure (parse drift + missing step) goes red | **pass** — `test_an_unparsed_workflow_with_no_ensure_labels_still_goes_red` |
| 3 | The sibling's call-site `assertTrue(jobs)` is removed | **pass** — one owner, in `commands()` |
| 4 | `python3 -m unittest discover tests` | **pass** — `Ran 1346 tests ... OK` (1344 + 2) |
| 5 | `python3 lint.py` | **pass** — `lint: 0 problem(s) across 24 skills` |
| 6 | `python3 gates.py` and `--selftest` | **pass** — `gates: 0 problem(s)`, `selftest: ok` |
| 7 | `python3 one_owner.py` gains nothing | **pass, by derivation** — 9 problems, all pre-existing; `EXCLUDED` covers `tests/` |

## Testing the test

Two mutants, each applied to the shipped guard and reverted after:

| mutant | expected | observed |
| --- | --- | --- |
| Delete the `assertTrue(jobs, ...)` guard entirely | both new tests fail | `FAILED (failures=2)` |
| `assertTrue(jobs, ...)` → `assertIsNotNone(jobs, ...)` — a guard that is satisfied by `{}` | both new tests fail | `FAILED (failures=2)` |

The second mutant is the one that matters: it keeps a guard in place, at
the same line, with the same message, and only weakens what the guard
claims. A test suite that passes it would be pinning the presence of an
assertion rather than its content.

## Not verified

- The guard is a `unittest` assertion, so it protects test-time readers
  of `sweeps.yml` only. Nothing here changes `sweeps.py` or the workflow.
- The other 50 flagged loops are argued safe by the empty-collection
  table in defect.md, which runs each owning suite — not by a proof that
  no other vacuous loop exists anywhere in the repo.
