---
stage: verify
run: maintenance:gate-row-the-reader-rejects-becomes-spend
date: 2026-08-27
assumptions: []
---

# Verification: a gate row the reader rejects becomes spend

## 1. The writer refuses what the reader cannot read — PASS

An unreadable gate name and a negative wait both raise instead of
producing a row.

```
$ python3 -m unittest tests.test_cost_ledger -k CannotOutwrite
----------------------------------------------------------------------
Ran 4 tests in 0.000s

OK
```

## 2. Writer and reader never disagree, over a matrix — PASS

The property test crosses nine gate names (including `code-review`,
`UX`, `""`, `a:b` and a non-ASCII name) with five waits (including a
negative and a float). For every pair, either the writer raises or the
reader parses what it produced, and the row is never counted as spend.
Before the guard this matrix failed 39 of its subtests:

```
$ python3 -m unittest tests.test_cost_ledger -k CannotOutwrite   # pre-fix
AssertionError: unexpectedly None : wrote an unreadable row: 'gate_wait:méfiance:12s'
----------------------------------------------------------------------
Ran 4 tests in 0.004s

FAILED (failures=39)
```

## 3. The three shipped gates still round-trip — PASS

`test_every_shipped_gate_name_is_writable` walks `human_gates.GATES`
itself, so a future gate the ledger cannot record fails here loudly
instead of miscounting spend silently. The dependent suites were not
edited — the only test file this run touched is
`tests/test_cost_ledger.py`.

```
$ git diff --name-only -- tests/
tests/test_cost_ledger.py

$ python3 -m unittest tests.test_cost_report tests.test_gate_digest tests.test_gates
Ran 224 tests in 0.210s
OK
```

## 4. No existing ledger row is affected — PASS

The shipped ledger holds 41 rows, 22 of them gate rows, and the reader
already accepts every one. This run rewrites nothing and appends
nothing.

```
$ python3 -c "import cost_ledger, pathlib; ..."
costs.jsonl rows=41 problems=0 gate rows readable=22
existing rows the reader refuses: 0
```

## 5. Full battery green, payload mirrored — PASS

1344 tests on the merge base, 1348 here: the four added above.
`cost_ledger.py` is in `factory_init.MIRRORS`, so
`update-manifest` was run and the payload copy carries the guard;
detector E is green against the regenerated manifest.

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ python3 -m unittest discover tests
Ran 1348 tests in 15.443s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

## Not verified

No gate passage was recorded end to end: that path runs in the daily
digest against live GitHub label history, and this run made no network
call and wrote no ledger row. What is verified is that the writer can no
longer produce a row the reader refuses — not that the digest's own
callers behave differently, because for today's three gates they do not.
