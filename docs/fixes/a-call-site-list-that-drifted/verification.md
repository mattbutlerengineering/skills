---
stage: verify
run: maintenance:a-call-site-list-that-drifted
date: 2026-08-30
assumptions: []
---

# Verification: a call-site list that drifted

## 1. The docstring now names the real callers — PASS

Derived from the source and compared to the prose:

```
derived : {'gates.py', 'plane_drift.py', 'work_queue.py'}
documented: {'gates.py', 'plane_drift.py', 'work_queue.py'}
```

## 2. The test fails when the docstring names a non-caller — PASS

Mutation: add `sweeps.py` to the listing (the exact stale claim this run
removed).

```
AssertionError: Items in the first set but not the second:
FAILED (failures=1)
```

## 3. The test fails when a real caller is missing from the listing — PASS

Mutation: give `cost_report.py` a genuine `row_done(...)` call.

```
AssertionError: Items in the second set but not the first:
  'cost_report.py'
FAILED (failures=1)
```

Both directions matter. A one-directional check would have passed the
original defect: every module the stale list named that *was* still a
caller remained one; the failure was the two it named that were not, and
the count.

The first attempt at this mutation was wrong and is recorded rather than
hidden — it injected `_ = row_done`, a reference and not a call, so the
AST walk correctly ignored it and the test correctly passed. Re-run with
a real call site, it fails as it should.

## 4. Rewrapping the docstring does not fail the test — PASS

The docstring is normalised (`" ".join(doc.split())`) before matching.
The first cut matched against the raw docstring and failed for the wrong
reason: the prose wrapped between `Call sites` and `(`, so a literal
space in the pattern could not match the newline. A test that only
passes at one line width is a trap for the next person to edit the
prose.

## 5. Full battery green, payload mirrored — PASS

1344 tests on the merge base, 1345 here: the one added above.
`knowledge_plane.py` is mirrored, so `update-manifest` ran.

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)

$ python3 -m unittest discover tests
Ran 1345 tests in 16.389s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

## 6. Red before green — PASS

```
AssertionError: unexpectedly None : row_done's docstring no longer
carries a delimited `Call sites (...): <modules> —` listing for this
test to check
```

## What is NOT verified

No behaviour changed. `row_done` returns exactly what it returned
before; this run touches its docstring and adds a test. There is
therefore no runtime evidence to show, and none is owed.
