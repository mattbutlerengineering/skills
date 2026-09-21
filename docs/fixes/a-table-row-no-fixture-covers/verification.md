---
stage: verify
run: maintenance:a-table-row-no-fixture-covers
date: 2026-08-30
assumptions:
  - "Criteria are defect.md's three work items plus the standing triad; re-entry: implement, so there is no prd.md/breakdown.md pair."
  - "The first attempt at the table-row mutant is reported alongside the one that counts. It added a row at the FRONT of STAGE_ARTIFACTS, which every existing fixture then trips over -- 16 failures, of which the closure assertion is one. That mutant proves nothing about the new test, because test_decision_table already catches it. The mutant that isolates the new test appends the row at the END."
---

# Verification: a table row no fixture covers

## Evidence

Branch tip:

```
$ python3 -m unittest discover tests 2>&1 | tail -3
Ran 1346 tests in 16.421s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

## Criteria

| # | Criterion | Result |
| --- | --- | --- |
| 1 | The `decompose` fixture returns `decompose` | **pass** — `fixture returns: decompose` |
| 2 | Removing that fixture fails the closure assertion | **pass** |
| 3 | An `expected` naming an impossible stage fails | **pass** |
| 4 | A row no fixture reaches fails | **pass** — and *only* the closure assertion fails |
| 5 | Full battery green | **pass** — 1346 tests (1344 + 2) |

## Mutants

```
=== MUTANT 1: the new fixture removed (main's state) ===
FAIL: test_every_stage_the_table_can_return_has_a_fixture
+ [] : rows of the maintenance table that no fixture expects
FAILED (failures=1)

=== MUTANT 2: a fixture expecting a stage the table cannot return ===
FAIL: test_decision_table (fixture='zz-bogus')
FAIL: test_every_stage_the_table_can_return_has_a_fixture
+ [] : fixtures expecting a stage the table cannot return
FAILED (failures=2)

=== MUTANT 3a: a row prepended to STAGE_ARTIFACTS ===
FAILED (failures=16)   <- 15 of them test_decision_table; proves nothing

=== MUTANT 3b: a row APPENDED to STAGE_ARTIFACTS ===
FAIL: test_every_stage_the_table_can_return_has_a_fixture
+ [] : rows of the table that no fixture expects
FAILED (failures=1)    <- the new test is the only thing that notices
```

Mutant 3b is the one that matters. A row appended past `operate` is
reached by no existing fixture, so `test_decision_table` stays green on
all fifteen of them and the closure assertion is the only failure. That
is the whole case for the test.

## A mutant that did not run

Mutant 3a and 3b each failed to apply on first attempt — `assert
s.count(old) == 1` raised, because `STAGE_ARTIFACTS = [` also matches the
maintenance table's neighbourhood and my first anchor was not unique.
The guard did its job: the run printed the AssertionError instead of a
verdict, and an `OK` from a later command in the same block could have
been misread as a passing mutant. Both were re-run with unique anchors
and the results above are from those runs.

## Not verified

- That `decompose` is reachable by *only* the shape the new fixture
  uses. The fixture closes the row; it does not enumerate every tree
  that lands on it.
- The router's English conditionals, which `test_lint` already records
  as deliberately unpinned.
